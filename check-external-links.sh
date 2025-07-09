#!/usr/bin/env zsh
#---------------------------------------------------------------------------
# Checks that all external links, those starting with http*, have "targets".
#---------------------------------------------------------------------------

default_path="docs"

help() {
	cat << EOF
A fairly crude, but mostly effective tool that checks URLs in markdown
files and HTML template files to make sure they all have "targets". 
For markdown files, it prints anchor tags ("[name](url)") that don't
have a "{:target=...}" appended to them. For HTML files, it looks for 
the equivalent "<a href="..." target="...">...</a>".

It doesn't exit with an error if such links are found, because in some
cases, this might be intentional.

Usage: $script [-h|--help] [-n|--noop] [path1 ...]

Where the arguments are the following:
-h | --help            Print this message and exit
-n | --noop            Just print the commands but don't make changes.
-v | --verbose         Print the paths as they are processed. Mostly useful
                       when no problems are found and you are paranoid nothing
                       was checked. ;)
path1 ...              Check these paths. Directories will be visited recursively.
                       Default: All markdown and HTML files under "$default_path",
                       excluding files under "_site" and "_sass".
EOF
}

error() {
	for arg in "$@"
	do
		echo "ERROR: $arg"
	done
	help
	exit 1
}

paths=()
: ${VERBOSE=}
while [[ $# -gt 0 ]]
do
	case $1 in
		-h|--h*)
			help
			exit 0
			;;
		-n|--n*)
			NOOP=echo
			;;
		-v|--v*)
			VERBOSE=echo
			;;
		-*)
			error "Unrecognized option: $1"
			;;
		*)
			paths+=("$1")
			;;
	esac
	shift
done

[[ ${#paths[@]} -gt 0 ]] || paths=("$default_path")

eg=$(which egrep)
# Use a somewhat complicated script to find the URLs starting
# with http, print only the matches and then filter out the 
# URLs that contain "target". It won't work perfectly, but ...
[[ -n "$VERBOSE" ]] && echo "Checking markdown files:"
for path in "${paths[@]}"
do
	if [[ -n "$VERBOSE" ]]
	then
		dir=$([[ -d "$path" ]] && echo "(directory)")
		echo "$path $dir"
	fi
	$eg -nHoR '\(https?[^)]+\)(\S*)' \
		--include '*.markdown' --include '*.md' \
		--exclude-dir '_site' --exclude-dir '_sass' \
		$path | $eg -v 'target='
done

[[ -n "$VERBOSE" ]] && echo "Checking HTML files:"
for path in "${paths[@]}"
do
	if [[ -n "$VERBOSE" ]]
	then
		dir=$([[ -d "$path" ]] && echo "(directory)")
		echo "$path $dir"
	fi
	$eg -nHoR '<a\s*href="https?[^>]+>' \
		--include '*.html' \
		--exclude-dir '_site' --exclude-dir '_sass' \
		$path | $eg -v 'target='
done
