
#!/bin/bash

# read version from version.txt
VERSION=$(cat app/version.txt)

# increment minor version
VERSION_PRE_MINUS=$(echo $VERSION | awk -F- '{print $1}')
VERSION_POST_MINUS=$(echo $VERSION | awk -F- '{print $2}')
VERSION_PRE_MINUS=$(echo $VERSION_PRE_MINUS | awk -F. '{print $1"."$2"."$3+1}')

echo $VERSION_PRE_MINUS"-"$VERSION_POST_MINUS > app/version.txt