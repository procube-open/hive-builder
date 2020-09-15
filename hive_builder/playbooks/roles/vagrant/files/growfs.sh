#!/bin/sh
# this script copy from following page
# https://www.ikemo3.com/inverted/vagrant/extend-partion-on-centos7/
#  Thanks to Hideki Ikemoto
# TODO: support disk_size on virtualbox provider

yum install -y e2fsprogs

if [ -b /dev/sda ]; then
  TARGET_DISK=/dev/sda
elif [ -b /dev/vda ]; then
  TARGET_DISK=/dev/vda
else
  echo "ERROR: neather /dev/sda or /dev/vda is not exists." 1>&2
  exit 1
fi

## resize disk
sed -e 's/\s*\([\+0-9a-zA-Z]*\).*/\1/' << EOF | fdisk $TARGET_DISK || true
d  # delete partition
n  # add a new partition
p  # primary
1  # Partition number: 1
   # First sector(default)
   # Last sector(default)
w  # write table to disk and exit
EOF

partprobe

## resize partition(CentOS 7, ext4)
#resize2fs /dev/vda1

## resize partition(CentOS 7, xfs)
xfs_growfs /
