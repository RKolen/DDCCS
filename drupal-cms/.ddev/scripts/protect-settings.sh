#!/usr/bin/env bash
#
# Re-apply read-only permissions to Drupal's settings and services files.
#
# DDEV's settings management makes settings.php and services.yml writable
# every time it regenerates settings.ddev.php on start. Drupal's status
# report flags writable settings files as a security risk ("Protection
# disabled"), so this hook restores 0444 after DDEV is done with them.
#
# Run automatically from the post-start hook in .ddev/config.yaml.

set -euo pipefail

SITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../web/sites/default" && pwd)"

for file in settings.php services.yml settings.local.php; do
  if [ -f "${SITE_DIR}/${file}" ]; then
    chmod 444 "${SITE_DIR}/${file}"
  fi
done
