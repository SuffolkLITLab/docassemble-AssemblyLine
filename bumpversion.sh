#!/bin/bash

helpvar="Setup:
Copy the example env file at '.env.example' to '.env', and fill the values of your own variables
* TEAMS_BUMP_WEBHOOK: a url that you setup following the procudure at https://stackoverflow.com/a/65759554
* TWINE_USERNAME: your Pypi username, or '__token__' if you are using an API token
* TWINE_PASSWORD: your Pypi password, or an API token, including the 'pypi-' prefix

How to run:

$ (source .env && ./bumpversion.sh patch)

Can pass in test, patch, minor, or major depending on which part of the version you're bumping. We
roughly follow semantic versioning:
* test is a nonstandard version increment. Since you have to install Docassemble packages to test 
  if they work in other packages, you should bump test before installing to see what works
* patch is a version that changes nothing about how other interviews use your package/library.
  Usually just bug fixes.
* minor is the addition of a feature, and generally means that you cannot downgrade after upgrading
* major is a breaking change, either internally or externally
For more info about semantic versioning (aka semver), see https://semver.org/
"

real_run=true
announce_to_teams=true
publish_to_pypi=true

while [ -n "$1" ]; do
  case "$1" in
  -h | --help)
    echo -n "$helpvar"
    shift
    exit
    ;;
  -n | --dry-run)
    real_run=false
    shift
    ;;
  --disable-teams)
    announce_to_teams=false
    shift
    ;;
  --disable-pypi)
    publish_to_pypi=false
    shift
    ;;
  --)
    shift # double dash makes for parameters
    break
    ;;
  major | minor | patch | test)
    bump_type=$1
    shift
    ;;
  *)
    break # found not an option: just continue
    ;;
  esac
done


echo "$announce_to_teams"
echo "$publish_to_pypi"
echo "$bump_type"

### Make sure you have all the necessary commands installed and env vars set
if ! git --help > /dev/null 2>&1; then
  echo "You must have the git command installed"
  exit 1
fi

if ! bumpversion --help > /dev/null 2>&1; then
  echo "You need to install the bumpversion python library"
  exit 1
fi

if ! twine --help > /dev/null 2>&1; then
  echo "You need to install the twine python library to publish to pypi"
  exit 1
fi

if [ -z "$bump_type" ]; then
  echo -n "You need to pass in test, patch, minor, or major: $helpvar"
  exit 1
fi

if "$publish_to_pypi" && [ -z "$TWINE_USERNAME" ]; then
  echo "You need to have the TWINE_USERNAME environment variable defined"
  exit 1
fi

if "$publish_to_pypi" && [ -z "$TWINE_PASSWORD" ]; then
  echo "You need to have the TWINE_PASSWORD environment variable defined"
  exit 1
fi

if "$announce_to_teams" && [ -z "$TEAMS_BUMP_WEBHOOK" ]; then
  echo "You need to have the TEAMS_BUMP_WEBHOOK environment variable defined"
  exit 1
fi

# Set after, because we can't iterate through things without getting to the end
set -euo pipefail

# TODO(brycew): should we restrict this to only work on default branches?
git fetch --all
branch=$(git rev-parse --abbrev-ref HEAD)
if [ -n "$(git ls-remote --exit-code --heads origin "$branch")" ] && \
   [ x"$(git merge-base "$branch" origin/"$branch")" != x"$(git rev-parse origin/"$branch")" ]
then
  echo "$branch is behind the origin. Pull from origin first."
  exit 1
fi

### Makes git commit and tag
if $real_run
then
  new_version=$(bumpversion --list --config-file .bumpversion.cfg "$bump_type" | grep new_version | cut -d= -f 2)
else
  new_version=$(bumpversion --list --dry-run --verbose --config-file .bumpversion.cfg "$bump_type" | grep new_version | cut -d= -f 2)
fi

if [ "$bump_type" = "patch" ] || [ "$bump_type" = "minor" ] || [ "$bump_type" = "major" ] 
then
  echo What has changed about this "$bump_type" version? Press ctrl-d to finish, ctrl-c to cancel
  release_update=$(</dev/stdin)
  if $real_run
  then
    echo -e "# Version v$new_version\n\n$release_update\n\n$(cat CHANGELOG.md)" > CHANGELOG.md
    git add CHANGELOG.md && git commit --amend -C HEAD
  fi
fi

### Make and update Pypi package
rm -rf build dist ./*.egg-info
python3 setup.py sdist

### Auto get project and repo name to put in Teams message
remote_url=$(git remote get-url --push origin ) 
repo_name=$(basename -s ".git" "$remote_url")
org_name=$(basename "$(dirname "$remote_url")")
if [[ "$org_name" = *@* ]]; then
  # Likely an SSH URL. Split at the ':'
  org_name=$(echo "$org_name" | cut -d ':' -f2)
fi
project_name=$(echo "$repo_name" | cut -d - -f2)

# This JSON was built using: https://messagecardplayground.azurewebsites.net/, 
# and https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference
link_ver=${new_version//["."]}
sed -e "s/{{version}}/$new_version/g; s/{{link_version}}/$link_ver/g; s/{{project_name}}/$project_name/g; s/{{org_name}}/$org_name/g; s/{{repo_name}}/$repo_name/g;" << EOF > /tmp/teams_msg_to_send.json
{
	"@type": "MessageCard",
	"@context": "https://schema.org/extensions",
	"summary": "{{project_name}} Version released",
	"themeColor": "0078D7",
	"title": "{{project_name}} Version {{version}} released", 
	"sections": [
		{
			"activityTitle": "Version {{version}}",
			"activityImage": "https://avatars.githubusercontent.com/u/33028765?s=200&v=4", 
			"facts": [
				{
					"name": "Repository:",
					"value": "{{org_name}}/{{repo_name}}"
				},
				{
					"name": "Tag",
					"value": "v{{version}}"
				}
			],
			"text": "" 
		}
	],
	"potentialAction": [
        {
            "@type": "OpenUri",
            "name": "See Changelog",
            "targets": [
                {
                    "os": "default",
                    "uri": "https://github.com/{{org_name}}/{{repo_name}}/blob/main/CHANGELOG.md#version-v{{link_version}}"
                }
            ]
        },
		{
			"@type": "OpenUri",
			"name": "View in GitHub",
			"targets": [
				{
					"os": "default",
					"uri": "http://github.com/{{org_name}}/{{repo_name}}/releases/tag/v{{version}}"
				}
			]
		}
	]
}
EOF

if $real_run
then
  ## Push and save stuff at the very end of the script
  git push
  git push --tags
  # Only push to pypi and announce on non-test bumps
  if [ ! "$bump_type" = "test" ]
  then
    if "$publish_to_pypi"
    then
      # Needs TWINE_USERNAME and TWINE_PASSWORD
      twine upload --repository 'pypi' dist/* --non-interactive
    fi
    if "$announce_to_teams"
    then
      curl -H "Content-Type:application/json" -d "@/tmp/teams_msg_to_send.json" "$TEAMS_BUMP_WEBHOOK"
    fi
  fi
  rm -rf build dist ./*.egg-info

else
  if [ "$bump_type" = "minor" ] || [ "$bump_type" = "major" ] 
  then
    echo "Changelog would be:"
    echo -e "# v$new_version\n\n$release_update\n\n$(cat CHANGELOG.md)"
  fi

  if [ ! "$bump_type" = "test" ]
  then
    if "$publish_to_pypi"
    then
      echo "Would push to Pypi"
    else
      echo "Would NOT push to Pypi"
    fi
    if "$announce_to_teams"
    then
      echo "Teams message JSON is: $(cat /tmp/teams_msg_to_send.json)"
    else
      echo "Would NOT announce to teams"
    fi
  else
    echo "Would NOT push to Pypi or announce to Teams"
  fi

fi
rm "/tmp/teams_msg_to_send.json"

