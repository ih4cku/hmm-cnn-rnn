#!/bin/bash
set -e

# NOTE! Make sure the data is for the dataset!
hmm_root="/home/paile/Desktop/chars/pipeline/data/svhn/data_5_5/hmm"
dataset="svhn"

if [ ! -f dataset/$dataset/prepare_lang.sh ]; then
    echo "Error: No such dataset \"$dataset\""
    exit 1
fi

aligns_dir=$hmm_root/aligns
lang=$hmm_root/lang

rm -rf $hmm_root/data/*/split*/
rm -rf $lang
rm -rf $hmm_root/exp

# prepare lang
dataset/$dataset/prepare_lang.sh $lang

# train_mono.sh <data> <lang> <exp>
./train_mono.sh --nj 8 --totgauss 1000 --num_iters 100 --max_iter_inc 50 \
    $hmm_root/data/train $hmm_root/lang $hmm_root/exp/mono0a $aligns_dir

# # make decoding graph
# ./mkgraph.sh $lang $hmm_root/exp/mono0a $hmm_root/exp/mono0a/graph

# # decode
# ./decode.sh --nj 8 $hmm_root/exp/mono0a/graph $hmm_root/data/test  $hmm_root/exp/mono0a/decode_test
# ./decode.sh --nj 8 $hmm_root/exp/mono0a/graph $hmm_root/data/train $hmm_root/exp/mono0a/decode_train

# # Getting results
# echo "----- test error -----"
# grep WER $hmm_root/exp/mono0a/decode_test/wer_*  | utils/best_wer.sh
# grep SER $hmm_root/exp/mono0a/decode_test/wer_*  | utils/best_wer.sh
# echo "----- train error -----"
# grep WER $hmm_root/exp/mono0a/decode_train/wer_* | utils/best_wer.sh
# grep SER $hmm_root/exp/mono0a/decode_train/wer_* | utils/best_wer.sh
