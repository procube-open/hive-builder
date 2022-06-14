#!/bin/sh
# this script copy from following page
# https://www.ikemo3.com/inverted/vagrant/extend-partion-on-centos7/
#  Thanks to Hideki Ikemoto
# TODO: support disk_size on virtualbox provider

yum install -y e2fsprogs

TARGET_DISK=$(lsblk --list | awk '$7=="/" {print "/dev/" substr($1,1, length($1)-1)}')
if [ -z "$TARGET_DISK" ]; then
  echo "ERROR: / partition is not found(device)." 1>&2
  exit 1
fi

TARGET_PART=$(lsblk --list | awk '$7=="/" {print substr($1,length($1),1)}')
if [ -z "$TARGET_PART" ]; then
  echo "ERROR: / partition is not found(partision)." 1>&2
  exit 1
fi

## resize disk
sed -e 's/\s*\([\+0-9a-zA-Z]*\).*/\1/' << EOF | fdisk $TARGET_DISK || true
d  # delete partition
${TARGET_PART} # ignore error "1: unknown command" when there is only one partition in the device.
n  # add a new partition
p  # primary
${TARGET_PART} # Partition number
   # First sector(default)
   # Last sector(default)
w  # write table to disk and exit
EOF

partprobe

## resize partition(CentOS 7, ext4)
#resize2fs /dev/vda1

## resize partition(CentOS 7, xfs)
xfs_growfs /
