import cPickle
import random
import os
from os import path
import glog
import cv2
import numpy as np
from collections import OrderedDict
from sklearn.decomposition import PCA
from sklearn.externals import joblib
import kaldi_io

import config
import utils

random.seed(23)

def read_frame(frm_pth):
    im = cv2.imread(frm_pth, 0).astype('float32')
    im = cv2.resize(im, config.RESHAPE_SIZE)
    return im.flatten() / 255.

def load_frames(frame_pths):
    frames_data = [read_frame(frm) for frm in frame_pths]
    return np.vstack(frames_data)

def load_frames_info(split):
    with open(split.frames_info_pth) as f:
        frames_info = cPickle.load(f)
    return frames_info

def train(split_name):
    glog.info('training PCA')
    split = config.splits[split_name]
    frames_info = load_frames_info(split)

    # select frames
    all_frames = []
    for samp_id in frames_info:
        samp_frames = [path.join(split.frames_dir, samp_id, frm) for frm in frames_info[samp_id]['frames']]
        all_frames.extend(samp_frames)
    sel_frame_pths = random.sample(all_frames, min(config.NUM_FRAMES_TRAIN, len(all_frames)))

    # read frames data
    sel_frames_data = load_frames(sel_frame_pths)

    # train PCA
    pca = PCA(n_components=0.99)
    pca.fit(sel_frames_data)

    # dump PCA
    pca_dump_dir = path.split(config.PCA_DUMP_PTH)[0]
    if not path.isdir(pca_dump_dir):
        os.makedirs(pca_dump_dir)
    joblib.dump(pca, config.PCA_DUMP_PTH)
    glog.info('PCA dump to %s', config.PCA_DUMP_PTH)


def extract_features(split_name):
    split = config.splits[split_name]

    # load PCA
    pca = joblib.load(config.PCA_DUMP_PTH)

    frames_info = load_frames_info(split)
    pca_featuers = OrderedDict()
    for samp_id in frames_info:
        samp_frames = [path.join(split.frames_dir, samp_id, frm) for frm in frames_info[samp_id]['frames']]
        raw_samp_data = load_frames(samp_frames)
        pca_samp_data = pca.transform(raw_samp_data)
        pca_featuers[samp_id] = pca_samp_data

    pca_feature_dir = path.split(split.pca_feature_pth)[0]
    if not path.isdir(pca_feature_dir):
        os.makedirs(pca_feature_dir)
    joblib.dump(pca_featuers, split.pca_feature_pth)
    glog.info('PCA features dump to %s', split.pca_feature_pth) 


def prepare_hmm_data(split_name):
    split = config.splits[split_name]
    frames_info = load_frames_info(split)
    if not path.isdir(split.hmm_data_dir):
        os.makedirs(split.hmm_data_dir)

    # text
    text_lines = []
    for samp_id in frames_info:
        text_lines.append(samp_id+' '+' '.join(frames_info[samp_id]['trans'])+'\n')
    with open(path.join(split.hmm_data_dir, 'text'), 'w') as f:
        f.writelines(text_lines)

    # utt2spk
    with open(path.join(split.hmm_data_dir, 'utt2spk'), 'w') as f:
        f.writelines([samp_id+' global\n' for samp_id in frames_info])
    # spk2utt
    with open(path.join(split.hmm_data_dir, 'spk2utt'), 'w') as f:
        f.writelines(' '.join(['global']+frames_info.keys()))

    # wrute scp, ark
    pca_featuers = joblib.load(split.pca_feature_pth)
    ark_fn = path.join(split.hmm_data_dir, 'feats.ark')
    scp_fn = path.join(split.hmm_data_dir, 'feats.scp')
    with kaldi_io.Float32MatrixWriter('ark,scp:%s,%s' % (ark_fn, scp_fn)) as w:
        for samp_id in pca_featuers:
            w[samp_id] = pca_featuers[samp_id]
    glog.info('%s hmm data done.', split_name)
