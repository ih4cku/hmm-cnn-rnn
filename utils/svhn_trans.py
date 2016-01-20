#!/usr/bin/env python
"""
Extract text from digitStruct.mat
"""
import os
import numpy as np
from os import path
import h5py
from itertools import izip

def show_keys(grp, d):
    try:
        for k in grp.keys():
            print '  '*d, k
            show_keys(grp[k], d+1)
    except AttributeError, e:
        return

DIGITS = np.array(['null', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'])

def parse_mat(image_root, trans_pth):
    mat_pth = path.join(image_root, 'digitStruct.mat')

    f_mat = h5py.File(mat_pth)
    digitStruct = f_mat['digitStruct']
    # get names
    print 'getting image paths ...'
    names = digitStruct['name'][:].flatten()
    images = [''.join(map(chr, f_mat[l][:].flatten())) for l in names]

    # get labels
    print 'getting labels ...'
    bboxs = digitStruct['bbox'][:].flatten()
    labels = [] 
    for l in bboxs:
        lab = f_mat[l]['label'][:].flatten()
        if lab.shape[0] == 1:
            lab = [int(lab[0])]
        else:
            lab = [int(f_mat[sl][:].flatten()[0]) for sl in lab]
        labels.append(lab)

    # print
    print 'putting into lines ...'
    lines = []
    for i, l in izip(images, labels):
        lines.append('%s %s\n' % (path.join(image_root, i), ''.join(DIGITS[np.array(l)])))

    print 'dumping to', trans_pth, '...'
    with open(trans_pth, 'w') as f:
        f.writelines(lines)
    print 'done.'

if __name__ == '__main__':
    parse_mat('/home/paile/research/svhn_numbers/images/train', 'train_trans.txt')
    parse_mat('/home/paile/research/svhn_numbers/images/test', 'test_trans.txt')
