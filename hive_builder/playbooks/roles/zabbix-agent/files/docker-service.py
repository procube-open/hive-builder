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
import re
import uptime
# logging.basicConfig(level=os.environ.get('HIVE_LOG_LEVEL', logging.INFO))
DAEMON = None


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
    logger.exception(f'fail to get services', e)


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
    logger.exception(f'fail to get services', e.message)


def discover(client, logger):
  try:
    for service in client.services.list():
      logger.debug(f'found services : {service.name}')
      yield {'{#SERVICE_NAME}': service.name}
  except Exception as e:
    logger.exception(f'fail to get services', e)


def read_blacklist():
  try:
    with open('/etc/zabbix/service_discovery_blacklist') as f:
      return f.readlines()
  except FileNotFoundError:
    return []


def discover_innerservice(clients, logger):
  blacklist = read_blacklist()
  try:
    for service in next(iter(clients.values())).services.list():
      labels = service.attrs.get('Spec', {}).get('Labels', {})
      if labels.get('HIVE_STANDALONE', "False") == 'True':
        logger.debug(f'traverse inner services in standalone container : {service.name}')
        innerservices = set()
        for task in service.tasks():
          if task.get('DesiredState') == 'running':
            status = task.get('Status')
            if status.get('State') == 'running':
              logger.debug(f'found runinig task on {task.get("NodeID")}')
              container_id = task.get('Status', {}).get('ContainerStatus', {}).get('ContainerID', '')
              if len(container_id) == 0:
                logger.error(f'fail to get container ID for service "{service}" on node "{task.get("NodeID")}"')
                return
              container = clients[task.get('NodeID')].containers.get(container_id)
              (rc, data) = container.exec_run('systemctl list-units --type=service --no-legend --no-pager', user='root')
              if rc != 0:
                logger.error(f'fail to execute list-units on node "{task.get("NodeID")}"')
                return
              for l in data.decode('utf-8').splitlines():
                sname = l.split()[0]
                if sname not in blacklist and sname not in innerservices:
                  innerservices.add(sname)
        for sname in innerservices:
          yield {'{#SERVICE_NAME}': service.name, '{#INNER}': sname.replace('@', '%')}
  except Exception as e:
    logger.exception(f'fail to get services', e)


def service_uptime_innerservice(clients, logger, service_name, inner):
  try:
    sl = next(iter(clients.values())).services.list(filters={'name': service_name})
    if len(sl) != 1:
      logger.error(f'fail to get service {service_name} count of service={len(sl)}')
      return
    min = -1
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
          if rc != 0:
            logger.error(f'fail to execute list-units on node "{task.get("NodeID")}"')
            return -1
          key_value = data.decode('utf-8').split('=')
          if len(key_value) != 2:
            logger.error(f'fail to parse output "{data.decode("utf-8")}" of command systemctl show -p ActiveEnterTimestampMonotonic {inner}')
            return -1
          s_uptime = int(uptime.uptime() - (float(key_value[1]) / 1000000))
          if min == -1 or s_uptime < min:
            min = s_uptime
    return min
  except Exception as e:
    logger.exception(f'fail to get uptime for inner service "{inner}" in container "{service_name}": ', e)


def replicas_innerservice(clients, logger, service_name, inner):
  try:
    sl = next(iter(clients.values())).services.list(filters={'name': service_name})
    if len(sl) != 1:
      logger.error(f'fail to get service {service_name} count of service={len(sl)}')
      return
    desired_count = 0
    running_count = 0
    for task in sl[0].tasks():
      if task.get('DesiredState') == 'running':
        desired_count += 1
        status = task.get('Status')
        if status.get('State') == 'running':
          logger.debug(f'found runinig task on {task.get("NodeID")}')
          container_id = task.get('Status', {}).get('ContainerStatus', {}).get('ContainerID', '')
          if len(container_id) == 0:
            logger.error(f'fail to get container ID for service "{service_name}" on node "{task.get("NodeID")}"')
            return
          container = clients[task.get('NodeID')].containers.get(container_id)
          (rc, data) = container.exec_run('systemctl is-active ' + inner, user='root')
          if rc == 0:
            running_count += 1
    return running_count * 100 / desired_count if desired_count > 0 else 0
  except Exception as e:
    logger.exception(f'fail to get replicas for inner service "{inner}" in container "{service_name}": ', e)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('servers', metavar='Server', nargs='+',
                      help='list of docker swarm node server')
  group = parser.add_mutually_exclusive_group()
  group.add_argument("--discover", help="discover services and print zabbix discover data format json.", action="store_true")
  group.add_argument("--discover-innerservice",
                     help="discover inner-services in a standalone type container and print zabbix discover data format json.", action="store_true")
  group.add_argument("--uptime", help="print least uptime for the service.", metavar='service')
  group.add_argument("--replicas", help="print available running task persentage for the service.", metavar='service')
  parser.add_argument("--inner", help="name of inner service for standalone container.", metavar='inner')
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
    except docker.errors.APIError as e:
      logger.error(f'fail to initialize docker client for server {server}: {e}')
      continue
    node_id = info.get('Swarm', {}).get('NodeID', '')
    if len(node_id) > 0:
      clients[node_id] = client
    else:
      logger.error(f'fail to get node id for server {server}')

  if args.discover:
    print(json.dumps(dict(data=[v for v in discover(next(iter(clients.values())), logger)])))
  elif args.discover_innerservice:
    print(json.dumps(dict(data=[v for v in discover_innerservice(clients, logger)])))
  elif args.uptime:
    if args.inner:
      print(json.dumps(service_uptime_innerservice(clients, logger, args.uptime, args.inner.replace('%', '@'))))
    else:
      print(json.dumps(service_uptime(next(iter(clients.values())), logger, args.uptime)))
  elif args.replicas:
    if args.inner:
      print(json.dumps(replicas_innerservice(clients, logger, args.replicas, args.inner.replace('%', '@'))))
    else:
      print(json.dumps(replicas(next(iter(clients.values())), logger, args.replicas)))
  else:
    logger.exception('command option is required')


if __name__ == "__main__":
    main()
