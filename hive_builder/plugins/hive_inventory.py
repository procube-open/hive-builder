#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 Procube Co., Ltd.

"""
hive inventory: dynamic inventory plugin for hive
"""

from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.errors import AnsibleParserError
import ipaddress
import os
import re

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
          choices: ['vagrant', 'aws', 'azure', 'gcp', 'openstack', 'prepared', 'kickstart']
        separate_repository:
          description: whether repository node is separated from swarm nodes
          type: bool
          default: true
        cidr:
          description: cidr of vpc
          required: true
        # inbound_rules:
        #   description: inbound rules
        #   type: list
        #   suboptions:
        #     port:
        #       description: port number
        #       required: true
        #       type: int
        #     src:
        #       description: network addresses to ristrict source ip
        #       type: list
        #       default: ['0.0.0.0/0']
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
        drbd_download_url:
          description: "download url for drbd"
        instance_type:
          description: "the instance type of hive hosts(availabe when provider is a IaaS)"
        image_name:
          description: "the source image of the hive host(availabe when provider is a IaaS)"
        region:
          description: "the region where hive hosts are located (availabe when provider is a IaaS)"
        prepared_resource_group:
          description: "do not create/destory resource group (available when provider is azure)"
        not_support_az:
          description: "do not distributes vm to Availability Zone (available when provider is azure)"
        disk_size:
          description: disk size of hive hosts
          type: int with unit(G,M,K)
          default: 20G
        disk_encrypted:
          description: disk of hive hosts is encrypted
          type: bool
          default: False
        kms_key_id:
          description: "key id for encryption (availabe when provider is aws)"
        kernel_version:
          description: "kernel version to be updated at base role"
        mirrored_disk_size:
          description: disk size of hosts for drbd mirror disk, if not specified then hive does not provision mirrord disk
          type: int (megabyte)
        mirrored_disk_encrypted:
          description: mirrored disk is encrypted
          type: bool
          default: False
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
        repository_disk_encrypted:
          description: disk of repository server is encrypted
          type: bool
          default: False
        root_password:
          description: "password of root user (only available when provider is 'preapred')"
        kickstart_config:
          description: configuration for kickstart file, availble on kickstart provider
          type: dict
          suboptions:
            iso_src:
              description: iso image source file or device, availble on kickstart provider
            iso_dest:
              description: iso image destination file or device, availble on kickstart provider
            networks:
              description: interace definition for tagged vlans, availble on kickstart provider
              type: list
              suboptions:
                interface:
                  description: interface name
                  required: true
                vlanid:
                  description: vlan id 1-4095
                  type: int
                ips:
                  description: ip address list
                  type: list
                  required: true
                netmask:
                  description: netmask
                  required: true
                gateway:
                  description: ip adderss of gateway
                nameservers:
                  description: name servers
                  type: list
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
    self.inventory.add_group('hosts')
    self.inventory.add_child('servers', 'hives')
    self.inventory.add_child('servers', 'repository')
    self.inventory.add_child('hosts', 'servers')
    self.inventory.add_child('hosts', 'mother')
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
    if self.provider not in ['vagrant', 'aws', 'azure', 'gcp', 'openstack', 'prepared', 'kickstart']:
      raise AnsibleParserError(f'provider must be one of "vagrant", "aws", "azure", "gcp", "openstack", "prepared", "kickstart", but specified {self.provider}')
    if self.provider != 'kickstart' and 'kickstart_config' in self.stage:
      raise AnsibleParserError('kickstart_config cannot be specified when provider is not kickstart')
    if self.provider == 'vagrant':
      if 'instance_type' in self.stage:
        raise AnsibleParserError('instance_type cannot be specified when provider is vagrant')
      if 'region' in self.stage:
        raise AnsibleParserError('region cannot be specified when provider is vagrant')
    else:
      if 'prepared_resource_group' in self.stage and self.provider != 'azure':
        raise AnsibleParserError('prepared_resource_group is only available when provider is "azure"')
      if 'not_support_az' in self.stage and self.provider != 'azure':
        raise AnsibleParserError('not_support_az is only available when provider is "azure"')
      if self.provider not in ['kickstart', 'prepared'] and 'memory_size' in self.stage:
        raise AnsibleParserError('memory_size cannot be specified when provider is IaaS')
      if 'repository_memory_size' in self.stage:
        raise AnsibleParserError('repository_memory_size cannot be specified when provider is IaaS')
      if 'dev' in self.stage:
        raise AnsibleParserError('dev cannot be specified when provider is IaaS')
      if 'bridge' in self.stage:
        raise AnsibleParserError('bridge cannot be specified when provider is IaaS')

  def add_stage_group(self):
    self.inventory.add_group(self.stage_name)
    self.inventory.set_variable(self.stage_name, 'hive_provider', self.provider)
    custom_hostname = self.stage.get('custom_hostname', 'hive')
    hostname_pattern = r'^[a-z0-9][a-z0-9-]*[a-z0-9]$'
    if not (re.match(hostname_pattern, custom_hostname) and (len(custom_hostname)) + len(self.name) < 55):
      raise AnsibleParserError('custom_hostname must consist of alphanumeric and hyphens, and custom_hostname + inventory_name be up to 55 in length')
    self.inventory.set_variable(self.stage_name, 'hive_custom_hostname', custom_hostname)

  def set_subnets(self):
    self.subnets = []
    if 'cidr' not in self.stage:
      raise AnsibleParserError('cidr must be specified')
    mother_name = f'{self.stage_prefix}mother.{self.name}'
    self.inventory.add_host(mother_name, group='mother')
    self.inventory.add_host(mother_name, group=self.stage_name)
    self.inventory.set_variable(mother_name, 'hive_cidr', self.stage['cidr'])
    if 'prepared_resource_group' in self.stage:
      self.inventory.set_variable(mother_name, 'hive_prepared_resource_group', self.stage['prepared_resource_group'])
    if 'not_support_az' in self.stage:
      self.inventory.set_variable(mother_name, 'hive_not_support_az', self.stage['not_support_az'])
    if 'region' in self.stage:
      self.inventory.set_variable(mother_name, 'hive_region', self.stage['region'])
    if 'bridge' in self.stage:
      self.inventory.set_variable(mother_name, 'hive_bridge', self.stage['bridge'])
    if 'dev' in self.stage:
      self.inventory.set_variable(mother_name, 'hive_dev', self.stage['dev'])
    if 'kickstart_config' in self.stage:
      self.inventory.set_variable(mother_name, 'hive_kickstart_config', self.stage['kickstart_config'])
    if 'filestore_cidr' in self.stage:
      self.inventory.set_variable(mother_name, 'hive_filestore_cidr', self.stage['filestore_cidr'])
    if 'subnets' not in self.stage:
      try:
        net = ipaddress.ip_network(self.stage['cidr'])
      except ValueError as e:
        raise AnsibleParserError(str(e))
      default_subnet = {'cidr': self.stage['cidr'], 'name': self.name + '-default'}
      self.inventory.set_variable(mother_name, 'hive_subnets', [default_subnet.copy()])
      default_subnet['netmask'] = str(net.netmask)
      if 'ip_address_list' in self.stage:
        default_subnet['ip_list'] = (y for y in self.stage.get('ip_address_list'))
      else:
        hosts = net.hosts()
        # first one is route, so skip it
        next(hosts)
        # azure use 2 more address https://docs.microsoft.com/en-us/azure/virtual-network/virtual-networks-faq
        next(hosts)
        next(hosts)
        default_subnet['ip_list'] = map(str, hosts)
      self.subnets.append(default_subnet)
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
    custom_hostname = self.stage.get('custom_hostname', 'hive')
    hostname_pattern = r'^[a-z0-9][a-z0-9-]*[a-z0-9]$'
    if not (re.match(hostname_pattern, custom_hostname) and (len(custom_hostname)) + len(self.name) < 55):
      raise AnsibleParserError('custom_hostname must consist of alphanumeric and hyphens, and custom_hostname + inventory_name be up to 55 in length')
    if 'ip_address_list' in self.stage:
      number_of_hosts = len(self.stage.get('ip_address_list'))
    for idx in range(number_of_hosts):
      host_name = f'{self.stage_prefix}{custom_hostname}{idx}.{self.name}'
      self.inventory.add_host(host_name, group=self.stage_name)
      if 'root_password' in self.stage:
        self.inventory.set_variable(host_name, 'hive_root_password', self.stage['root_password'])
      if 'kernel_version' in self.stage:
        self.inventory.set_variable(host_name, 'hive_kernel_version', self.stage['kernel_version'])
      if 'drbd_download_url' in self.stage:
        self.inventory.set_variable(host_name, 'hive_drbd_download_url', self.stage['drbd_download_url'])
      if 'internal_cidr' in self.stage:
        self.inventory.set_variable(host_name, 'hive_internal_cidr', self.stage['internal_cidr'])
      if 'internal_cidr_v6' in self.stage:
        self.inventory.set_variable(host_name, 'hive_internal_cidr_v6', self.stage['internal_cidr_v6'])
      if 'kms_key_id' in self.stage:
        self.inventory.set_variable(host_name, 'hive_kms_key_id', self.stage['kms_key_id'])
      if idx == number_of_hosts - 1:
        if not separate_repository:
          self.inventory.add_host(host_name, group='hives')
          if 'memory_size' in self.stage:
            self.inventory.set_variable(host_name, 'hive_memory_size', self.stage['memory_size'])
          if 'cpus' in self.stage:
            self.inventory.set_variable(host_name, 'hive_cpus', self.stage['cpus'])
          if 'disk_size' in self.stage:
            self.inventory.set_variable(host_name, 'hive_disk_size', self.stage['disk_size'])
          if 'disk_encrypted' in self.stage:
            self.inventory.set_variable(host_name, 'hive_disk_encrypted', self.stage['disk_encrypted'])
          if 'instance_type' in self.stage:
            self.inventory.set_variable(host_name, 'hive_instance_type', self.stage['instance_type'])
          if 'mirrored_disk_size' in self.stage:
            self.inventory.set_variable(host_name, 'hive_mirrored_disk_size', self.stage['mirrored_disk_size'])
          if 'mirrored_disk_encrypted' in self.stage:
            if 'kms_key_id' not in self.stage:
              raise AnsibleParserError('mirrored_disk_encrypted require kms_key_id')
            self.inventory.set_variable(host_name, 'hive_mirrored_disk_encrypted', self.stage['mirrored_disk_encrypted'])
        self.inventory.add_host(host_name, group='repository')
        if 'repository_memory_size' in self.stage:
          self.inventory.set_variable(host_name, 'hive_memory_size', self.stage['repository_memory_size'])
        if 'repository_cpus' in self.stage:
          self.inventory.set_variable(host_name, 'hive_cpus', self.stage['repository_cpus'])
        if 'repository_disk_size' in self.stage:
          self.inventory.set_variable(host_name, 'hive_disk_size', self.stage['repository_disk_size'])
        if 'repository_disk_encrypted' in self.stage:
          if 'kms_key_id' not in self.stage:
            raise AnsibleParserError('repository_disk_encrypted require kms_key_id')
          self.inventory.set_variable(host_name, 'hive_disk_encrypted', self.stage['repository_disk_encrypted'])
        if 'repository_instance_type' in self.stage:
          self.inventory.set_variable(host_name, 'hive_instance_type', self.stage['repository_instance_type'])
      else:
        self.inventory.add_host(host_name, group='hives')
        if 'memory_size' in self.stage:
          self.inventory.set_variable(host_name, 'hive_memory_size', self.stage['memory_size'])
        if 'cpus' in self.stage:
          self.inventory.set_variable(host_name, 'hive_cpus', self.stage['cpus'])
        if 'disk_size' in self.stage:
          self.inventory.set_variable(host_name, 'hive_disk_size', self.stage['disk_size'])
        if 'disk_encrypted' in self.stage:
          if 'kms_key_id' not in self.stage:
            raise AnsibleParserError('disk_encrypted require kms_key_id')
          self.inventory.set_variable(host_name, 'hive_disk_encrypted', self.stage['disk_encrypted'])
        if 'instance_type' in self.stage:
          self.inventory.set_variable(host_name, 'hive_instance_type', self.stage['instance_type'])
        if 'mirrored_disk_size' in self.stage:
          self.inventory.set_variable(host_name, 'hive_mirrored_disk_size', self.stage['mirrored_disk_size'])
        if 'mirrored_disk_encrypted' in self.stage:
          self.inventory.set_variable(host_name, 'hive_mirrored_disk_encrypted', self.stage['mirrored_disk_encrypted'])

      if 'image_name' in self.stage:
        self.inventory.set_variable(host_name, 'hive_vm_image_name', self.stage['image_name'])

      subnet = self.subnets[idx % len(self.subnets)]
      if 'name' in subnet:
        self.inventory.set_variable(host_name, 'hive_subnet', subnet['name'])
      if 'region' in self.stage:
        az_suffix_list = self.stage.get('az_suffix_list', ['-a', '-b', '-c'])
        az_default = self.stage['region'] + az_suffix_list[idx % len(az_suffix_list)]
        if self.provider == 'azure':
          az_default = (idx % 3) + 1
        self.inventory.set_variable(host_name, 'hive_available_zone', subnet.get('available_zone', az_default))
      self.inventory.set_variable(host_name, 'hive_private_ip', next(subnet['ip_list']))
      self.inventory.set_variable(host_name, 'hive_netmask', subnet['netmask'])
    self.inventory.set_variable('hives', 'hive_swarm_master', f'{self.stage_prefix}{custom_hostname}{os.getenv("HIVE_FIRST_HIVE")}.{self.name}')
    self.inventory.add_host(f'{self.stage_prefix}{custom_hostname}{os.getenv("HIVE_FIRST_HIVE")}.{self.name}', group='first_hive')
