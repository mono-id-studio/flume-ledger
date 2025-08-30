#!/bin/bash

# create file version.txt if not exists
if [ ! -f app/version.txt ]; then
    echo "0.0.0-1" > app/version.txt
fi

# read version from version.txt
VERSION=$(cat app/version.txt)

# increment build number
VERSION=$(echo $VERSION | awk -F- '{print $1"-"$2+1}')
echo $VERSION > app/version.txt