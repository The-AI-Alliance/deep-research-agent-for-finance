#!/usr/bin/env zsh
#------------------------------------------------------------------------
# A simple script that merges the latest work from "latest" to "main",
# pushes the updates upstream, then switches to "latest" again.
# This is mostly useful if you tend to work in "latest", so updates are
# published immediately, and you periodically want to update main.
#------------------------------------------------------------------------

git checkout latest
git pull
git checkout main
git pull
git merge latest
git push
git checkout latest
