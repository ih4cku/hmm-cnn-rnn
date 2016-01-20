#!/usr/bin/env python
import config
from seqgen import frame, feature

if __name__ == '__main__':
    frame.prepare_frames('train')
    # frame.prepare_frames('test')

    if config.HMM_TRAIN:
        feature.train('train')

        feature.extract_features('train')
        feature.extract_features('test')

        feature.prepare_hmm_data('train')
        feature.prepare_hmm_data('test')    
