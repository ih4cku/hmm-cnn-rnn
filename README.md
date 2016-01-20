These codes is used by myself and not well organized yet. :-p

# running pipeline 

1. prepare transcriptions
    - `utils/xxx_trans.py`
2. prepare `allwords.txt` in dataset dir
3. generate files used in lang
    - `utils/gen_lang_files.py`
4. set path in `config.py`
5. run `pipeline.py` to generate data
6. run `kaldi/run.sh`
    - !Remember to set `hmm_root` and `dataset`
7. run `utils/visaligns.sh`
    - show alignments
    - crop chars
8. generate sample list for caffe with `utils/gen_list.sh`

# caffe

1. run `caffe/makeds.sh`
2. train digit model 
    - `cd caffe`
    - `./train.sh`


# rnnlib

1. run `rnnlib/create_nc.py` in the folder with `config.py`