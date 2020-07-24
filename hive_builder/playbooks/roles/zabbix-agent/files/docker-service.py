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
# logging.basicConfig(level=os.environ.get('HIVE_LOG_LEVEL', logging.INFO))
DAEMON = None


# python 3.6 does not support fromisoformat
def fromisoformat(str):
  # strptime does not support nano second
  return datetime.strptime(re.sub(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}).*$', r'\1', str), '%Y-%m-%dT%H:%M:%S.%f')


def uptime(client, logger, service_name):
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
              # uptime = int((datetime.now() - datetime.fromisoformat(status.get('Timestamp'))).total_seconds())
              uptime = int((datetime.utcnow() - fromisoformat(status.get('Timestamp'))).total_seconds())
              if min == -1 or uptime < min:
                min = uptime
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
      logger.debug(f'traverse services in {service.name}')
      yield {'{#SERVICE_NAME}': service.name}
  except Exception as e:
    logger.exception(f'fail to get services', e)


def main():
  parser = argparse.ArgumentParser()
  group = parser.add_mutually_exclusive_group()
  group.add_argument("--discover", help="discover services and print zabbix discover data format json.", action="store_true")
  group.add_argument("--uptime", help="print least uptime for the service.", metavar='service')
  group.add_argument("--replicas", help="print available running task persentage for the service.", metavar='service')
  args = parser.parse_args()
  logger = logging.getLogger('docker-service')
  logger.setLevel(os.environ.get('HIVE_LOG_LEVEL', logging.INFO))
  syslog_handler = handlers.SysLogHandler(address="/dev/log", facility=handlers.SysLogHandler.LOG_LOCAL1)
  logger.addHandler(syslog_handler)
  try:
    client = docker.from_env()
    if args.discover:
      print(json.dumps(dict(data=[v for v in discover(client, logger)])))
    elif args.uptime:
      print(json.dumps(uptime(client, logger, args.uptime)))
    elif args.replicas:
      print(json.dumps(replicas(client, logger, args.replicas)))
    else:
      logger.exception('command option is required')
  except docker.errors.APIError as e:
    logger.exception(f'fail to initialize docker client: {e}')


if __name__ == "__main__":
    main()
