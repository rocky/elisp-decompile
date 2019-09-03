#!/bin/bash
me=${BASH_SOURCE[0]}
mydir=$(dirname $me)
builtin cd $mydir/lap
if (( $# == 0 )) ; then
    files=*.lap
else
    files="$@"
fi

for file in *.lap; do
    echo "=================== $file ================"
    if ! python ../../lapdecompile/main.py $file; then
	exit $?
    fi
    echo "---             end $file      -----------"
done
