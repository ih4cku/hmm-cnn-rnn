#!/bin/bash

N=1
P=0
tscale=1.0
loopscale=0.1
reverse=false

. utils/parse_options.sh || exit 1;

if [ $# != 3 ]; then
    echo "Usage: $0 <lang-dir> <model-dir> <graph-dir>"
    exit 1
fi

lang=$1
tree=$2/tree
model=$2/final.mdl
dir=$3

mkdir -p $dir

required="$lang/L.fst $lang/G.fst $lang/phones.txt $lang/words.txt $lang/phones/silence.csl $lang/phones/disambig.int $model $tree"
for f in $required; do
    [ ! -f $f ] && echo "mkgraph.sh: expetect $f to exist." && exit 1
done

mkdir -p $lang/tmp

if [[ ! -s $lang/tmp/LG.fst || $lang/tmp/LG.fst -ot $lang/G.fst || \
    $lang/tmp/LG.fst -ot $lang/L_disambig.fst ]]; then
    fsttablecompose $lang/L_disambig.fst $lang/G.fst | fstdeterminizestar --use-log=true | \
        fstminimizeencoded | fstarcsort --sort_type=ilabel > $lang/tmp/LG.fst || exit 1
    fstisstochastic $lang/tmp/LG.fst || echo "[info]: LG not stochastic."
fi

clg=$lang/tmp/CLG_${N}_${P}.fst

if [[ ! -s $clg || $clg -ot $lang/tmp/LG.fst ]]; then
    fstcomposecontext --context-size=$N --central-position=$P \
        --read-disambig-syms=$lang/phones/disambig.int \
        --write-disambig-syms=$lang/tmp/disambig_ilabels_${N}_${P}.int \
        $lang/tmp/ilabels_${N}_${P} < $lang/tmp/LG.fst |\
        fstarcsort --sort_type=ilabel > $clg
    fstisstochastic $clg || echo "[info]: CLG not stochastic."
fi

if [[ ! -s $dir/Ha.fst || $dir/Ha.fst -ot $model || \
    $dir/Ha.fst -ot $lang/tmp/ilabels_${N}_${P} ]]; then
    make-h-transducer --disambig-syms-out=$dir/disambig_tid.int \
        --transition-scale=$tscale $lang/tmp/ilabels_${N}_${P} $tree $model \
        > $dir/Ha.fst || exit 1
fi

if [[ ! -s $dir/HCLGa.fst || $dir/HCLGa.fst -ot $dir/Ha.fst || \
    $dir/HCLGa.fst -ot $clg ]]; then
    fsttablecompose $dir/Ha.fst $clg | fstdeterminizestar --use-log=true \
        | fstrmsymbols $dir/disambig_tid.int | fstrmepslocal | \
        fstminimizeencoded > $dir/HCLGa.fst || exit 1
    fstisstochastic $dir/HCLGa.fst || echo "HCLGa is not stochastic."
fi

if [[ ! -s $dir/HCLG.fst || $dir/HCLG.fst -ot $dir/HCLGa.fst ]]; then
    add-self-loops --self-loop-scale=$loopscale --reorder=true \
        $model < $dir/HCLGa.fst > $dir/HCLG.fst || exit 1

    if [ $tscale == 1.0 -a $loopscale == 1.0 ]; then
        fstisstochastic $dir/HCLG.fst || echo "[info]: final HCLG is not stochastic."
    fi
fi

cp $lang/words.txt $dir/ || exit 1
mkdir -p $dir/phones
cp $lang/phones/word_boundary.* $dir/phones/ 2>/dev/null
cp $lang/phones/align_lexicon.* $dir/phones/ 2>/dev/null

cp $lang/phones/disambig.{txt,int} $dir/phones/ 2>/dev/null
cp $lang/phones/silence.csl $dir/phones/ || exit 1
cp $lang/phones.txt $dir/ 2>/dev/null

am-info --print-args=false $model | grep pdfs | awk '{print $NF}' > $dir/num_pdfs

exit 0