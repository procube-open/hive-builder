#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 Procube Co., Ltd.

import docker
import os
import logging
import subprocess
import re
import ipaddress
import json
import signal
import time

logging.basicConfig(level=os.environ.get('HIVE_LOG_LEVEL', logging.INFO))
DAEMON = None


class HookBase:
  def __init__(self, label_value, serivce_id, service_name):
    self.label_value = label_value
    self.serivce_id = serivce_id
    self.service_name = service_name
    self.stay = False

  @property
  def id(self):
    return self.label_value + '@' + self.service_name + '#' + self.__class__.__name__

  @classmethod
  def check_service(cls, service):
    label_value = service.attrs.get('Spec', {}).get('Labels', {}).get(cls.label_name)
    if label_value is not None:
      DAEMON.logger.debug(f'label "{cls.label_name}" is found at service {service.name}')
      return cls.get_hook(label_value, service.id, service.name)
    return None

  @classmethod
  def get_hook(cls, label_value, serivce_id, name):
    return cls(label_value, serivce_id, name)

  def check_tasks(self):
    stay = False
    for task in DAEMON.client.services.get(self.serivce_id).tasks():
      if task.get('DesiredState') == 'running' and task.get('NodeID') == DAEMON.node_id:
        DAEMON.logger.debug(f'found task: {json.dumps(task)}')
        stay = True
    if self.stay and not stay:
      self.on_leave()
    elif stay and not self.stay:
      self.on_enter()
    self.stay = stay

  def on_registered(self):
    self.check_tasks()

  def on_unregistered(self):
    self.on_leave()

  def on_node_down(self):
    self.on_leave()


class MarkNode(HookBase):
  label_name = 'HIVE_MARK'

  def on_enter(self):
    node = DAEMON.get_node()
    if node is None:
      DAEMON.logger.info(f'fail to get node at on_enter, do nothing')
      return
    spec = node.attrs.get('Spec', {}).copy()
    labels = spec.get('Labels', {}).copy()
    if labels.get(self.label_value) == "true":
      DAEMON.logger.info(f'label "{self.label_value}" value is alredy set to "true" at on_enter, do nothing')
      return
    labels[self.label_value] = "true"
    spec['Labels'] = labels
    DAEMON.logger.debug(f'update node "{node.id}" Spec to "{json.dumps(spec)}"')
    node.update(spec)

  def on_leave(self):
    node = DAEMON.get_node()
    if node is None:
      DAEMON.logger.info(f'fail to get node at on_leave, do nothing')
      return
    spec = node.attrs.get('Spec', {}).copy()
    labels = spec.get('Labels', {}).copy()
    if self.label_value not in labels:
      DAEMON.logger.info(f'label "{self.label_value}" value is not set at on_leave, do nothing')
      return
    labels.pop(self.label_value)
    spec['Labels'] = labels
    DAEMON.logger.debug(f'update node "{node.id}" Spec to "{json.dumps(spec)}"')
    node.update(spec)


class SetVIP(HookBase):
  label_name = 'HIVE_VIP'
  router_label_name = 'HIVE_ROUTER'

  @classmethod
  def check_service(cls, service):
    label_value = service.attrs.get('Spec', {}).get('Labels', {}).get(cls.label_name)
    if label_value is None:
      return None
    me = cls.get_hook(label_value, service.id, service.name)
    if me is None:
      return None
    me.router = service.attrs.get('Spec', {}).get('Labels', {}).get(cls.router_label_name)
    DAEMON.logger.debug(f'label "HIVE_ROUTER" value is {me.router}')
    return me

# sample of output of ip addr command
# 1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
#     link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
#     inet 127.0.0.1/8 scope host lo
#        valid_lft forever preferred_lft forever
#     inet 10.1.32.12/32 scope global lo
#        valid_lft forever preferred_lft forever
#     inet6 ::1/128 scope host
#        valid_lft forever preferred_lft forever
# 2: em1: <BROADCAST,MULTICAST,SLAVE,UP,LOWER_UP> mtu 1500 qdisc mq master bond0 state UP group default qlen 1000
#     link/ether 6c:2b:59:ab:5d:16 brd ff:ff:ff:ff:ff:ff
# 3: em2: <BROADCAST,MULTICAST,SLAVE,UP,LOWER_UP> mtu 1500 qdisc mq master bond0 state UP group default qlen 1000
#     link/ether 6c:2b:59:ab:5d:16 brd ff:ff:ff:ff:ff:ff
# 4: bond0: <BROADCAST,MULTICAST,MASTER,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
#     link/ether 6c:2b:59:ab:5d:16 brd ff:ff:ff:ff:ff:ff
#     inet 10.1.32.2/20 brd 10.1.47.255 scope global noprefixroute bond0
#        valid_lft forever preferred_lft forever
#     inet 10.1.32.12/20 scope global secondary bond0
#        valid_lft forever preferred_lft forever
#     inet6 fe80::6e2b:59ff:feab:5d16/64 scope link
#        valid_lft forever preferred_lft forever
# 5: docker_gwbridge: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default
#     link/ether 02:42:0f:41:6f:78 brd ff:ff:ff:ff:ff:ff
#     inet 172.21.34.1/25 brd 172.21.34.127 scope global docker_gwbridge
#        valid_lft forever preferred_lft forever
#     inet6 fe80::42:fff:fe41:6f78/64 scope link
#        valid_lft forever preferred_lft forever

  reg_start_if = re.compile(r'^ *(\d+): *([\w.]+)(@[\w]+)?: .*$')
  reg_link = re.compile(r'^ +link/.*$')
  reg_inet = re.compile(r'^ +inet (\d+\.\d+\.\d+\.\d+/\d+) .*$')

  def subprocess_run(self, args):
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='UTF-8')
    if proc.returncode != 0:
      DAEMON.logger.error(f'fail to execute "{" ".join(args)}" command. stderr: {proc.stderr}')
      return proc
    DAEMON.logger.info(f'success to execute "{" ".join(args)}" command. stdout: {proc.stdout}')
    return proc

  def list_ifs(self):
    ip_addr = self.subprocess_run(['ip', 'addr'])
    state = 'start'
    interface = dict(ips=[])
    for line in ip_addr.stdout.splitlines():
      if state == 'start':
        start_if = self.__class__.reg_start_if.match(line)
        assert start_if, f'fail to parse line {line} does not match regexp {self.__class__.reg_start_if.pattern} in {state} state.'
        state = 'in_if'
        interface['name'] = start_if.group(2)
      elif state == 'in_if':
        if self.__class__.reg_link.match(line) is None:
          inet = self.__class__.reg_inet.match(line)
          if inet:
            inet_if = ipaddress.ip_interface(inet.group(1))
            interface['network'] = inet_if.network
            interface['ips'].append(inet_if.ip)
          else:
            start_if = self.__class__.reg_start_if.match(line)
            if start_if:
              assert 'name' in interface, '!!BUG!!'
              yield interface
              interface = dict(name=start_if.group(2), ips=[])
    if 'name' in interface:
      yield interface

  def get_interface(self):
    found = None
    if '@' in self.label_value:
      at_values = self.label_value.split('@')
      for interface in self.list_ifs():
        if interface['name'] == at_values[1]:
          found = interface
          try:
            vip_if = ipaddress.ip_interface(at_values[0])
          except ValueError as e:
            DAEMON.logger.error(f'Fail to parse as ip address with prefix length for {at_values[0]} : {e}')
          found['vip_if'] = vip_if
          break
    else:
      vip = ipaddress.ip_address(self.label_value)
      for interface in self.list_ifs():
        if 'network' in interface and vip in interface['network']:
          found = interface
          found['vip_if'] = ipaddress.ip_interface(str(vip) + '/' + str(interface['network'].prefixlen))
          break
    return found

  def on_enter(self):
    interface = self.get_interface()
    if interface is None:
      DAEMON.logger.error(f'No network interface to which a virtual IP {self.label_value} can be added was found.')
      return
    if interface['vip_if'].ip in interface['ips']:
      DAEMON.logger.info(f'vip {str(interface["vip_if"].ip)} is already bound on interface {interface["name"]} at on_enter')
      return
    self.setVip(interface)

  def setVip(self, interface):
    self.subprocess_run(['ip', 'addr', 'add', interface['vip_if'].with_prefixlen, 'dev', interface['name']])
    self.subprocess_run(['arping', '-c', '1', '-A', '-I', interface['name'], str(interface['vip_if'].ip)])
    if self.router:
      rest_count = 5
      while rest_count > 0:
        ping_proc = self.subprocess_run(['ping', '-c', '1', self.router, '-I', str(interface['vip_if'].ip)])
        if ping_proc.returncode == 0:
          return
        rest_count -= 1
        time.sleep(10)
      DAEMON.logger.error(f'Exceed max retry ping test count:5')
      self.clearVip(interface)

  def clearVip(self, interface):
    self.subprocess_run(['ip', 'addr', 'del', interface['vip_if'].with_prefixlen, 'dev', interface['name']])

  def on_leave(self):
    interface = self.get_interface()
    if interface is None:
      DAEMON.logger.error(f'any network interface is not found for vip {self.label_value}')
      return
    if interface['vip_if'].ip not in interface['ips']:
      DAEMON.logger.info(f'vip {str(interface["vip_if"].ip)} is not bound on interface {interface["name"]} at on_leave')
      return
    self.clearVip(interface)


class SetVIP0(SetVIP):
  label_name = 'HIVE_VIP0'
  router_label_name = 'HIVE_ROUTER0'


class SetVIP1(SetVIP):
  label_name = 'HIVE_VIP1'
  router_label_name = 'HIVE_ROUTER1'


class SetVIP2(SetVIP):
  label_name = 'HIVE_VIP2'
  router_label_name = 'HIVE_ROUTER2'


class SetVIP3(SetVIP):
  label_name = 'HIVE_VIP3'
  router_label_name = 'HIVE_ROUTER3'


class SetVIP4(SetVIP):
  label_name = 'HIVE_VIP4'
  router_label_name = 'HIVE_ROUTER4'


class SetVIP5(SetVIP):
  label_name = 'HIVE_VIP5'
  router_label_name = 'HIVE_ROUTER5'


class FollowSwarmServiceDaemon:
  def __init__(self):
    self.client = docker.from_env()
    client_info = self.client.info()
    self.node_name = client_info.get("Name")
    self.node_id = client_info.get('Swarm', {}).get('NodeID')
    self.logger = logging.getLogger(f'FollowSwarm@{self.node_name}')
    self.logger.debug(f'client.info():{json.dumps(client_info)}')
    self.hooks = {}
    self.hook_classes = [SetVIP, SetVIP0, SetVIP1, SetVIP2, SetVIP3, SetVIP4, SetVIP5, MarkNode]

  def list_hooks(self):
    for service in self.client.services.list():
      self.logger.debug(f'check if the service to be caputured: {service.name}')
      for hook_class in self.hook_classes:
        hook = hook_class.check_service(service)
        if hook is not None:
          yield hook

  def check_services(self):
    deleted_hooks = self.hooks.copy()
    new_hooks = []
    for hook in self.list_hooks():
      self.logger.debug(f'find a hook: {hook.id}')
      if hook.id in deleted_hooks:
        deleted_hooks.pop(hook.id)
      else:
        new_hooks.append(hook)
    for hook in deleted_hooks.values():
      self.logger.debug(f'{hook.id} is not found, so unregister it.')
      self.hooks.pop(hook.id)
      hook.on_unregistered()
    for hook in new_hooks:
      self.logger.debug(f'{hook.id} is new, so register it.')
      self.hooks[hook.id] = hook
      hook.on_registered()

  def check_tasks(self):
    for hook in self.hooks.values():
      hook.check_tasks()

  def hook_node_down(self):
    self.logger.info('shutdown process started')
    try:
      for hook in self.hooks.values():
        hook.on_node_down()
    except Exception as e:
      self.logger.exception(f'exception occur in shutdown process: {e}')

  def run(self):
    self.logger.info('Follow Swarm Service Daemon Started')
    self.check_services()
    try:
      for ev in self.client.events(decode=True):
        if ev.get('Type') == 'service':
          self.logger.debug('service type event received')
          self.check_services()
          self.logger.debug('container type event received')
        if ev.get('Type') == 'container':
          self.check_tasks()
      # when events() return End of Element, it means node is down
    except docker.errors.APIError as e:
      # raise exception from docker api, it means node is down
      self.logger.exception(f'fail to call docker api: {e}')
    except AssertionError as e:
      self.logger.exception(f'unexpected result: {e}')
    except KeyboardInterrupt:
      self.logger.info(f'keyboard interrupted')
    except SystemExit:
      self.logger.info(f'receive terminate signal')
    self.hook_node_down()
    self.logger.info('Follow Swarm Service Daemon Stopped')

  def get_node(self):
    node = None
    try:
      node = self.client.nodes.get(self.node_id)
    except Exception as e:
      self.logger.exception(f'fail to get node for {self.node_name}: %s', e)
    return node


def on_terminate(signum, frame):
  raise SystemExit('Signal received')


def main():
  global DAEMON
  signal.signal(signal.SIGTERM, on_terminate)
  try:
    DAEMON = FollowSwarmServiceDaemon()
  except docker.errors.APIError as e:
    logging.getLogger('FollowSwarm@UNKNOWN').error(f'fail to initialize docker client: {e}')
  DAEMON.run()


if __name__ == "__main__":
    main()
