#!/usr/bin/python

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


DOCUMENTATION = r'''
---
module: hive_drbd_release
short_description: Find a published DRBD RPM archive for the selected kernel
description:
  - Selects a non-prerelease archive from procube-open/drbd9-rpm-automated.
  - Requires an exact kernel release match, including EL version and architecture.
options:
  kernel:
    type: str
    required: true
'''


RELEASES_URL = 'https://api.github.com/repos/procube-open/drbd9-rpm-automated/releases'


def select_asset(releases, kernel):
  suffix = '-' + kernel + '.tar.gz'
  for release in sorted(releases, key=lambda entry: entry.get('published_at') or '', reverse=True):
    if release.get('draft') or release.get('prerelease'):
      continue
    for asset in release.get('assets', []):
      if asset['name'].startswith('drbd-') and asset['name'].endswith(suffix):
        result = {'download_url': asset['browser_download_url'],
                  'tag': release['tag_name'], 'asset': asset['name']}
        if (asset.get('digest') or '').startswith('sha256:'):
          result['checksum'] = asset['digest']
        return result
  return None


def find_release(kernel, fetch_page):
  page = 1
  while True:
    releases = fetch_page(page)
    match = select_asset(releases, kernel)
    if match:
      return match
    if len(releases) < 100:
      raise ValueError(
          f'No published DRBD RPM archive matches selected kernel {kernel}. '
          'Wait for a matching drbd9-rpm-automated release, or explicitly set '
          'hive_kernel_version and/or hive_drbd_download_url. '
          'RPMs for another kernel, EL version or architecture will not be used.')
    page += 1


def main():
  module = AnsibleModule(
      argument_spec={'kernel': {'type': 'str', 'required': True}},
      supports_check_mode=True)

  def fetch_page(page):
    response, info = fetch_url(
        module, f'{RELEASES_URL}?per_page=100&page={page}',
        headers={'Accept': 'application/vnd.github+json'}, timeout=30)
    if info['status'] != 200:
      raise ValueError(
          f'DRBD release lookup failed: GitHub HTTP {info["status"]}. '
          'Check connectivity and API rate limits, or set hive_drbd_download_url.')
    releases = json.loads(response.read())
    if not isinstance(releases, list):
      raise ValueError('Unexpected GitHub releases response')
    return releases

  try:
    result = find_release(module.params['kernel'], fetch_page)
  except (ValueError, KeyError) as error:
    module.fail_json(msg=str(error))
  module.exit_json(changed=False, **result)


if __name__ == '__main__':
  main()
