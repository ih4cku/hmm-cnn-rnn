#!/usr/bin/env python
from digitmodel import DigitNet
import utils
from os import path
import numpy as np
import labelfeature

frames_root_dir = '/home/paile/research/svhn_numbers/data/win_20_12/frames'
label_fn = 'lists/test.txt'
net = DigitNet()

def loadDataset(label_fn):
    labellings = labelfeature.getLabellings(label_fn)
    frame_dirs ,labels = zip(*labellings)
    frames = [utils.getFrameFiles(path.join(frames_root_dir,d)) for d in frame_dirs]
    labels = [filter(lambda x:x!=' ', lab) for lab in labels]
    return frames, labels

def mergeRepetition(labs):
    out_labs = []
    old_lab = ''
    for i in range(len(labs)-1):
        new_lab = labs[i]
        if new_lab != old_lab:
            out_labs.append(new_lab)
            old_lab = new_lab
    if labs[-1] != old_lab:
        out_labs.append(labs[-1])
    out_labs = ''.join(out_labs)
    return out_labs

def prediction(frames):
    cls_names = np.asarray(net.cls_names)
    rec_result = []

    for frm_list in frames:
        predictions = net.predict(frm_list)
        preds = cls_names[predictions.argmax(axis=1)]
        preds = mergeRepetition(preds)
        rec_result.append(preds)
    return rec_result
    
def evaluation(rec_result, gt_labels):
    n_all = len(gt_labels)
    n_true = [l1==l2 for l1,l2 in zip(rec_result, gt_labels)].count(True)
    return float(n_true)/n_all

if __name__ == '__main__':
    frames, gt_labels = loadDataset(label_fn)
    rec_result = prediction(frames)
    eval_result = evaluation(rec_result, gt_labels)
    print '----------- results -----------'
    for p in zip(rec_result, gt_labels):
        print p
    print 'seqError:', eval_result