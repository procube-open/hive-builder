#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 Procube Co., Ltd.

"""
hive inventory: dynamic inventory plugin for hive
"""

from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.errors import AnsibleParserError
import ipaddress

DOCUMENTATION = r'''
  name: hive_inventory
  plugin_type: inventory
  short_description: Returns Inventory for hive docker site
  description:
    - Generate vpcs, firewall, subnets, hosts resources

  options:
    plugin:
      description: token that ensures this is a source file for the 'hive_inventory' plugin.
      required: True
      choices: ['hive_inventory']
    name:
      description:
      - name of hive
      - all hosts can reffernce as hive_name
      - domein name format(ex. pdns.example.com) is recommended
      required: True
    stages:
      description: stage list
      required: True
      suboptions:
        stage:
          description: Name of the stage
          required: true
          choices: ['private', 'staging', 'production']
        provider:
          description: infrastructure provider
          required: true
          choices: ['vagrant', 'aws', 'azure', 'gcp', 'openstack', 'prepared']
        separate_repository:
          description: whether repository node is separated from swarm nodes
          type: bool
          default: true
        cidr:
          description: cidr of vpc
          required: true
        inbound_rules:
          description: inbound rules
          type: list
          suboptions:
            port:
              description: port number
              required: true
              type: int
            src:
              description: network addresses to ristrict source ip
              type: list
              default: ['0.0.0.0/0']
        number_of_hosts:
          description: number of hosts
          default: 4 if separate_repository else 3
          type: int
        subnets:
          description: list of subnet
          type: list
          suboptions:
            cidr:
              description: cidr of subnet
              required: true
            name:
              description: name of subnet
              default: "{name of site}_subnet_{index of item}"
            available_zone:
              description: available zone of subnet
              required: true
        memory_size:
          description: "memory size of hive hosts(only available when provider is 'vagrant')"
          type: int with unit(G,M,K)
          default: VirtualBox default
        cpus:
          description: "number of cpu of hive hosts(only available when provider is 'vagrant')"
          type: int
          default: VirtualBox default
        instance_type:
          description: "the instance type of hive hosts(availabe when provider is a IaaS)"
        image_name:
          description: "the source image of the hive host(availabe when provider is a IaaS)"
        region:
          description: "the region where hive hosts are located (availabe when provider is a IaaS)"
        disk_size:
          description: disk size of hive hosts
          type: int with unit(G,M,K)
          default: 20G
        mirrored_disk_size:
          description: disk size of hosts for drbd mirror disk, if not specified then hive does not provision mirrord disk
          type: int (megabyte)
        repository_memory_size:
          description: "memory size of hosts(only available when provider is 'vagrant')"
          type: int with unit(G,M,K)
          default: 512M
        repository_instance_type:
          description: "instance type of host(availabe when provider is a IaaS)"
        repository_disk_size:
          description: disk size of hosts
          type: int with unit(G,M,K)
          default: 40G
'''

EXAMPLES = r'''
plugin: hive_inventory
name: test.example.com
stages:
  private:
    provider: vagrant
    separate_repository: False
    subnets:
    - cidr: 192.168.0.96/29
'''


class InventoryModule(BaseInventoryPlugin):

  NAME = 'hive_inventory'  # used internally by Ansible, it should match the file name but not required

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
    self.inventory.add_group('servers')
    self.inventory.add_group('hives')
    self.inventory.add_group('repository')
    self.inventory.add_group('first_hive')
    self.inventory.add_group('mother')
    self.inventory.add_child('servers', 'hives')
    self.inventory.add_child('servers', 'repository')
    self.name = self.get_option('name')
    self.inventory.set_variable('all', 'hive_name', self.name)
    stages = self.get_option('stages')
    for stage_name, option in stages.items():
      stage = Stage(self.name, stage_name, option, inventory)
      stage.set_provider()
      stage.add_stage_group()
      stage.set_subnets()
      stage.add_hives()


class Stage:
  def __init__(self, name, stage_name, option, inventory):
    self.stage_name = stage_name
    self.name = name
    self.stage = option
    self.inventory = inventory
    if self.stage_name not in ['private', 'staging', 'production']:
      raise AnsibleParserError(f'stage must be one of "private", "staging", "production", but specified {self.stage_name}')
    self.stage_prefix = 'p-' if self.stage_name == 'private' else 's-' if self.stage_name == 'staging' else ''

  def set_provider(self):
    if 'provider' not in self.stage:
      raise AnsibleParserError('provider must be specified')
    self.provider = self.stage['provider']
    if self.provider not in ['vagrant', 'aws', 'azure', 'gcp', 'openstack', 'prepared']:
      raise AnsibleParserError(f'provider must be one of "vagrant", "aws", "azure", "gcp", "openstack", "prepared", but specified {self.provider}')
    if 'disk_size' in self.stage:
      self.disk_size = self.stage['disk_size']
    if 'repository_disk_size' in self.stage:
      self.repository_disk_size = self.stage['repository_disk_size']
    if 'root_password' in self.stage:
      self.root_password = self.stage['root_password']
    if self.provider == 'vagrant':
      if 'instance_type' in self.stage:
        raise AnsibleParserError('instance_type cannot be specified when provider is vagrant')
      if 'region' in self.stage:
        raise AnsibleParserError('region cannot be specified when provider is vagrant')
      if 'memory_size' in self.stage:
        self.memory_size = self.stage['memory_size']
      if 'repository_memory_size' in self.stage:
        self.repository_memory_size = self.stage['repository_memory_size']
      if 'cpus' in self.stage:
        self.cpus = self.stage['cpus']
      if 'repository_cpus' in self.stage:
        self.repository_cpus = self.stage['repository_cpus']
    else:
      if 'memory_size' in self.stage:
        raise AnsibleParserError('memory_size cannot be specified when provider is IaaS')
      if 'repository_memory_size' in self.stage:
        raise AnsibleParserError('repository_memory_size cannot be specified when provider is IaaS')
      if 'bridge' in self.stage:
        raise AnsibleParserError('bridge cannot be specified when provider is IaaS')
      if 'instance_type' in self.stage:
        self.instance_type = self.stage['instance_type']
      if 'repository_instance_type' in self.stage:
        self.repository_instance_type = self.stage['repository_instance_type']

  def add_stage_group(self):
    self.inventory.add_group(self.stage_name)
    self.inventory.set_variable(self.stage_name, 'hive_provider', self.provider)

  def set_subnets(self):
    self.subnets = []
    if 'cidr' not in self.stage:
      raise AnsibleParserError('cidr must be specified')
    mother_name = f'{self.stage_prefix}mother.{self.name}'
    self.inventory.add_host(mother_name, group='mother')
    self.inventory.add_host(mother_name, group=self.stage_name)
    self.inventory.set_variable(mother_name, 'hive_cidr', self.stage['cidr'])
    if 'region' in self.stage:
      self.inventory.set_variable(mother_name, 'hive_region', self.stage['region'])
    if 'subnets' not in self.stage:
      try:
        net = ipaddress.ip_network(self.stage['cidr'])
      except ValueError as e:
        raise AnsibleParserError(str(e))
      if 'ip_address_list' in self.stage:
        self.subnets.append({'ip_list': (y for y in self.stage.get('ip_address_list')), 'netmask': str(net.netmask)})
      else:
        hosts = net.hosts()
        # first one is route, so skip it
        next(hosts)
        self.subnets.append({'ip_list': map(str, hosts), 'netmask': str(net.netmask)})
    else:
      var_subnets = []
      for idx, s in enumerate(self.stage['subnets']):
        subnet = s.copy()
        var_subnets.append(s)
        if 'name' not in subnet:
          subnet['name'] = f'{self.stage_prefix}subnet{idx}'
        if 'cidr' not in subnet:
          raise AnsibleParserError('cidr in subnet must be specified')
        try:
          net = ipaddress.ip_network(subnet['cidr'])
        except ValueError as e:
          raise AnsibleParserError(str(e))
        hosts = net.hosts()
        # first one is route, so skip it
        next(hosts)
        # aws use 3 more address https://aws.amazon.com/jp/vpc/faqs/
        next(hosts)
        next(hosts)
        next(hosts)
        subnet['ip_list'] = map(str, hosts)
        subnet['netmask'] = str(net.netmask)
        self.subnets.append(subnet)
      self.inventory.set_variable(mother_name, 'hive_subnets', var_subnets)

  def add_hives(self):
    separate_repository = self.stage.get('separate_repository', True)
    number_of_hosts = self.stage.get('number_of_hosts', 4 if separate_repository else 3)
    if 'ip_address_list' in self.stage:
      number_of_hosts = len(self.stage.get('ip_address_list'))
    for idx in range(number_of_hosts):
      host_name = f'{self.stage_prefix}hive{idx}.{self.name}'
      self.inventory.add_host(host_name, group=self.stage_name)
      if hasattr(self, 'root_password'):
        self.inventory.set_variable(host_name, 'hive_root_password', self.root_password)
      if idx == number_of_hosts - 1:
        if not separate_repository:
          self.inventory.add_host(host_name, group='hives')
          if hasattr(self, 'memory_size'):
            self.inventory.set_variable(host_name, 'hive_memory_size', self.memory_size)
          if hasattr(self, 'cpus'):
            self.inventory.set_variable(host_name, 'hive_cpus', self.memory_size)
          if hasattr(self, 'disk_size'):
            self.inventory.set_variable(host_name, 'hive_disk_size', self.disk_size)
          if hasattr(self, 'instance_type'):
            self.inventory.set_variable(host_name, 'hive_instance_type', self.instance_type)
          if 'mirrored_disk_size' in self.stage:
            self.inventory.set_variable(host_name, 'hive_mirrored_disk_size', self.stage['mirrored_disk_size'])
        self.inventory.add_host(host_name, group='repository')
        if hasattr(self, 'repository_memory_size'):
          self.inventory.set_variable(host_name, 'hive_memory_size', self.repository_memory_size)
        if hasattr(self, 'repository_cpus'):
          self.inventory.set_variable(host_name, 'hive_cpus', self.repository_memory_size)
        if hasattr(self, 'repository_disk_size'):
          self.inventory.set_variable(host_name, 'hive_disk_size', self.repository_disk_size)
        if hasattr(self, 'repository_instance_type'):
          self.inventory.set_variable(host_name, 'hive_instance_type', self.repository_instance_type)
      else:
        self.inventory.add_host(host_name, group='hives')
        if hasattr(self, 'memory_size'):
          self.inventory.set_variable(host_name, 'hive_memory_size', self.memory_size)
        if hasattr(self, 'cpus'):
          self.inventory.set_variable(host_name, 'hive_cpus', self.memory_size)
        if hasattr(self, 'disk_size'):
          self.inventory.set_variable(host_name, 'hive_disk_size', self.disk_size)
        if hasattr(self, 'instance_type'):
          self.inventory.set_variable(host_name, 'hive_instance_type', self.instance_type)
        if 'mirrored_disk_size' in self.stage:
          self.inventory.set_variable(host_name, 'hive_mirrored_disk_size', self.stage['mirrored_disk_size'])

      if 'image_name' in self.stage:
        self.inventory.set_variable(host_name, 'hive_image_name', self.stage['image_name'])

      subnet = self.subnets[idx % len(self.subnets)]
      if 'name' in subnet:
        self.inventory.set_variable(host_name, 'hive_subnet', subnet['name'])
      if 'available_zone' in subnet:
        self.inventory.set_variable(host_name, 'hive_available_zone', subnet['available_zone'])
      self.inventory.set_variable(host_name, 'hive_private_ip', next(subnet['ip_list']))
      self.inventory.set_variable(host_name, 'hive_netmask', subnet['netmask'])
    self.inventory.set_variable('hives', 'hive_swarm_master', f'{self.stage_prefix}hive0.{self.name}')
    self.inventory.add_host(f'{self.stage_prefix}hive0.{self.name}', group='first_hive')
