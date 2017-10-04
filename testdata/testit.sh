#!/bin/bash
for file in *.lap; do
    echo "=================== $file ================"
    python ../eldecompile/main.py $file
    echo "---             end $file      -----------"
done
