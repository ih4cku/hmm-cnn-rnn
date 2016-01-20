#!/bin/bash
# note: not finished

# functions ##############
show_fst() {
    if [ $# != 4 ]; then
        echo "Usage: show_fst isymbols osymbols in.fst out.png"
        exit 1;
    fi

    isymbols=$1
    osymbols=$2
    fstfn=$3
    outfn=$4
    ext=${outfn##*.}

    fstdraw --portrait=true --isymbols=$isymbols --osymbols=$osymbols $fstfn | \
        dot -T$ext > $outfn
    if [[ $ext = "pdf" ]]; then
        pdfcrop $outfn $outfn
    fi
}


# relateive dirs ##############
hmm_dir="/home/paile/Desktop/chars/pipeline/data/data_20_5/hmm"
vis_dir="/home/paile/Desktop/chars/pipeline/kaldi/vis"

tr_data=$hmm_dir/data/train
te_data=$hmm_dir/data/test
lang=$hmm_dir/lang
exp=$hmm_dir/exp/mono0a

phones_syms=$lang/phones.txt
words_syms=$lang/words.txt

# show L and G
show_fst $phones_syms $words_syms $lang/L.fst $vis_dir/L.pdf
show_fst $words_syms $words_syms $lang/G.fst $vis_dir/G.pdf

