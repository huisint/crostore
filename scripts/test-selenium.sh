#! /usr/bin/env bash

set -euC
set -o pipefail

bash scripts/test.sh --selenium="$SELENIUM_URL" ${@}
