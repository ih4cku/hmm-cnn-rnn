#!/bin/bash
nj=4
cmd=utils/run.pl
num_threads=4 # if >1, will use gmm-latgen-faster-parallel
beam=10
lattice_beam=6

. utils/parse_options.sh || exit 1;

echo "$0 $@"

if [ $# != 3 ]; then 
    echo "Usage: $0 [options] <graph-dir> <data-dir> <decode-dir>"
    echo "... where <decode-dir> is assumed to be the sub-directory of the directory"
    echo "where the model is."
    echo "main options (for others, see top of script file)"
    echo "  --config <config-file>                           # config containing options"
    echo "  --nj <nj>                                        # number of parallel jobs"
    echo "  --iter <iter>                                    # Iteration of model to test."
    echo "  --model <model>                                  # which model to use (e.g. to"
    echo "                                                   # specify the final.alimdl)"
    echo "  --cmd (utils/run.pl|utils/queue.pl <queue opts>) # how to run jobs."
    echo "  --transform-dir <trans-dir>                      # dir to find fMLLR transforms "
    echo "  --acwt <float>                                   # acoustic scale used for lattice generation "
    echo "  --scoring-opts <string>                          # options to local/score.sh"
    echo "  --num-threads <n>                                # number of threads to use, default 1."
    echo "  --parallel-opts <opts>                           # ignored now, present for historical reasons."
    exit 1
fi

graphdir=$1
data=$2
dir=$3
srcdir=`dirname $dir`
sdata=$data/split$nj

mkdir -p $dir/log

# split data
[[ -d $sdata && $data/feats.scp -ot $sdata ]] || utils/split_data.sh --per-utt $data $nj || exit 1
echo $nj > $dir/num_jobs

# set model
if [ -z "$model" ]; then
    if [ -z $iter ]; then 
        model=$srcdir/final.mdl
    else
        model=$srcdir/$iter.mdl
    fi
fi

# check files
for f in $sdata/1/feats.scp $model $graphdir/HCLG.fst; do
    [ ! -f $f ] && echo "decode.sh: no such file $f." && exit 1
done

thread_string=
[ $num_threads -gt 1 ] && thread_string="-parallel --num-threads=$num_threads"

feats="ark:copy-feats scp:$sdata/JOB/feats.scp ark:- |"

if [ -f "$graphdir/num_pdfs" ]; then
    [ "`cat $graphdir/num_pdfs`" -eq `am-info --print-args=false $model |\
        grep pdfs | awk '{print $NF}'` ] || \
        { echo "Mismatch in number of pdfs with $model"; exit 1; }
fi

# $cmd --num-threads $num_threads JOB=1:$nj $dir/log/decode.JOB.log \
#     gmm-latgen-faster$thread_string --beam=$beam --lattice-beam=$lattice_beam \
#         --word-symbol-table=$graphdir/words.txt \
#         $model $graphdir/HCLG.fst "$feats" "ark:|gzip -c > $dir/lat.JOB.gz" || exit 1

# [ ! -x score.sh ] && echo "local/score.sh not exist for scoring." && exit 1
# ./score.sh --cmd "$cmd" $data $graphdir $dir || { echo "$0: Scoring failed."; exit 1; }

mkdir -p $dir/scoring
$cmd JOB=1:$nj $dir/log/decode.JOB.log \
    gmm-decode-faster --beam=$beam --word-symbol-table=$graphdir/words.txt \
        $model $graphdir/HCLG.fst "$feats" "ark,t:$dir/scoring/LMWT.tra" || exit 1

cat $dir/scoring/LMWT.tra | \
    utils/int2sym.pl -f 2- $graphdir/words.txt | sed 's:\<SIL\>::g' | \
    compute-wer --text --mode=present "ark:$data/text" "ark,p:-" > $dir/wer_LMWT || exit 1
