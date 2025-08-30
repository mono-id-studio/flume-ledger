#!/bin/bash

# read version from version.txt
VERSION=$(cat app/version.txt)

# increment major version
VERSION=$(echo $VERSION | awk -F. '{print $1+1"."0"."0}' | awk -F- '{print $1"-"0}')
echo $VERSION > app/version.txt