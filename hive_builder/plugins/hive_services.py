#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 Procube Co., Ltd.

"""
hive inventory: dynamic inventory plugin for hive
"""

from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.errors import AnsibleParserError
from ansible.parsing.yaml.objects import AnsibleMapping, AnsibleSequence, AnsibleUnicode

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

    self._read_config_data(path)
    self.inventory.add_group('services')
    self.inventory.add_group('images')
    self.inventory.add_group('volumes')
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
    prepared_volumes = []
    for name, options in services.items():
      service = Service(name, options, available_on)
      service.parse(inventory)
      prepared_volumes += service.prepared_volumes
    inventory.set_variable('hives', 'hive_prepared_volumes', prepared_volumes)
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
      network = Network('hive_default_network', AnsibleMapping(), STAGES)
      network.parse(inventory)


IMAGE_PARAMS = ['from', 'roles', 'env', 'stop_signal', 'user', 'working_dir', 'standalone', 'entrypoint', 'command', 'privileged']
SERVICE_PARAMS_COPY = ['environment', 'ports', 'command', 'entrypoint', 'labels', 'mode', 'endpoint_mode', 'backup_scripts']
NETWORK_PARAMS = ['driver', 'ipam', 'driver_opts']
SERVICE_PARAMS = SERVICE_PARAMS_COPY + ['volumes', 'image', 'available_on']
VOLUME_PARAMS = ['target', 'type', 'volume', 'source']
VOLUME_PARAMS_DEF = ['driver', 'driver_opts', 'drbd']


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
        raise AnsibleParserError(f'unknown parameter {option_name} is specified in service {self.name}')
      inventory.set_variable(self.name, f'hive_{option_name}', option_value)


class Service:
  def __init__(self, name, options, available_on):
    self.name = name
    self.options = options
    self.available_on = available_on
    self.prepared_volumes = []

  def parse(self, inventory):
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
    if 'volumes' in self.options:
      volumes_value = self.options['volumes']
      if type(volumes_value) != AnsibleSequence:
        raise AnsibleParserError(f'"volumes" must be list type in service {self.name}, but {type(volumes_value)}')
      volumes = []
      for volume in volumes_value:
        if type(volume) == AnsibleUnicode:
          volumes.append(volume)
          # we do not prepare volume
        elif type(volume) == AnsibleMapping:
          if 'source' not in volume or 'target' not in volume:
              raise AnsibleParserError(f'both "source" and "target" must be specified in volume at service {self.name}')
          if 'driver' in volume:
            # we prepare volume at build-volume phase
            preared_volume = {'name': volume['source'], 'driver': volume['driver'], 'available_on': self.available_on}
            if 'driver_opts' in volume:
              volume['hive_driver_opts'] = volume['driver_opts']
            self.prepared_volumes.append(preared_volume)
          if 'drbd' in volume:
            if 'driver' in volume:
              raise AnsibleParserError(f'both "driver" and "drbd" can not be specified in volume at service {self.name}')
            self.prepared_volumes.append({'name': volume['source'], 'drbd': volume['drbd'], 'available_on': self.available_on})
          volume_value = {}
          for k, v in volume.items():
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
        for option_name, option_value in image_value.items():
          if option_name not in IMAGE_PARAMS:
            raise AnsibleParserError(f'unknown parameter {option_name} is specified in "image" at service {self.name}')
          inventory.set_variable(image_name, f'hive_{option_name}', option_value)
      else:
        raise AnsibleParserError(f'"image" must be dict type or str type in service {self.name}, but type is {type(image_value)}')
