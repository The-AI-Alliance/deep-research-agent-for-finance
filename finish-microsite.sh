#!/usr/bin/env zsh
#------------------------------------------------------------------------
# Convert this microsite template into your desired microsite.
# Run finish-microsite.sh -h to see the required arguments and options.
# Note: This file defaults to use zsh. If you don't have zsh, but you
# DO have bash v5+, then use /path/to/bash finish-microsite.sh.
#------------------------------------------------------------------------

ymdformat="%Y-%m-%d"
tsformat="$ymdformat %H:%M %z"
script=$0
dir=$(dirname $script)
cfg="$dir/docs/_config.yml"
index="$dir/docs/index.markdown"
work_branch=main
publish_branch=main
fa_max_number=6  # FAs numbered from 1 to max_...
focus_areas_url="https://thealliance.ai/focus-areas"

declare -A fa_names
fa_names[FA1]="Skills and Education"
fa_names[FA2]="Trust and Safety"
fa_names[FA3]="Applications and Tools"
fa_names[FA4]="Hardware Enablement"
fa_names[FA5]="Foundation Models and Datasets"
fa_names[FA6]="Advocacy"

declare -A fa_url_names
fa_url_names[FA1]=skills-education
fa_url_names[FA2]=trust-and-safety
fa_url_names[FA3]=applications-and-tools
fa_url_names[FA4]=hardware-enablement
fa_url_names[FA5]=foundation-models
fa_url_names[FA6]=advocacy

dashboard_base="The-AI-Alliance"
declare -A fa_dashboard_numbers
fa_dashboard_numbers[FA1]=
fa_dashboard_numbers[FA2]=23
fa_dashboard_numbers[FA3]=34
fa_dashboard_numbers[FA4]=
fa_dashboard_numbers[FA5]=28
fa_dashboard_numbers[FA6]=

declare -A fa_assignees
fa_assignees[FA1]=
fa_assignees[FA2]="deanwampler,bnayahu"
fa_assignees[FA3]="adampingel,rawkintrevo"
fa_assignees[FA4]="deanwampler"
fa_assignees[FA5]="deanwampler,hughesthe1st,jolson-ibm"
fa_assignees[FA6]="pasanth"

help() {
	cat << EOF
$script [options] \
  -t|--site-title|--microsite-title title \
  -w|--work-group work_group

These arguments are required, but they can appear in any order, intermixed
with optional arguments (discussed below). See the example below:

-t | --site-title | --microsite-title title
                       The title of the microsite.
-w | --work-group work_group
                       The name of work group sponsoring this site.

These arguments are optional:
-h | --help            Print this message and exit.
-n | --noop            Just print the commands but don't run them.
-s | --next-steps      At the end of running this script to create a new repo,
                       some information about "next steps" is printed. If you want to see
                       this information again, run this script again just using this flag.
-r | --repo-name name  The name of GitHub repo. If you are running this script in the
                       repo's root directory, its name will be used, by default.
--work-group-url | -u work_group_url
                       The URL of the work group sponsoring this site.
                       If one of the "FA#" or "#" arguments is used for --work-group (see below),
                       then a known URL will be used. If the URL isn't known for the
                       specified workgroup and one isn't specified, the default URL for
                       focus areas will be used: $focus_areas_url
--repo-dir dir         The absolute path to the repo root directory or the relative
                       path from the current directory. Only needed when you aren't
                       running this script in the repo root directory.
-d | --dashboard N     The "N" for the ${dashboard_base}/N link
                       to use for the project's dashboard. Projects in FA2, FA3, and FA5 have
                       default values. If not provided and there is no default, so no dashboard
                       will be associated with the project automatically.
                       (At this time, this is only used in the ".github/*TEMPLATE" files.)
-a | --assignees list  Comma-separated list of GitHub user names to whom issues are assigned.
                       E.g., "--assignees bob,ted". Default: Each FA has a default list.
--use-latest           By default, this script previously assumed that you would publish
                       the website from the "latest" branch, while using "main" for integration.
                       This is difficult for less-technical users. Now the default is to use 
                       "main", but if you prefer to use "latest" as the publish branch, use
                       this option. See also "--publish-branch BR".
--publish-branch BR    Instead of publishing from "main" (or "latest"; see "--use-latest"),
                       set up "BR" as the branch used for publishing the website.
--no-push              Normally, all edits are pushed upstream to the GitHub repo. Use this option
                       skip that step, for example if your plan to make additional edits first or
                       when debugging this script!! ;)

For example, suppose you want to create a microsite with the title "AI for Evil Project",
under the Trust and Safety work group, then use one of the following commands:

$script --repo-name ai-for-evil-project --microsite-title "AI for Evil Project" --work-group fa2
$script --repo-name ai-for-evil-project --microsite-title "AI for Evil Project" --work-group 2

Note that just specifying "2", "fa2" or "FA2", etc. for any of the focus areas will result in the
following names being used:

EOF

for i in {1..$fa_max_number}
do
	# By "coincidence" it works to use the $focus_areas_url as a prefix!
	printf "%d or FA%d -> %-30s (URL: %s)\n" $i $i "${fa_names[FA$i]}" "${focus_areas_url}/${fa_url_names[FA$i]}"
done

	cat <<EOF

NOTE: The title and work group strings need to be quoted if they contain spaces!
EOF
}

repo_name=

next_steps() {
	cat << EOF

Next Steps:

Return to the README-template for any additional instructions to follow:

  local:  README-template.md
  GitHub: https://github.com/The-AI-Alliance/$repo_name/blob/main/README-template.md

Don't forgot to commit and push any subsequent changes upstream, e.g., "git push --all".
You also need to do this if you used the "--no-push" option.

To see these instructions again, run the following command:

  $script --next-steps
EOF
}

error() {
	for arg in "$@"
	do
		echo "ERROR ($script): $arg"
	done
	echo "ERROR: Try: $script --help"
	exit 1
}

warn() {
	for arg in "$@"
	do
		echo "WARN  ($script): $arg"
	done
}

info() {
	for arg in "$@"
	do
		echo "INFO  ($script): $arg"
	done
}

repo_dir=
work_group_url=
dashboard=
assignees=
do_push=true
show_next_steps=false
while [[ $# -gt 0 ]]
do
	case $1 in
		-h|--h*)
			help
			exit 0
			;;
		-n|--noop)
			NOOP=echo
			;;
		-s|--next-steps)
			show_next_steps=true
			;;
		-r|--repo-name)
			shift
			repo_name="$1"
			;;
		--repo-dir)
			shift
			repo_dir="$1"
			;;
		-t|--site-title|--microsite-title)
			shift
			microsite_title="$1"
			;;
		-w|--work-group)
			shift
			n=$(echo $1 | sed -e 's/fa//i')
			if [[ $n -ge 1 ]] && [[ $n -le $fa_max_number ]]
			then
				# User input valid faN, FAN, fAN, FaN, or N within range.
				dashboard_number=${fa_dashboard_numbers[FA$n]}
				[[ -n $dashboard_number ]] && dashboard=${dashboard_base}/${fa_dashboard_numbers[FA$n]}
				assignees=${fa_assignees[FA$n]}
				work_group=${fa_names[FA$n]}
				[[ -n $work_group_url ]] || work_group_url="${focus_areas_url}/${fa_url_names[FA$n]}"
			elif [[ $n -lt 1 ]] || [[ $n -gt $fa_max_number ]]
			then
				# User input an invalid faN, FAN, fAN, FaN, or N, because the N is outside the range.
				error "Unknown focus area specified: $1. Must be 1 to $fa_max_number or FA1 to FA$fa_max_number"
			else
				work_group="$1"
				[[ -n $work_group_url ]] || work_group_url=$focus_areas_url
			fi
			;;
		-u|--work-group-url)
			shift
			work_group_url=$1
			;;
		-d|--dashboard)
			shift
			n=$1
			if [[ $n -ge 1 ]]
			then
				# User input valid number
				dashboard=${dashboard_base}/$n
			else
				# User input a full URL (hopefully!)
				dashboard="$n"
			fi
			;;
		-a|--assignees)
			shift
			assignees="$1"
			;;
		--use-latest)
			publish_branch="latest"
			;;
		--publish-branch)
			shift
			publish_branch="$1"
			;;
		-a|--assignees)
			shift
			assignees="$1"
			;;
		--no-push)
			do_push=false
			;;
		*)
			error "Unrecognized argument: $1"
			;;
	esac
	shift
done

[[ -z "$repo_name" ]] && repo_name=$(basename $PWD)

$show_next_steps && next_steps && exit 0

missing=()
[[ -z "$microsite_title" ]] && missing+=("The microsite title is required. ")
[[ -z "$work_group" ]] && missing+=("The work group name is required. ")
[[ ${#missing[@]} > 0 ]] && error "${missing[@]}"

info "Updating data in the repo:"
info "  Repo name:              $repo_name"
[[ -n "$repo_dir" ]] && \
  info "  Repo dir:               $repo_dir"
info "  Title:                  $microsite_title"
info "  Work group:             $work_group"
[[ -n "$work_group_url" ]] && \
  info "  Work group URL:         $work_group_url"
info "  GitHub:"
[[ -n "$dashboard" ]] && \
  info "    Dashboard:            $dashboard"
[[ -n "$assignees" ]] && \
  info "    Issue assignees:      $assignees"
info "    Work branch:          $work_branch"
info "    Publishing branch:    $publish_branch"
info "    Pushing changes to GitHub? $do_push"

info "Replacing macro placeholders with values:"
[[ -z "$ymdtimestamp" ]] && ymdtimestamp=$(date +"$ymdformat")
date -j -f "$ymdformat" +"$ymdformat" "$ymdtimestamp" > /dev/null 2>&1
[[ $? -ne 0 ]] && error "Invalid YMD timestamp format for timestamp: $ymdtimestamp" "Required format: $ymdformat"
[[ -z "$timestamp" ]] && timestamp=$(date +"$tsformat")
date -j -f "$tsformat" +"$tsformat" "$timestamp" > /dev/null 2>&1
[[ $? -ne 0 ]] && error "Invalid timestamp format for timestamp: $timestamp" "Required format: $tsformat"

[[ -n "$repo_dir" ]] && $NOOP cd "$repo_dir"

other_files=(
	Makefile
	*.sh
	docs/_config.yml
)
markdown_files=($(find docs -name '*.markdown') $(find . -name '*.md'))
html_files=($(find docs/_layouts docs/_includes -name '*.html'))
github_files=($(find .github \( -name '*.yaml' -o -name '*.md' \)))

info "Replacing macros with correct values:"
info "  REPO_NAME:       $repo_name"
info "  MICROSITE_TITLE: $microsite_title"
info "  WORK_GROUP_NAME: $work_group"
info "  WORK_GROUP_URL:  $work_group_url"
info "  DASHBOARD:       $dashboard"
info "  ASSIGNEES:       $assignees"
info "  YMD_TSTAMP:      $ymdtimestamp"
info "  TIMESTAMP:       $timestamp"
info
info "Processing Files:"

for file in "${other_files[@]}" "${markdown_files[@]}" "${html_files[@]}" "${github_files[@]}"
do
	info "  $file"
	if [[ -z $NOOP ]]
	then
		sed -e "s?REPO_NAME?$repo_name?g" \
		    -e "s?MICROSITE_TITLE?$microsite_title?g" \
		    -e "s?WORK_GROUP_NAME?$work_group?g" \
		    -e "s?WORK_GROUP_URL?$work_group_url?g" \
		    -e "s?DASHBOARD?$dashboard?g" \
		    -e "s?ASSIGNEES?$assignees?g" \
		    -e "s?YMD_TSTAMP?$ymdtimestamp?g" \
		    -e "s?TIMESTAMP?$timestamp?g" \
		    -i ".back" "$file"
	else
		$NOOP sed ... -i .back $file
	fi
done

info "Delete the backup '*.back' files that were just made."
$NOOP find . -name '*.back' -exec rm {} \;

if [[ $work_branch = $publish_branch ]]
then
	info "You are publishing the website from the work branch: $work_branch."
	info "Deleting the update-main.sh script, which you don't need."
	git rm update-main.sh
fi

info "Committing changes to the work branch: $work_branch."
# Use --no-verify to suppress complaints and nonzero exit when
# there is nothing to commit.
$NOOP git commit --no-verify -m "$0: Committing changes after variable substitution." .

if [[ $work_branch != $publish_branch ]]
then
	exists=$(git br -a | grep $publish_branch | wc -l)
	if [[ $exists -eq 0 ]]
	then
		info "Create a $publish_branch branch, from which the website will be published."
		$NOOP git checkout -b $publish_branch
	else
		info "Merge the changes to the '$publish_branch' branch, from which the website will be published."
		$NOOP git checkout $publish_branch
		$NOOP git merge main
		$NOOP git commit --no-verify -m "$0: Updating the publication branch, $publish_branch, from the work branch, $work_branch" .
	fi

	info "Switching back to the $work_branch branch."
	$NOOP git checkout $work_branch
fi

if $do_push
then 
	info "Pushing all changes upstream to the GitHub repo."
	$NOOP git push --all
	[[ $status -eq 0 ]] || warn "I could not push the changes back to GitHub." "Try 'git push -all' yourself." "If that doesn't work, talk one of the Alliance engineers for help."
else
	info "You used the --no-push option; changes are not NOT pushed upstream to the GitHub repo!"
	info "You will need to run 'git push --all' yourself!"
fi

echo
info "Done! The current working directory is $PWD."
next_steps
