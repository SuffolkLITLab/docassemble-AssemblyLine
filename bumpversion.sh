#/bin/bash

set -e

# First arg: test, patch, minor, or major

if [ "$1" = "minor" -o "$1" = "major" ] 
then
  # ask for editor text
  # echo "" > /tmp/release_text
  #"$EDITOR" /tmp/release_text
  echo What has changed about this "$1" version?
  read release_update
  new_version=`bumpversion --config-file .bumpscript/.bumpversion.cfg $1 --list | grep new_version | cut -d= -f 2 ` 
  echo -e "# Version v$new_version\n\n$release_update\n\n`cat CHANGELOG.md`" > CHANGELOG.md
  git add CHANGELOG.md && git commit --amend -C HEAD
else
  new_version=`bumpversion --config-file .bumpscript/.bumpversion.cfg $1 --list | grep new_version | cut -d= -f 2`
fi
git push 
git push --tags
sed -e s/{{version}}/$new_version/g .bumpscript/version_teams_msg.json > /tmp/teams_msg_to_send.json
curl -H "Content-Type:application/json" -d "@/tmp/teams_msg_to_send.json" $teams_bump_webhook
rm "/tmp/teams_msg_to_send.json"

