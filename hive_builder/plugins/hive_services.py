#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 Procube Co., Ltd.

"""
hive inventory: dynamic inventory plugin for hive
"""

from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.errors import AnsibleParserError
from ansible.parsing.yaml.objects import AnsibleMapping, AnsibleSequence, AnsibleUnicode
from ansible.module_utils.six import text_type
from hive_builder.hive import hiveContext
from ansible.utils.display import Display

display = Display()

DOCUMENTATION = r'''
  name: hive_services
  plugin_type: inventory
  short_description: Returns Inventory for hive volumes, networks, images, service
  description:
    - Generate volumes, networks, images, services from service defition yaml

  options:
    plugin:
      description: token that ensures this is a source file for the 'hive_services' plugin.
      required: True
      choices: ['hive_services']
    services:
      description: service definitions
      required: True
    networks:
      description: network definitions
      required: False
    available_on:
      description: list of stage which the service available on
'''

EXAMPLES = r'''
plugin: hive_inventory
stages:
- stage: private
  provider: vagrant
  separate_repository: False
  name: test
  subnets:
  - cidr: 192.168.0.96/29
'''

STAGES = ['private', 'staging', 'production']


class InventoryModule(BaseInventoryPlugin):

  NAME = 'hive_services'  # used internally by Ansible, it should match the file name but not required

  def __init__(self):
    super(InventoryModule, self).__init__()
    self.sites = []

  def verify_file(self, path):
    ''' return true/false if this is possibly a valid file for this plugin to consume '''
    valid = False
    if super(InventoryModule, self).verify_file(path):
      # base class verifies that file exists and is readable by current user
      if path.endswith(('.yaml', '.yml')):
        valid = True
    return valid

  def parse(self, inventory, loader, path, cache=True):
    super(InventoryModule, self).parse(inventory, loader, path, cache)
    self.context = hiveContext()
    self.context.setup(None)
    self._read_config_data(path)
    self.inventory.add_group('services')
    self.inventory.add_group('images')
    self.inventory.add_group('volumes')
    self.inventory.add_group('drbd_volumes')
    self.inventory.add_group('nfs_volumes')
    self.inventory.add_group('networks')
    available_on = self.get_option('available_on')
    if available_on is None:
      available_on = STAGES
    for s in available_on:
      if s not in STAGES:
        raise AnsibleParserError(f'"element of "available_on" must be one of {STAGES}, but {s}')
      self.inventory.add_group(s)
    services = self.get_option('services')
    if type(services) != AnsibleMapping:
      raise AnsibleParserError(f'"services" must be dict type, but {type(services)}')
    device_id_map = self.context.vars.get('drbd_device_map', {})
    published_port_map = self.context.vars.get('published_port_map', {})
    for name, options in services.items():
      service = Service(name, options, available_on)
      service.parse(inventory, device_id_map, published_port_map)
    self.context.set_persistent('drbd_device_map', device_id_map)
    self.context.set_persistent('published_port_map', published_port_map)
    self.context.save_persistent()
    networks = self.get_option('networks')
    no_default = True
    if networks is not None:
      if type(networks) != AnsibleMapping:
        raise AnsibleParserError(f'"networks" must be dict type')
      for name, options in networks.items():
        if name == 'hive_default_network':
          no_default = False
        network = Network(name, options, available_on)
        network.parse(inventory)
    if no_default:
      network = Network('hive_default_network', AnsibleMapping(), available_on)
      network.parse(inventory)


IMAGE_PARAMS = ['from', 'roles', 'env', 'stop_signal', 'user', 'working_dir', 'standalone', 'entrypoint',
                'command', 'privileged', 'expose', 'pull_on', 'pull_from']
SERVICE_PARAMS_COPY = ['backup_scripts', 'command', 'dns', 'endpoint_mode', 'entrypoint', 'environment', 'healthcheck',
                       'hosts', 'ignore_error', 'initialize_roles', 'labels', 'logging', 'monitor_error', 'mode', 'networks', 'placement', 'replicas',
                       'restart_config', 'standalone', 'user', 'working_dir']
NETWORK_PARAMS = ['driver', 'ipam', 'driver_opts']
SERVICE_PARAMS = SERVICE_PARAMS_COPY + ['volumes', 'image', 'ports', 'available_on']
VOLUME_PARAMS = ['target', 'type', 'source', 'readonly']
VOLUME_PARAMS_DEF = ['driver', 'driver_opts', 'drbd', 'nfs']


class Network:
  def __init__(self, name, options, available_on):
    self.name = name
    self.options = options
    self.available_on = available_on

  def parse(self, inventory):
    inventory.add_host(self.name, group='networks')
    for s in self.available_on:
      inventory.add_host(self.name, group=s)
    if self.options is None:
      return
    if type(self.options) != AnsibleMapping:
      raise AnsibleParserError(f'value must be dict type in network {self.name}')
    for option_name, option_value in self.options.items():
      if option_name not in NETWORK_PARAMS:
        raise AnsibleParserError(f'unknown parameter {option_name} is specified in network in service {self.name}')
      inventory.set_variable(self.name, f'hive_{option_name}', option_value)


class Service:
  def __init__(self, name, options, available_on):
    self.name = name
    self.options = options
    self.available_on = available_on

  def parse(self, inventory, device_id_map, published_port_map):
    if type(self.options) != AnsibleMapping:
      raise AnsibleParserError(f'value must be dict type in service {self.name}')
    inventory.add_host(self.name, group='services')
    for option_name, option_value in self.options.items():
      if option_name not in SERVICE_PARAMS:
        raise AnsibleParserError(f'unknown parameter {option_name} is specified in service {self.name}')
      if option_name in SERVICE_PARAMS_COPY:
        inventory.set_variable(self.name, f'hive_{option_name}', option_value)
    if 'available_on' in self.options:
      self.available_on = self.options['available_on']
      for s in self.available_on:
        if s not in STAGES:
          raise AnsibleParserError(f'"element of "available_on" of service {self.name} must be one of {STAGES}, but {s}')
    for s in self.available_on:
      inventory.add_host(self.name, group=s)
    if 'volumes' in self.options or self.options.get('standalone', False):
      volumes_value = self.options.get('volumes', AnsibleSequence([]))
      if type(volumes_value) != AnsibleSequence:
        raise AnsibleParserError(f'"volumes" must be list type in service {self.name}, but {type(volumes_value)}')
      volumes = []
      if self.options.get('standalone', False):
        volumes = [
            {'source': '/sys/fs/cgroup', 'target': '/sys/fs/cgroup', 'readonly': True},
            {'source': '', 'target': '/run', 'type': 'tmpfs'},
            {'source': '', 'target': '/tmp', 'type': 'tmpfs'}
        ]
      for volume in volumes_value:
        if type(volume) == AnsibleUnicode:
          raise AnsibleParserError(f'we do not support short syntax {text_type(volume)} in volume at service {self.name}')
        elif type(volume) == AnsibleMapping:
          if 'source' not in volume or 'target' not in volume:
              raise AnsibleParserError(f'both "source" and "target" must be specified in volume at service {self.name}')
          if 'nfs' in volume:
            if 'driver' in volume:
              raise AnsibleParserError(f'both "driver" and "nfs" can not be specified in volume at service {self.name}')
            if 'drbd' in volume:
              raise AnsibleParserError(f'both "nfs" and "drbd" can not be specified in volume at service {self.name}')
            self.add_volume(inventory, {'name': volume['source'], 'nfs': volume['nfs']}, 'nfs_volumes', volume['nfs'].get('available_on', self.available_on))
          if 'driver' in volume:
            # we prepare volume at build-volume phase
            prepared_volume = {'name': volume['source'], 'driver': volume['driver']}
            if 'driver_opts' in volume:
              prepared_volume['dirver_options'] = volume['driver_opts']
            self.add_volume(inventory, prepared_volume, 'volumes', self.available_on)
          if 'drbd' in volume:
            if 'driver' in volume:
              raise AnsibleParserError(f'both "driver" and "drbd" can not be specified in volume at service {self.name}')
            if 'device_id' in volume['drbd']:
              if volume['drbd']['device_id'] in device_id_map.values() and volume['drbd']['device_id'] != device_id_map.get(volume['source']):
                raise AnsibleParserError(
                    f'duplicate deviceid {volume["drbd"]["device_id"]} of volume {volume["source"]} in service {self.name}')
            else:
              if volume['source'] in device_id_map:
                  volume['drbd']['device_id'] = device_id_map[volume['source']]
              else:
                # assign new device id
                for device_id in range(1, 256):
                  if device_id not in device_id_map.values():
                    volume['drbd']['device_id'] = device_id
                    break
                if 'device_id' not in volume['drbd']:
                  raise AnsibleParserError(f'too many drbd volumes or garbage device_id are remain in "device_id_map" of persistent hive variable')
            device_id_map[text_type(volume['source'])] = volume['drbd']['device_id']
            self.add_volume(inventory, {'name': volume['source'], 'drbd': volume['drbd']},
                            'drbd_volumes', volume['drbd'].get('available_on', self.available_on))
          volume_value = {}
          for k, v in volume.items():
            # TODO: support properties of mounts property of docker_swarm_service module
            # I do not know what driver_config option means, it does check for volume definition? or it does create volume ondemand?
            if k not in VOLUME_PARAMS + VOLUME_PARAMS_DEF:
              raise AnsibleParserError(f'unknown parameter {k} is specified in volume in service {self.name}')
            if k in VOLUME_PARAMS:
              volume_value[k] = v
          volumes.append(volume_value)
        else:
          raise AnsibleParserError(f'all element of "volumes" must be dict type or str type in service {self.name}')
      inventory.set_variable(self.name, 'hive_volumes', volumes)

    if 'image' in self.options:
      image_value = self.options['image']
      if type(image_value) == AnsibleUnicode:
        # self.options['image'] can be {{hive_registry}}/image_some_another_service to refer build image
        inventory.set_variable(self.name, 'hive_image', image_value)
      elif type(image_value) == AnsibleMapping:
        # this container needs build.
        image_name = f'image_{self.name}'
        inventory.add_host(image_name, group='images')
        for s in self.available_on:
          inventory.add_host(image_name, group=s)
        # when hive_image_name is set, means image = {{hive_registry}}:{{hive_image_name}}
        inventory.set_variable(self.name, 'hive_image_name', image_name)
        if 'from' not in image_value:
          raise AnsibleParserError(f'"from" must be specified in "image" at service {self.name}')
        # just copy paste parameter for build image
        if self.options.get('standalone', False):
          inventory.set_variable(image_name, f'hive_standalone', True)
          inventory.set_variable(image_name, f'hive_privileged', True)
        if 'pull_from' in image_value and 'pull_on' not in image_value:
          raise AnsibleParserError(f'pull_from must be specified in "image" at service {self.name} when pull_on is specified')
        for option_name, option_value in image_value.items():
          if option_name not in IMAGE_PARAMS:
            raise AnsibleParserError(f'unknown parameter {option_name} is specified in "image" at service {self.name}')
          inventory.set_variable(image_name, f'hive_{option_name}', option_value)
      else:
        raise AnsibleParserError(f'"image" must be dict type or str type in service {self.name}, but type is {type(image_value)}')
    if 'ports' in self.options:
      ports = []
      for portdef in self.options['ports']:
        if type(portdef) == AnsibleMapping:
          pass
        elif type(portdef) == AnsibleUnicode:
          slash = portdef.split('/')
          protocol = 'tcp'
          if len(slash) > 1:
            protocol = slash[1]
          colon = slash[0].split(':')
          if len(colon) > 1:
            portdef = {'published_port': int(colon[0]), 'target_port': int(colon[1]), 'protocol': protocol}
          else:
            portdef = {'target_port': int(colon[0]), 'protocol': protocol}
        else:
          raise AnsibleParserError(f'element of "ports" must be dict type or str type in service {self.name}, but type is {type(portdef)}')
        if portdef['protocol'] not in ['tcp', 'udp', 'sctp']:
          raise AnsibleParserError(f'unknown protocol {portdef["protocol"]} is specified {self.name}.')
        published_port_key = self.name + text_type(portdef['target_port'])
        if 'published_port' in portdef:
          if portdef['published_port'] in published_port_map.values() and portdef['published_port'] != published_port_map.get(published_port_key):
            display.warning(
                f'duplicate port number {portdef["published_port"]} of port {published_port_key}')
        else:
          if published_port_key in published_port_map:
              portdef['published_port'] = published_port_map[published_port_key]
          else:
            # assign new port number
            for port_number in range(61001, 65535):
              if port_number not in published_port_map.values():
                portdef['published_port'] = port_number
                break
            if 'published_port' not in portdef:
              raise AnsibleParserError(f'too many published ports or garbage port number are remain in "published_port_map" of persistent hive variable')
        published_port_map[published_port_key] = portdef['published_port']
        ports.append(portdef)
      inventory.set_variable(self.name, f'hive_ports', ports)

  def add_volume(self, inventory, volume, group, available_on):
    name = 'volume_' + volume['name']
    inventory.add_host(name, group=group)
    for s in available_on:
      inventory.add_host(name, group=s)
    inventory.set_variable(name, 'hive_volume', volume)
