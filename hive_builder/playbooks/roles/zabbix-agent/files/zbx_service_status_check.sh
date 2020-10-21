#!/bin/bash

service="${1/\%/@}"
systemctl is-active -q $service
echo $?