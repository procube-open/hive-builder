#!/usr/bin/python

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


DOCUMENTATION = r'''
---
module: hive_zabbix
short_description: Configure Hive monitoring through the Zabbix 8 API
description:
  - Runs on the repository host so the API does not need to be publicly accessible.
options:
  server_url:
    type: str
    required: true
  login_user:
    type: str
    default: Admin
  login_password:
    type: str
    required: true
  resource:
    type: str
    choices: [host, hostgroup, template, template_macro]
    required: true
  state:
    type: str
    choices: [present, absent]
    default: present
  host_name:
    type: str
  host_groups:
    type: list
    elements: str
  link_templates:
    type: list
    elements: str
  interfaces:
    type: list
    elements: dict
  template_xml:
    type: str
  template_name:
    type: str
  macro_name:
    type: str
  macro_value:
    type: str
'''


class Zabbix:
  def __init__(self, module):
    self.module = module
    self.token = None

  def call(self, method, params):
    headers = {'Content-Type': 'application/json'}
    if self.token:
      headers['Authorization'] = 'Bearer ' + self.token
    response, info = fetch_url(
        self.module, self.module.params['server_url'].rstrip('/') + '/api_jsonrpc.php',
        data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}),
        headers=headers, method='POST', timeout=60, use_proxy=False)
    if info['status'] != 200:
      raise ValueError(f'{method}: HTTP status {info["status"]}')
    result = json.loads(response.read())
    if 'error' in result:
      raise ValueError(f'{method}: {result["error"].get("data", result["error"]["message"])}')
    return result['result']

  def groups(self, names):
    existing = self.call('hostgroup.get', {'output': ['groupid', 'name'], 'filter': {'name': names}})
    missing = sorted(set(names) - {group['name'] for group in existing})
    if missing and not self.module.check_mode:
      self.call('hostgroup.create', [{'name': name} for name in missing])
      existing = self.call('hostgroup.get', {'output': ['groupid', 'name'], 'filter': {'name': names}})
    return [{'groupid': group['groupid']} for group in existing], bool(missing)

  def host(self, params):
    hosts = self.call('host.get', {
        'output': ['hostid', 'host'], 'filter': {'host': [params['host_name']]},
        'selectHostGroups': ['groupid'], 'selectParentTemplates': ['templateid'],
        'selectInterfaces': ['interfaceid', 'type', 'main', 'useip', 'ip', 'dns', 'port', 'details']})
    if params['state'] == 'absent':
      if hosts and not self.module.check_mode:
        self.call('host.delete', [host['hostid'] for host in hosts])
      return bool(hosts)
    groups, changed = self.groups(params['host_groups'])
    templates = self.call('template.get', {
        'output': ['templateid', 'host'], 'filter': {'host': params['link_templates']}})
    missing = set(params['link_templates']) - {template['host'] for template in templates}
    if missing:
      raise ValueError(f'templates not found: {sorted(missing)}')
    desired = {
        'host': params['host_name'], 'groups': groups,
        'templates': [{'templateid': template['templateid']} for template in templates],
        'interfaces': params['interfaces']}
    if not hosts:
      if not self.module.check_mode:
        self.call('host.create', desired)
      return True
    host = hosts[0]
    # Keep manual links and groups; Hive manages only its requested memberships.
    for key, actual, id_key in (
        ('groups', host['hostgroups'], 'groupid'),
        ('templates', host['parentTemplates'], 'templateid')):
      ids = {entry[id_key] for entry in actual}
      changed = changed or not all(entry[id_key] in ids for entry in desired[key])
      desired[key] += [{id_key: value} for value in ids
                       if value not in {entry[id_key] for entry in desired[key]}]
    interfaces = []
    for interface in desired['interfaces']:
      match = next((entry for entry in host['interfaces']
                    if str(entry['type']) == str(interface['type'])
                    and str(entry['main']) == str(interface['main'])), None)
      if match:
        interface = dict(interface, interfaceid=match['interfaceid'])
      if not match or any(str(match[key]) != str(value) for key, value in interface.items()):
        changed = True
      interfaces.append(interface)
    managed_ids = {interface.get('interfaceid') for interface in interfaces}
    interfaces += [interface for interface in host['interfaces']
                   if interface['interfaceid'] not in managed_ids]
    desired['interfaces'] = interfaces
    if changed and not self.module.check_mode:
      self.call('host.update', dict(desired, hostid=host['hostid']))
    return changed

  def template_macro(self, params):
    templates = self.call('template.get', {
        'output': ['templateid'], 'filter': {'host': [params['template_name']]}})
    if len(templates) != 1:
      raise ValueError(f'template not found: {params["template_name"]}')
    templateid = templates[0]['templateid']
    macros = self.call('usermacro.get', {
        'output': ['hostmacroid', 'value'], 'hostids': [templateid],
        'filter': {'macro': params['macro_name']}})
    if macros and macros[0]['value'] == params['macro_value']:
      return False
    if not self.module.check_mode:
      if macros:
        self.call('usermacro.update', {
            'hostmacroid': macros[0]['hostmacroid'], 'value': params['macro_value']})
      else:
        self.call('usermacro.create', {
            'hostid': templateid, 'macro': params['macro_name'], 'value': params['macro_value']})
    return True

  def template(self, params):
    rules = {
        'host_groups': {'createMissing': True},
        'template_groups': {'createMissing': True},
        'templates': {'createMissing': True, 'updateExisting': True},
        'templateLinkage': {'createMissing': True},
    }
    for resource in ('discoveryRules', 'graphs', 'httptests', 'items', 'templateDashboards', 'triggers', 'valueMaps'):
      rules[resource] = {'createMissing': True, 'updateExisting': True}
    request = {'format': 'xml', 'source': params['template_xml'], 'rules': rules}
    difference = self.call('configuration.importcompare', request)
    if not difference:
      return False
    if not self.module.check_mode:
      self.call('configuration.import', request)
    return True

  def configure(self, params):
    self.token = self.call('user.login', {
        'username': params['login_user'], 'password': params['login_password']})
    try:
      if params['resource'] == 'hostgroup':
        return self.groups(params['host_groups'])[1]
      return getattr(self, params['resource'])(params)
    finally:
      self.call('user.logout', [])


def main():
  module = AnsibleModule(
      argument_spec={
          'server_url': {'type': 'str', 'required': True},
          'login_user': {'type': 'str', 'default': 'Admin'},
          'login_password': {'type': 'str', 'required': True, 'no_log': True},
          'resource': {'type': 'str', 'required': True,
                       'choices': ['host', 'hostgroup', 'template', 'template_macro']},
          'state': {'type': 'str', 'default': 'present', 'choices': ['present', 'absent']},
          'host_name': {'type': 'str'}, 'host_groups': {'type': 'list', 'elements': 'str'},
          'link_templates': {'type': 'list', 'elements': 'str'},
          'interfaces': {'type': 'list', 'elements': 'dict'},
          'template_xml': {'type': 'str'}, 'template_name': {'type': 'str'},
          'macro_name': {'type': 'str'}, 'macro_value': {'type': 'str'},
      },
      required_if=[
          ['resource', 'host', ['host_name']],
          ['resource', 'hostgroup', ['host_groups']],
          ['resource', 'template', ['template_xml']],
          ['resource', 'template_macro', ['template_name', 'macro_name', 'macro_value']],
      ],
      supports_check_mode=True)
  if module.params['resource'] == 'host' and module.params['state'] == 'present':
    for key in ('host_groups', 'link_templates', 'interfaces'):
      if module.params[key] is None:
        module.fail_json(msg=f'{key} is required for a present host')
  try:
    changed = Zabbix(module).configure(module.params)
  except (ValueError, KeyError) as error:
    module.fail_json(msg=str(error))
  module.exit_json(changed=changed)


if __name__ == '__main__':
  main()
