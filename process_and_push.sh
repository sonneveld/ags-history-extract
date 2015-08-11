#!/bin/bash

set -e

rm -rf extracted-*

./process.py

pushd extracted-templates
git remote add origin git@github.com:sonneveld/ags-templates.git
git push origin master -f
popd

pushd extracted-demo
git remote add origin git@github.com:sonneveld/ags-demo-quest.git
git push origin master -f
popd
