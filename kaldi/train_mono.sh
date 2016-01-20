#!/bin/bash

# copy aligns to show
copy_aligns() {
  if [ $# != 1 ]; then
    echo "Usage: copy_aligns <iter>"
    exit 1;
  fi
  iter=$1
  dst_dir=$aligns_dir/$iter
  mkdir -p $dst_dir
  # copy model and aligns
  for i in $(seq 1 $nj); do
    cp $exp/$x.mdl $exp/ali.$i.gz $dst_dir/
  done
  # copy phones
  if [ ! -f $aligns_dir/phones.txt ]; then
    cp $lang/phones.txt $aligns_dir/
  fi
}

echo "$0 $@"

nj=1
cmd=utils/run.pl
num_iters=100
max_iter_inc=40
realign_iters=
totgauss=100
careful=true

# parse options
. utils/parse_options.sh || exit 1;

# pass arguments
if [ $# -lt 3 ]; then
  echo "Usage: $0 [options] <data-dir> <lang-dir> <exp-dir> <aligns-dir>"
  echo " e.g.: $0 data/train.1k data/lang exp/mono"
  echo "main options (for others, see top of script file)"
  echo "  --nj <nj>                                        # number of parallel jobs"
  echo "  --cmd (utils/run.pl|utils/queue.pl <queue opts>) # how to run jobs."
  exit 1;
else
  data=$1
  lang=$2
  exp=$3
  aligns_dir=$4
fi

# clear aligns_dir
echo "aligns_dir: $aligns_dir"
if [ ! -z $aligns_dir ] && [ -d $aligns_dir ]; then
  echo "delete aligns_dir."
  rm -rf $aligns_dir
fi

oov_sym=`cat $lang/oov.int` || exit 1

# split data
sdata=$data/split$nj
echo "split data: $sdata"
[[ -d $sdata && $data/feats.scp -ot $sdata ]] || utils/split_data.sh --per-utt $data $nj || exit 1

# define feats
feats="ark:copy-feats scp:$sdata/JOB/feats.scp ark:- |"
example_feats="`echo $feats | sed s/JOB/1/g`"

# init 
echo "$0: Initializing monophone system."
[ ! -f $lang/phones/sets.int ] && exit 1
shared_phones_opt="--shared-phones=$lang/phones/sets.int"
feat_dim=`feat-to-dim "$example_feats" -`
echo "dim: $feat_dim"
$cmd JOB=1 $exp/log/init.log \
    gmm-init-mono $shared_phones_opt "--train-feats=$feats subset-feats --n=2000 ark:- ark:-|" \
    $lang/topo $feat_dim $exp/0.mdl $exp/tree || exit 1

# set gaussian update number
numgauss=`gmm-info --print-args=false $exp/0.mdl | grep gaussians | awk '{print $NF}'`
incgauss=$(( ($totgauss-$numgauss)/$max_iter_inc ))

# compile training graph
echo "$0: Compiling training graphs"
$cmd JOB=1:$nj $exp/log/compile_graphs.JOB.log \
    compile-train-graphs $exp/tree $exp/0.mdl $lang/L.fst \
    "ark:utils/sym2int.pl --map-oov $oov_sym -f 2- $lang/words.txt < $sdata/JOB/text|" \
    "ark:|gzip -c > $exp/fsts.JOB.gz" || exit 1

# equal alignment estimate
$cmd JOB=1:$nj $exp/log/align.0.JOB.log \
    align-equal-compiled "ark:gunzip -c $exp/fsts.JOB.gz|" "$feats" ark,t:- \| \
    gmm-acc-stats-ali --binary=true $exp/0.mdl "$feats" ark:- \
    $exp/0.JOB.acc || exit 1

gmm-est --min-gaussian-occupancy=5 --mix-up=$numgauss \
    $exp/0.mdl "gmm-sum-accs - $exp/0.*.acc|" $exp/1.mdl 2>$exp/log/update.0.log || exit 1
rm $exp/0.*.acc

# iteratively align and update GMM
beam=10
x=1
while [ $x -lt $num_iters ]; do
    echo "$0: Pass $x"
  # if echo $realign_iters | grep -w $x >/dev/null; then
    echo "$0: Aligning data"
    $cmd JOB=1:$nj $exp/log/align.$x.JOB.log \
        gmm-align-compiled --beam=$beam --retry-beam=$(( $beam*4 )) --careful=$careful $exp/$x.mdl \
            "ark:gunzip -c $exp/fsts.JOB.gz|" "$feats" "ark,t:|gzip -c >$exp/ali.JOB.gz" || exit 1
  # fi
    $cmd JOB=1:$nj $exp/log/acc.$x.JOB.log \
        gmm-acc-stats-ali $exp/$x.mdl "$feats" "ark:gunzip -c $exp/ali.JOB.gz|" \
        $exp/$x.JOB.acc || exit 1

    $cmd $exp/log/update.$x.log \
        gmm-est --write-occs=$exp/$(( $x+1 )).occs --mix-up=$numgauss $exp/$x.mdl \
        "gmm-sum-accs - $exp/$x.*.acc|" $exp/$(( $x+1 )).mdl || exit 1
    
    if [ $x -le $max_iter_inc ]; then
        numgauss=$(( $numgauss+$incgauss ))
    fi

    # if aligns_dir is set, then copy alignments
    if [ ! -z $aligns_dir ]; then
      copy_aligns $x
    fi
    rm $exp/$x.mdl $exp/$x.*.acc $exp/$x.occs 2>/dev/null

    x=$(( $x+1 ))
done

( cd $exp; rm final.{mdl,occs} 2>/dev/null; ln -s $x.mdl final.mdl; ln -s $x.occs final.occs )

utils/summarize_warnings.pl $exp/log

echo "Training done."
