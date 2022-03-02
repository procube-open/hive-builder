#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 Procube Co., Ltd.

import docker
import logging
from logging import handlers
import json
import os
import argparse
from datetime import datetime
from time import time
import re
# logging.basicConfig(level=os.environ.get('HIVE_LOG_LEVEL', logging.INFO))
DAEMON = None
CACHE_FILE_DIR = '/var/lib/zabbix'


# python 3.6 does not support fromisoformat
def fromisoformat(str):
  # strptime does not support nano second
  return datetime.strptime(re.sub(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}).*$', r'\1', str), '%Y-%m-%dT%H:%M:%S.%f')


def service_uptime(client, logger, service_name):
  try:
    for service in client.services.list():
      logger.debug(f'traverse services in {service.name}')
      if service.name == service_name:
        logger.debug(f'found service: {service_name}')
        min = -1
        for task in service.tasks():
          logger.debug(task.get('DesiredState'))
          if task.get('DesiredState') == 'running':
            status = task.get('Status')
            if status.get('State') == 'running':
              logger.debug(f'found runinig task start_time={status.get("Timestamp")}')
              # s_uptime = int((datetime.now() - datetime.fromisoformat(status.get('Timestamp'))).total_seconds())
              s_uptime = int((datetime.utcnow() - fromisoformat(status.get('Timestamp'))).total_seconds())
              if min == -1 or s_uptime < min:
                min = s_uptime
        return min
    logger.error(f'service {service_name} is not found')
  except Exception as e:
    logger.exception(f'fail to get uptime for "{service_name}": {e}')
  return 0


def replicas(client, logger, service_name):
  try:
    for service in client.services.list():
      logger.debug(f'traverse services in {service.name}')
      if service.name == service_name:
        logger.debug(f'found service: {service_name}')
        desired_count = 0
        running_count = 0
        for task in service.tasks():
          if task.get('DesiredState') == 'running':
            desired_count += 1
            status = task.get('Status')
            if status.get('State') == 'running':
              running_count += 1
        return running_count * 100 / desired_count if desired_count > 0 else 0
    logger.error(f'service {service_name} is not found')
  except Exception as e:
    logger.exception(f'fail to get replicas for "{service_name}": {e}')
  return 0


def discover(client, logger, standalone=False):
  try:
    for service in client.services.list():
      logger.debug(f'found services : {service.name}')
      if (not standalone) or service.attrs.get('Spec', {}).get('Labels', {}).get('HIVE_STANDALONE', "False") == 'True':
        yield {'{#SERVICE_NAME}': service.name}
  except Exception as e:
    logger.exception(f'fail to get list of services: {e}')


def read_blacklist():
  try:
    with open('/etc/zabbix/service_discovery_blacklist') as f:
      return list(map(lambda x: re.compile(x.replace('\n', '')), f.readlines()))
  except FileNotFoundError:
    return []


def discover_innerservice(clients, logger, nDispose):
  blacklist = read_blacklist()
  cache = dict()
  cache_path = CACHE_FILE_DIR + '/discover_innerservice_cache.json'
  if os.path.exists(cache_path):
    with open(cache_path) as f:
      cache = json.load(f)
    cache_list = sorted(cache.items(), key=lambda x: x[1]['mtime'])
    # LRU: remove first nDispose items from cache
    del cache_list[:nDispose]
    cache = dict(cache_list)
  try:
    for service in next(iter(clients.values())).services.list():
      labels = service.attrs.get('Spec', {}).get('Labels', {})
      if labels.get('HIVE_STANDALONE', "False") == 'True':
        logger.debug(f'traverse inner services in standalone container : {service.name}')
        innerservices = set()
        if service.name in cache:
          logger.debug(f'cache hit for service : {service.name}')
          innerservices = set(cache[service.name]['services'])
        else:
          for task in service.tasks():
            if task.get('DesiredState') == 'running':
              status = task.get('Status')
              if status.get('State') == 'running':
                logger.debug(f'found runinig task on {task.get("NodeID")}')
                container_id = task.get('Status', {}).get('ContainerStatus', {}).get('ContainerID', '')
                if len(container_id) == 0:
                  logger.error(f'fail to get container ID for service "{service.name}" on node "{task.get("NodeID")}"')
                  return
                container = clients[task.get('NodeID')].containers.get(container_id)
                (rc, data) = container.exec_run(
                    'systemctl list-unit-files --type service --no-pager --no-legend',
                    user='root')
                decoded_data = ''
                try:
                  decoded_data = data.decode('utf-8')
                except Exception:
                  pass
                if rc != 0:
                  logger.error(f'fail to execute list-units on node "{task.get("NodeID")}": {decoded_data}')
                  return
                for l in decoded_data.splitlines():
                  sname = l.split()[0]
                  status = l.split()[1]
                  if status == 'enabled' and ('@' not in sname) and not any(map(lambda pattern: pattern.match(sname), blacklist)):
                    (rc, data) = container.exec_run(
                        'systemctl show -p Type ' + sname, user='root')
                    decoded_data = ''
                    try:
                      decoded_data = data.decode('utf-8')
                    except Exception:
                      pass
                    if rc != 0:
                      logger.error(f'fail to execute show -p Type {sname} in service "{service.name}" on node "{task.get("NodeID")}": {decoded_data}')
                      return
                    key_value = decoded_data.split('=')
                    logger.debug(f'type of innner service {sname} of service "{service.name}" on node "{task.get("NodeID")}" is "{key_value[1]}"')
                    if len(key_value) != 2 or key_value[0] != 'Type':
                      logger.error(f'fail to parse output "{decoded_data}" of command systemctl show -p Type {sname}' +
                                   f' in "{service.name}" on node "{task.get("NodeID")}"')
                      return -1
                    if key_value[1] not in ['oneshot', 'dbus'] and sname not in innerservices:
                      innerservices.add(sname)
          cache[service.name] = {'services': list(innerservices), 'mtime': time()}
        for sname in innerservices:
          yield {'{#SERVICE_NAME}': service.name, '{#INNER}': sname.replace('@', '%')}
  except Exception as e:
    logger.exception(f'fail to get inner se$rvices: {e}')
  with open(cache_path, 'w') as f:
    json.dump(cache, f, indent=2)


def service_uptime_innerservice(clients, logger, service_name, inner):
  try:
    sl = [s for s in next(iter(clients.values())).services.list(filters={'name': service_name}) if s.name == service_name]
    if len(sl) != 1:
      logger.error(f'fail to get service {service_name} count of service={len(sl)}')
      return -1
    min = -1
    uptime_table = {}
    for task in sl[0].tasks():
      if task.get('DesiredState') == 'running':
        status = task.get('Status')
        if status.get('State') == 'running':
          logger.debug(f'found runinig task on {task.get("NodeID")}')
          container_id = task.get('Status', {}).get('ContainerStatus', {}).get('ContainerID', '')
          if len(container_id) == 0:
            logger.error(f'fail to get container ID for service "{service_name}" on node "{task.get("NodeID")}"')
            return
          container = clients[task.get('NodeID')].containers.get(container_id)
          (rc, data) = container.exec_run('systemctl show -p ActiveEnterTimestampMonotonic ' + inner, user='root')
          decoded_data = ''
          try:
            decoded_data = data.decode('utf-8')
          except Exception:
            pass
          if rc != 0:
            logger.error(f'fail to get Timestamp of service "{inner}@{service_name}" on node "{task.get("NodeID")}": {decoded_data}')
            return -1
          key_value = decoded_data.split('=')
          if len(key_value) != 2:
            logger.error(f'fail to parse output "{decoded_data}" of command systemctl show -p ActiveEnterTimestampMonotonic {inner}' +
                         f' in "{service_name}" on node "{task.get("NodeID")}"')
            return -1
          server_uptime = uptime_table.get(task.get('NodeID'))
          if server_uptime is None:
            (rc, data) = container.exec_run('cat /proc/uptime', user='root')
            decoded_data = ''
            try:
              decoded_data = data.decode('utf-8')
            except Exception:
              pass
            if rc != 0:
              logger.error(f'fail to get uptime of server  "{task.get("NodeID")}": result of cat /proc/uptime is "{decoded_data}"')
              return -1
            server_uptime = float(decoded_data.split(' ')[0])
            uptime_table[task.get('NodeID')] = server_uptime
          s_uptime = int(server_uptime - (float(key_value[1]) / 1000000))
          if min == -1 or s_uptime < min:
            min = s_uptime
    return min
  except Exception as e:
    logger.exception(f'fail to get uptime for inner service "{inner}" in container "{service_name}": {e}')
  return -1


def failed_innerservice_count(clients, logger, service_name):
  blacklist = read_blacklist()
  try:
    sl = [s for s in next(iter(clients.values())).services.list(filters={'name': service_name}) if s.name == service_name]
    if len(sl) != 1:
      logger.error(f'fail to get service {service_name} count of service={len(sl)}')
      return -1
    failed_count = 0
    for task in sl[0].tasks():
      if task.get('DesiredState') == 'running':
        status = task.get('Status')
        if status.get('State') == 'running':
          logger.debug(f'found runinig task on {task.get("NodeID")}')
          container_id = task.get('Status', {}).get('ContainerStatus', {}).get('ContainerID', '')
          if len(container_id) == 0:
            logger.error(f'fail to get container ID for service "{service_name}" on node "{task.get("NodeID")}"')
            return
          container = clients[task.get('NodeID')].containers.get(container_id)
          (rc, data) = container.exec_run(
              'systemctl list-units --type=service --no-pager --no-legend --state=failed --all',
              user='root')
          decoded_data = ''
          try:
            decoded_data = data.decode('utf-8')
          except Exception:
            pass
          if rc != 0:
            logger.error(f'fail to execute list-units in service "{service_name}" on node "{task.get("NodeID")}: {decoded_data}"')
            return 99
          for l in decoded_data.splitlines():
            sname = l.split()[0]
            logger.debug(f'found failed service "{sname}" in service "{service_name}" on node "{task.get("NodeID")}"')
            if not any(map(lambda pattern: pattern.match(sname), blacklist)):
              failed_count += 1
    return failed_count
  except Exception as e:
    logger.exception(f'fail to get failed service count in container "{service_name}": {e}')
  return 99


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('servers', metavar='Server', nargs='+',
                      help='list of docker swarm node server')
  group = parser.add_mutually_exclusive_group()
  group.add_argument("--discover", help="discover services and print zabbix discover data format json.", action="store_true")
  group.add_argument("--discover-standalone", help="discover standalone type services and print zabbix discover data format json.", action="store_true")
  group.add_argument("--discover-innerservice",
                     help="discover inner-services in a standalone type container and print zabbix discover data format json.", action="store_true")
  group.add_argument("--uptime", help="print least uptime for the service.", metavar='service')
  group.add_argument("--replicas", help="print available running task persentage for the service.", metavar='service')
  parser.add_argument("--inner", help="name of inner service for standalone container.", metavar='inner')
  parser.add_argument("--dispose", help="number of cache entry refreleshed.", metavar='nDispose', type=int, default=0)
  group.add_argument("--failed-innerservice-count",
                     help="count number of failed serivces in standalone type container and print", metavar='service')
  args = parser.parse_args()
  logger = logging.getLogger('docker-service')
  logger.setLevel(os.environ.get('HIVE_LOG_LEVEL', logging.INFO))
  syslog_handler = handlers.SysLogHandler(address="/dev/log", facility=handlers.SysLogHandler.LOG_LOCAL2)
  logger.addHandler(syslog_handler)
  clients = {}
  dot_docker = os.environ['HOME'] + '/.docker'
  tls_config = docker.tls.TLSConfig(ca_cert=dot_docker + '/ca.pem', verify=dot_docker + '/ca.pem',
                                    client_cert=(dot_docker + '/cert.pem', dot_docker + '/key.pem'))
  for server in args.servers:
    try:
      client = docker.DockerClient(base_url=f'tcp://{server}:2376', tls=tls_config)
      info = client.info()
    except (docker.errors.APIError, docker.errors.DockerException) as e:
      logger.error(f'fail to initialize docker client for server {server}: {e}')
      continue
    node_id = info.get('Swarm', {}).get('NodeID', '')
    if len(node_id) > 0:
      clients[node_id] = client
    else:
      logger.error(f'fail to get node id for server {server}')

  if args.discover:
    print(json.dumps(dict(data=[v for v in discover(next(iter(clients.values())), logger)])))
  elif args.discover_standalone:
    print(json.dumps(dict(data=[v for v in discover(next(iter(clients.values())), logger, standalone=True)])))
  elif args.discover_innerservice:
    print(json.dumps(dict(data=[v for v in discover_innerservice(clients, logger, args.dispose)])))
  elif args.uptime:
    if args.inner:
      print(json.dumps(service_uptime_innerservice(clients, logger, args.uptime, args.inner.replace('%', '@'))))
    else:
      print(json.dumps(service_uptime(next(iter(clients.values())), logger, args.uptime)))
  elif args.replicas:
    print(json.dumps(replicas(next(iter(clients.values())), logger, args.replicas)))
  elif args.failed_innerservice_count:
    print(json.dumps(failed_innerservice_count(clients, logger, args.failed_innerservice_count)))
  else:
    logger.error('command option is required')


if __name__ == "__main__":
    main()
