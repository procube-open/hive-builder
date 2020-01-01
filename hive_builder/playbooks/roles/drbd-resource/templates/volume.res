resource {{ hive_safe_volume.name }} {
  options {
    quorum majority;
    on-no-quorum io-error;
  }
{% for host in groups['hives'] | intersect(groups[hive_stage]) %}
  on {{ host }} {
    address   {{ hostvars[host].hive_private_ip }}:{{ 7788 + hive_safe_volume.drbd.device_id }};
    node-id   {{ loop.index0 }};
{% if (hive_safe_volume.drbd.diskless is not defined or host not in hive_safe_volume.drbd.diskless) and not (hostvars[host].hive_no_mirrored_device | default(False)) %}
    disk      /dev/drbdvg/{{ hive_safe_volume.name }};
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
        use-rle no;
    }
  }
}