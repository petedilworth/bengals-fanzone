#!/usr/bin/env bash
# Copies the site and its data into _site/ for local preview and GitHub Pages.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf _site
mkdir -p _site
cp -r site/. _site/
cp -r data _site/data
touch _site/.nojekyll
echo "Built _site/"
