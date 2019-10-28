#!/usr/bin/env python
# -*- coding: utf-8 -*-
# this module is downloaded from https://raw.githubusercontent.com/robparrott/ansible-vagrant/master/library/vagrant
#  2019/06/17 Mitsuru Nakakawaji <mitsuru@procube.jp>

# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from ansible.module_utils.basic import AnsibleModule
import sys
import subprocess
import os.path

DOCUMENTATION = '''
---
module: vagrant
short_description: create a local instance via vagrant
description:
     - creates VM instances via vagrant and optionally waits for it to be 'running'. This module has a dependency on python-vagrant.
version_added: "100.0"
options:
  state:
    description: Should the VMs be "present" or "absent."
  cmd:
    description:
      - vagrant subcommand to execute. Can be "up," "status," "config," "ssh," "halt," "destroy" or "clear."
    required: false
    default: null
    aliases: ['command']
  box_name:
    description:
      - vagrant boxed image to start
    required: false
    default: null
    aliases: ['image']
  box_path:
    description:
      - path to vagrant boxed image to start
    required: false
    default: null
    aliases: []
  instaces:
    description:
      - list of instance definition dict has inventory_hostname, private_ip
    required: True
  forward_ports:
    description:
      - comma separated list of ports to forward to the host
    required: False
    aliases: []
  vagrant_dir:
    description:
      - directory where vagrant command is executed
    required: True
  vm_name:
    description:
      - name of VM
    required: false
    default: null
    aliases: []

examples:
   - code: 'local_action: vagrant cmd=up box_name=lucid32 vm_name=webserver'
     description:
requirements: [ "vagrant" ]
author: Rob Parrott
'''

VAGRANT_FILE = "./Vagrantfile"
VAGRANT_DICT_FILE = "./Vagrantfile.json"
VAGRANT_LOCKFILE = "./.vagrant-lock"

VAGRANT_FILE_HEAD = "Vagrant::Config.run do |config|\n"
VAGRANT_FILE_BOX_NAME = "  config.vm.box = \"%s\"\n"
VAGRANT_FILE_VM_STANZA_HEAD = """
  config.vm.define :%s do |%s_config|
    %s_config.vm.network :hostonly, "%s"
    %s_config.vm.box = "%s"
"""
VAGRANT_FILE_HOSTNAME_LINE = "    %s_config.vm.host_name = \"%s\"\n"
VAGRANT_FILE_PORT_FORWARD_LINE = "    %s_config.vm.forward_port %s, %s\n"
VAGRANT_FILE_VM_STANZA_TAIL = "  end\n"

VAGRANT_FILE_TAIL = "\nend\n"

# If this is already a network on your machine, this may fail ... change it here.
VAGRANT_INT_IP = "192.168.179.%s"

DEFAULT_VM_NAME = "ansible"


try:
  import lockfile
except ModuleNotFoundError:
  print('Python module lockfile is not installed. Falling back to using flock(), which will fail on Windows.')

try:
  import vagrant
except ModuleNotFoundError:
  print("failed=True msg='python-vagrant required for this module'")
  sys.exit(1)


class VagrantWrapper(object):

  def __init__(self):
    '''
    Wrapper around the python-vagrant module for use with ansible.
    Note that Vagrant itself is non-thread safe, as is the python-vagrant lib, so we need to lock on basically all operations ...
    '''
    # Get a lock
    self.lock = None

    try:
      self.lock = lockfile.FileLock(VAGRANT_LOCKFILE)
      self.lock.acquire()
    except Exception:
      # fall back to using flock instead ...
      try:
        import fcntl
        self.lock = open(VAGRANT_LOCKFILE, 'w')
        fcntl.flock(self.lock, fcntl.LOCK_EX)
      except Exception:
        print("failed=True msg='Could not get a lock for using vagrant. Install python module \"lockfile\" to use vagrant on non-POSIX filesytems.'")
        sys.exit(1)

    # Initialize vagrant and state files
    self.vg = vagrant.Vagrant()

    # operation will create a default data structure if none present
    self.vg_data = {"instances": {}, "num_inst": 0}

  def __del__(self):
    "Clean up file locks"
    try:
      self.lock.release()
    except Exception:
      os.close(self.lock)
      os.unlink(self.lock)

  def prepare_box(self, box_name, box_path):
    """
    Given a specified name and URL, import a Vagrant "box" for use.
    """
    changed = False
    if box_name is None:
      raise Exception("You must specify a box_name with a box_path for vagrant.")
    boxes = self.vg.box_list()
    if box_name not in boxes:
      self.vg.box_add(box_name, box_path)
      changed = True

    return changed

  def build_instances(self, box_name, instances, box_path=None, ports=[]):
    """
    Fire up a given VM and name it, using vagrant's multi-VM mode.
    """
    changed = False
    if box_name is None:
      raise Exception("You must specify a box name for Vagrant.")
    if box_path is not None and self.prepare_box(box_name, box_path):
      changed = True

    for instance in instances:

      d = self._get_instance(instance['inventory_hostname'], instance['hive_private_ip'])
      if 'box_name' not in d:
        d['box_name'] = box_name
      d['forward_ports'] = ports

      # Save our changes and run
      self._instances()[instance['inventory_hostname']] = d

    return changed

  def up(self, check_mode, vm_name=None):
    changed = False

    vm_names = []
    if vm_name is not None:
      vm_names = [vm_name]
    else:
      vm_names = self._instances().keys()
    statuses = {}
    for vmn in vm_names:
      if self._get_status(vmn) != 'running':
        if not check_mode:
          self.vg.up(vmn, provision=True)
        changed = True
      statuses[vmn] = self._get_status(vmn)

    # ad = self._build_instance_array_for_ansible()
    return (changed, statuses)

  def status(self, vm_name=None):
    """
    Return the run status of the VM instance. If no instance N is given, returns first instance.
    """
    vm_names = []
    if vm_name is not None:
      vm_names = [vm_name]
    else:
      vm_names = self._instances().keys()

    statuses = {}
    for vmn in vm_names:
      statuses[vmn] = self._get_status(vmn)

    return (False, statuses)

  def config(self, vm_name=None):
    """
    Return info on SSH for the running instance.
    """
    vm_names = []
    if vm_name is not None:
      vm_names = [vm_name]
    else:
      vm_names = self._instances().keys()

    configs = {}
    for vmn in vm_names:
      cnf = self.vg.conf(None, vmn)
      configs[vmn] = cnf

    return (False, configs)

  def halt(self, check_mode, vm_name=None):
    """
    Shuts down a vm_name or all VMs.
    """
    changed = False
    vm_names = []
    if vm_name is not None:
      vm_names = [vm_name]
    else:
      vm_names = self._instances().keys()

    statuses = {}
    for vmn in vm_names:
      if self._get_status(vmn) == 'running':
        if not check_mode:
          self.vg.halt(vmn)
        changed = True
      statuses[vmn] = self._get_status(vmn)[0]

    return (changed, statuses)

  def destroy(self, check_mode, vm_name=None):
    """
    Halt and remove data for a VM, or all VMs.
    """
    changed = False

    vm_names = []
    if vm_name is not None:
      vm_names = [vm_name]
    else:
      vm_names = self._instances().keys()

    statuses = {}
    for vmn in vm_names:
      if not self._get_status(vmn) in ['absent', 'not_created']:
        if not check_mode:
          self.vg.destroy(vmn)
        changed = True
      statuses[vmn] = self._get_status(vmn)

    return (changed, statuses)

  def clear(self, check_mode, vm_name=None):
    """
    Halt and remove data for a VM, or all VMs. Also clear all state data
    """
    changed = self.vg.destroy(check_mode, vm_name)

    if os.path.isfile(VAGRANT_FILE):
      if not check_mode:
        os.remove(VAGRANT_FILE)
      changed = True
    if os.path.isfile(VAGRANT_DICT_FILE):
      if not check_mode:
        os.remove(VAGRANT_DICT_FILE)
      changed = True

    return changed

#
# Helper Methods
#

  def _instances(self):
    return self.vg_data['instances']

  def _get_instance(self, vm_name, ip):

    instances = self._instances()

    if vm_name in instances:
      return instances[vm_name]

    #
    # otherwise create one afresh
    #

    d = dict()
    N = self.vg_data['num_inst'] + 1
    # n = len(instances.keys())+1
    d['N'] = N
    d['name'] = vm_name
    d['internal_ip'] = ip
    d['forward_ports'] = []
    self.vg_data['num_inst'] = N

    self._instances()[vm_name] = d

    return d

  def _get_status(self, name):
    state = 'absent'
    try:
      state = self.vg.status(name)[0].state
    except Exception:
      pass
    return state

  #
  # Translate the state dictionary into the Vagrantfile
  #
  def write_vagrantfile(self):

    vfile = open(VAGRANT_FILE, 'w')
    vfile.write(VAGRANT_FILE_HEAD)

    instances = self._instances()
    for vm_name in instances.keys():
      d = instances[vm_name]
      name = d['name']
      ip = d['internal_ip']
      box_name = d['box_name']
      vfile.write(VAGRANT_FILE_VM_STANZA_HEAD %
                  (name, name, name, ip, name, box_name))
      vfile.write(VAGRANT_FILE_HOSTNAME_LINE % (name, name.replace('_', '-')))
      if 'forward_ports' in d:
        for p in d['forward_ports']:
          vfile.write(VAGRANT_FILE_PORT_FORWARD_LINE % (name, p, p))
      vfile.write(VAGRANT_FILE_VM_STANZA_TAIL)

    vfile.write(VAGRANT_FILE_TAIL)
    vfile.close()

  #
  # To be returned to ansible with info about instances
  #
  def _build_instance_array_for_ansible(self, vmname=None):

    vm_names = []
    instances = self._instances()
    if vmname is not None:
      vm_names = [vmname]
    else:
      vm_names = instances.keys()

    ans_instances = []
    for vm_name in vm_names:
      cnf = self.vg.conf(None, vm_name)
      if cnf is not None:
        d = {
            'name': vm_name,
            'id': cnf['Host'],
            'public_ip': cnf['HostName'],
            'internal_ip': instances[vm_name]['internal_ip'],
            'public_dns_name': cnf['HostName'],
            'port': cnf['Port'],
            'username': cnf['User'],
            'key': cnf['IdentityFile'],
            'status': self._get_status(vm_name)
        }
        ans_instances.append(d)

    return ans_instances

# --------
# MAIN
# --------


def main():

  module = AnsibleModule(
      argument_spec=dict(
          state=dict(),
          cmd=dict(required=False, aliases=['command']),
          box_name=dict(required=False, aliases=['image']),
          box_path=dict(),
          instances=dict(required=True, type='list', elements='dict'),
          forward_ports=dict(),
          vagrant_dir=dict(required=True)
      ),
      supports_check_mode=True
  )

  state = module.params.get('state')
  cmd = module.params.get('cmd')
  box_name = module.params.get('box_name')
  box_path = module.params.get('box_path')
  forward_ports = module.params.get('forward_ports')
  vagrant_dir = module.params.get('vagrant_dir')
  vm_name = module.params.get('vm_name')
  changed = False

  if forward_ports is not None:
    forward_ports = forward_ports.split(',')
  if forward_ports is None:
    forward_ports = []

  instances = module.params.get('instances')

  #
  # Check if we are being invoked under an idempotency idiom of "state=present" or "state=absent"
  #
  try:
    # Initialize vagrant
    os.chdir(vagrant_dir)
    vgw = VagrantWrapper()
    if vgw.build_instances(box_name, instances, box_path, forward_ports):
      changed = True

    if state is not None:

      if state != 'present' and state != 'absent':
        module.fail_json(msg="State must be \"present\" or \"absent\" in vagrant module.")

      if state == 'present':

        # vgw.write_vagrantfile()
        (changed, status) = vgw.up(module.check_mode)
        module.exit_json(changed=changed, status=status)

      if state == 'absent':
        (changed, status) = vgw.halt()
        module.exit_json(changed=changed, status=status)
    else:
      if cmd is None:
        module.fail_json(msg="either cmd or state must be specified in vagrant module.")

      if cmd == 'up':

        # vgw.write_vagrantfile()
        (changed, status) = vgw.up(module.check_mode)
        module.exit_json(changed=changed, status=status)

      elif cmd == 'status':

        # if vm_name == None:
        #    module.fail_json(msg="Error: you must specify a vm_name when calling status." )

        (changed, result) = vgw.status()
        module.exit_json(changed=changed, status=result)

      elif cmd == "config" or cmd == "conf":

        (changed, cnf) = vgw.config()
        module.exit_json(changed=changed, config=cnf)

      elif cmd == 'ssh':

        if vm_name is None:
          module.fail_json(msg="Error: you must specify a vm_name when calling ssh.")

        (changed, cnf) = vgw.config(vm_name)
        sshcmd = "ssh -i %s -p %s %s@%s" % (cnf["IdentityFile"], cnf["Port"], cnf["User"], cnf["HostName"])
        sshmsg = "Execute the command \"vagrant ssh %s\"" % (vm_name)
        module.exit_json(changed=changed, msg=sshmsg, SshCommand=sshcmd)

#            elif cmd == "load_key":
#
#                if vm_name == None:
#                    module.fail_json(msg="Error: you must specify a vm_name when calling load_key." )
#
#                cnf = vg.config(vm_name)
#                keyfile=cnf["IdentityFile"]
#
#                # Get loaded keys ...
#                loaded_keys = subprocess.check_output(["ssh-add", "-l"])
#                module.exit_json(changed = True, msg = loaded_keys)
#
#                subprocess.call(["ssh-add", keyfile])
#
#                module.exit_json(changed = True, msg = sshmsg, SshCommand = sshcmd)

      elif cmd == 'halt':

        (changed, status) = vgw.halt(module.check_mode)
        module.exit_json(changed=changed, status=status)

      elif cmd == 'destroy':

        (changed, status) = vgw.destroy(module.check_mode)
        module.exit_json(changed=changed, status=status)

      elif cmd == 'clear':

        changed = vgw.clear()
        module.exit_json(changed=changed)

      else:

        module.fail_json(msg="Unknown vagrant subcommand: \"%s\"." % (cmd))

  except subprocess.CalledProcessError as e:
    module.fail_json(msg="Vagrant command failed: %s. cwd=%s" % (e, os.getcwd()))
#    except Exception as e:
#        module.fail_json(msg=e.__str__())
  module.exit_json(status="success")


# this is magic, see lib/ansible/module_common.py
# <<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()
