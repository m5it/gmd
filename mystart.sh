#!/bin/bash
# Script to start program trough .venv. It also check if .venv exists.
# Link to ex.: /usr/local/bin/gmd then you can run like:
# gmd -h OR gmd --help OR gmd gui

#
if [[ ! -d ".venv" ]]; then
	echo "Required to install requirements.txt to .venv directory"
	exit 1
fi

#
./.venv/bin/python ./main.py $@
