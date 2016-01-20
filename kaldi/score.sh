#!/bin/bash
cmd=utils/run.pl

. parse_options.sh || exit 1

if [ $# != 3 ]; then
  echo "Usage: local/score.sh [options] <data-dir> <lang-dir|graph-dir> <decode-dir>"
  echo " Options:"
  echo "    --cmd (run.pl|queue.pl...)      # specify how to run the sub-processes."
  echo "    --min-lmwt <int>                # minumum LM-weight for lattice rescoring "
  echo "    --max-lmwt <int>                # maximum LM-weight for lattice rescoring "
  exit 1
fi

data=$1
lang_or_graph=$2
dir=$3


symtab=$lang_or_graph/words.txt

for f in $symtab $dir/lat.1.gz $data/text; do
    [ ! -f $f ] && echo "score.sh: no such file $f." && exit 1
done

mkdir -p $dir/scoring/log

lattice-best-path --word-symbol-table=$symtab \
    "ark:gunzip -c $dir/lat.*.gz|" "ark,t:$dir/scoring/LMWT.tra" || exit 1

cat $dir/scoring/LMWT.tra | \
    utils/int2sym.pl -f 2- $symtab | sed 's:\<UNK\>::g' | \
    compute-wer --text --mode=present \
    ark:$data/text ark,p:- > $dir/wer_LMWT || exit 1
