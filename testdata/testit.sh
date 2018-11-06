#!/bin/bash
if (( $# == 0 )) ; then
    files=*.lap
else
    files="$@"
fi

for file in *.lap; do
    echo "=================== $file ================"
    if ! python ../eldecompile/main.py $file; then
	exit $?
    fi
    echo "---             end $file      -----------"
done
