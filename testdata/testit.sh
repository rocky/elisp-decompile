#!/bin/bash
for file in *.lap; do
    echo "=================== $file ================"
    if ! python ../eldecompile/main.py $file; then
	exit $?
    fi
    echo "---             end $file      -----------"
done
