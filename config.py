"""
directory structure:
    TOP_ROOT
        |- data_WIDTH_STEP
        |   `- seq
        |       |- train
        |       |   |- frames
        |       |   `- features/features.pickle
        |       |
        |       |- test
        |       |   |- frames
        |       |   `- features/features.pickle
        |       |
        |       `- pca/pca.pickle
        |
        `- hmm
            `- data
                |- train
                |
                `- test
"""
from os import path

# TOP_ROOT = '/home/paile/Desktop/chars/pipeline/data/vgg/rnn'
# TOP_ROOT = '/home/paile/Desktop/chars/pipeline/data/iiit'
# TOP_ROOT = '/home/paile/Desktop/chars/pipeline/data/svhn'
# TOP_ROOT = '/home/paile/Desktop/chars/pipeline/data/icdar15'
TOP_ROOT = '/home/paile/Desktop/chars/pipeline/data/icdar03'

# sliding window param
HEIGHT = 28
WIDTH = 20
STEP  = 2

# data param
DATA_ROOT = path.join(TOP_ROOT, 'data_%d_%d' % (WIDTH, STEP))
SEQ_DATA_ROOT = path.join(DATA_ROOT, 'seq')

class Split(object):
    def __init__(self, split_name, split_trans):
        split_dir = path.join(SEQ_DATA_ROOT, split_name)
        self.split_name = split_name
        self.trans_pth  = split_trans
        self.frames_dir = path.join(split_dir, 'frames')
        self.frames_info_pth = path.join(self.frames_dir, 'frames.pickle')
        self.pca_feature_pth = path.join(split_dir, 'features', 'features.pickle')
        self.hmm_data_dir    = path.join(DATA_ROOT, 'hmm', 'data', split_name)

splits = {}
# splits['train'] = Split('train', None)
# splits['test']  = Split('test', '/home/paile/research/icdar2015/ch2test/test_trans.txt')

splits['train'] = Split('train', '/home/paile/research/icdar2003/ic03_trans.txt')

# splits['train'] = Split('train', '/home/paile/research/svhn_numbers/trans/train_trans.txt')
# splits['test']  = Split('test', '/home/paile/research/svhn_numbers/trans/test_trans.txt')

# splits['train'] = Split('train', '/home/paile/research/vggtext/train2w.txt')
# splits['test']  = Split('test', '/home/paile/research/vggtext/test1k.txt')

# splits['train'] = Split('train', '/home/paile/research/svt/svt1/words/train.txt')
# splits['test']  = Split('test', '/home/paile/research/svt/svt1/words/test.txt')

# splits['train'] = Split('train', '/home/paile/research/IIIT-5K/IIIT5K/python/train_trans.txt')
# splits['test']  = Split('test', '/home/paile/research/IIIT-5K/IIIT5K/python/test_trans.txt')

# PCA training
HMM_TRAIN = False
NUM_FRAMES_TRAIN = 20000
RESHAPE_SIZE = (HEIGHT, HEIGHT)
PCA_DUMP_PTH = path.join(SEQ_DATA_ROOT, 'pca', 'pca.pickle')

# rnnlib
RNN_NORM = True
