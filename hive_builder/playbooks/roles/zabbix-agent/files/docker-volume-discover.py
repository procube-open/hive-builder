#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 Procube Co., Ltd.

import docker
import logging
from logging import handlers
import json
import os

# logging.basicConfig(level=os.environ.get('HIVE_LOG_LEVEL', logging.INFO))
DAEMON = None


def volumes(client, logger):
  try:
    for service in client.services.list():
      logger.debug(f'traverse volumes in {service.name}')
      for volume in service.attrs.get('Spec', {}).get('TaskTemplate', {}).get('ContainerSpec', {}).get('Mounts', []):
        if volume.get('Type') == 'volume':
          logger.debug(f'found volume: {json.dumps(volume)}')
          yield {'{#SERVICE_NAME}': service.name, '{#NAME}': volume.get('Source'), '{#PATH}': volume.get('Target')}
  except Exception as e:
    logger.exception(f'fail to get services', e)


def main():
  logger = logging.getLogger('docker-volume-discover')
  logger.setLevel(os.environ.get('HIVE_LOG_LEVEL', logging.INFO))
  syslog_handler = handlers.SysLogHandler(address="/dev/log", facility=handlers.SysLogHandler.LOG_LOCAL1)
  logger.addHandler(syslog_handler)
  try:
    client = docker.from_env()
    print(json.dumps(dict(data=[v for v in volumes(client, logger)])))
  except docker.errors.APIError as e:
    logger.exception(f'fail to initialize docker client: {e}')


if __name__ == "__main__":
    main()
