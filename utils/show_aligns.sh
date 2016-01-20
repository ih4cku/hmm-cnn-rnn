#!/bin/bash
# This script showing training alignments and copy the last iter out
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ $# != 2 ]; then
    echo "Usage: $0 aligns_out_dir iter"
    exit 1
else
    aligns_out_dir=$1
    iter=$2
fi

aligns_dir="$aligns_out_dir/alis"
aligns_final_dir="$aligns_out_dir/aligns_$iter"
chars_out_dir="$aligns_out_dir/chars"

# show alignments on image
$DIR/show_aligns.py $aligns_dir $chars_out_dir

mkdir -p $aligns_final_dir
for f in `find $aligns_dir -name $iter.png`; do
    echo $f
    cp $f "$aligns_final_dir/$(echo $f | rev | cut -d'/' -f2 | rev).png"
done
