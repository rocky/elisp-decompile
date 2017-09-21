#!/bin/bash
for file in *.dis; do
    echo "=================== $file ================"
    python ../eldecompile/main.py $file
    echo "---             end $file      -----------"
done
