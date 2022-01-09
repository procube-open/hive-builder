resource {{ hive_safe_volume.name }} {
  options {
    quorum majority;
    on-no-quorum io-error;
  }
  disk {
    disk-flushes;
    md-flushes;
    c-plan-ahead 1;
    # on RHEL 8 on Azure cause error
    # kmod-drbd.x86_64  9.0.24_4.18.0_193.6.3.el8_2.x86_64-1
    # uname -r: 4.18.0-193.65.2.el8_2.x86_64
    #   drbd.d/pdnsadmin_data.res:10: Parse error: while parsing value ('0')
    #  for c-max-rate. Value is too small.
    # c-max-rate 0;
    # default = 102400 = 102MiB
    c-max-rate 1024000;
    c-delay-target 1;
    c-fill-target 1M;
    rs-discard-granularity 1048576;
    # following setting does not resolve stall problem
    # disk-timeout 100;
  }
{% for host in groups['hives'] | intersect(groups[hive_stage]) %}
  on {{ host }} {
    address   {{ hostvars[host].hive_private_ip }}:{{ 7000 + hive_safe_volume.drbd.device_id }};
    node-id   {{ loop.index0 }};
{% if (hive_safe_volume.drbd.diskless is not defined or host not in hive_safe_volume.drbd.diskless) and not (hostvars[host].hive_no_mirrored_device | default(False)) %}
    disk      /dev/{{ hive_safe_mirrored_disk_device.vgname }}/{{ hive_safe_volume.name }};
{% else %}
    disk      none;
{% endif %}
    device    minor {{ hive_safe_volume.drbd.device_id }};
    meta-disk internal;
  }
{% endfor %}
  connection-mesh {
    hosts {{ groups['hives'] | intersect(groups[hive_stage]) | join(' ') }};
    net {
        max-buffers    16000;
        max-epoch-size 16000;
        sndbuf-size 1048576;
        # following setting cause stall on connect?
        # tcp-cork no;
    }
  }
}