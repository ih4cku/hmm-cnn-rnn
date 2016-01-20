#!/bin/bash
# This script prepares the lang/ directory.

echo "$0 $@"  # Print the command line for logging

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ $# != 1 ]; then
  echo "Usage: $0 <lang-dir>"
  exit 1
else
  lang=$1
fi

if [ ! -f $DIR/lexicon.txt ]; then
  echo "$DIR/lexicon.txt not exist."
  exit 1
fi

mkdir -p $lang $lang/phones
cp $DIR/lexicon.txt $lang

# symbol-table for words which are extracted from the lexicon symbol table
cat $lang/lexicon.txt | awk '{print $1}' | awk 'BEGIN {print "<eps> 0"; n=1;} { printf("%s %s\n", $1, n++); }' \
 >$lang/words.txt

# list of phones.
cat $lang/lexicon.txt | awk '{for(n=2;n<=NF;n++) seen[$n]=1; } END{ for (w in seen) { print w; }}' \
 >$lang/phone.list

# symbol-table for phones:
cat $lang/phone.list | awk 'BEGIN {print "<eps> 0"; n=1;} { printf("%s %s\n", $1, n++); }' \
 >$lang/phones.txt

p=$lang/phones
echo "sil" > $p/silence.txt
echo "sil" > $p/context_indep.txt
echo "sil" > $p/optional_silence.txt
grep -v -w "sil" $lang/phone.list > $p/nonsilence.txt
touch $p/disambig.txt # disambiguation-symbols list, will be empty.
touch $p/extra_questions.txt # list of "extra questions"-- empty; we don't
 # have things like tone or word-positions or stress markings.
cat $lang/phone.list > $p/sets.txt # list of "phone sets"-- each phone is in its
 # own set.  Normally, each line would have a bunch of word-position-dependenent or
 # stress-dependent realizations of the same phone.

for t in silence nonsilence context_indep optional_silence disambig; do
  utils/sym2int.pl $lang/phones.txt <$p/$t.txt >$p/$t.int
  cat $p/$t.int | awk '{printf(":%d", $1);} END{printf "\n"}' | sed s/:// > $p/$t.csl 
done
for t in extra_questions sets; do
  utils/sym2int.pl $lang/phones.txt <$p/$t.txt >$p/$t.int
done

cat $lang/phone.list | awk '{printf("shared split %s\n", $1);}' >$p/roots.txt
utils/sym2int.pl -f 3-  $lang/phones.txt $p/roots.txt >$p/roots.int

echo "<SIL>" > $lang/oov.txt # we map OOV's to this.. there are no OOVs in this setup,
   # but the scripts expect this file to exist.
utils/sym2int.pl $lang/words.txt <$lang/oov.txt >$lang/oov.int

# Note: "word_boundary.{txt,int}" will not exist in this setup.  This will mean it's
# not very easy to get word alignments, but it simplifies some things.

# Make the FST form of the lexicon (this includes optional silence).
# utils/make_lexicon_fst.pl $lang/lexicon.txt | \
utils/make_lexicon_fst.pl $lang/lexicon.txt 0.2 "sil" | \
  fstcompile --isymbols=$lang/phones.txt --osymbols=$lang/words.txt \
  --keep_isymbols=false --keep_osymbols=false | \
   fstarcsort --sort_type=olabel > $lang/L.fst 

# Note: in this setup there are no "disambiguation symbols" because the lexicon
# contains no homophones; and there is no '#0' symbol in the LM because it's
# not a backoff LM, so L_disambig.fst is the same as L.fst.

cp $lang/L.fst $lang/L_disambig.fst

silphonelist=`cat $lang/phones/silence.csl | sed 's/:/ /g'`
nonsilphonelist=`cat $lang/phones/nonsilence.csl | sed 's/:/ /g'`
cat $DIR/topo.proto | sed "s:NONSILENCEPHONES:$nonsilphonelist:" | \
   sed "s:SILENCEPHONES:$silphonelist:" > $lang/topo

# use thrax to prepare G.fst 
cat $DIR/G.grm.template | \
  sed -e "s:WORDS_SYMTAB:$lang/words.txt:" -e "s:LINES_FILE:$DIR/sep_words.txt:" > $lang/G.grm
thraxcompiler --input_grammar=$lang/G.grm --output_far=$lang/G.far
farextract --filename_suffix=.fst --filename_prefix=$lang/ $lang/G.far
[ -f $lang/G.fst ] || { echo "ERROR: G.fst not extracted from G.far."; exit 1; }
fstarcsort --sort_type=ilabel $lang/G.fst $lang/G.fst
[ -f $lang/G.fst ] || { echo "ERROR: G.fst not generated."; exit 1; }
