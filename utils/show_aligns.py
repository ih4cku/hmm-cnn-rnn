#!/usr/bin/env python
"""
set "aligns_dir" and "out_dir" and run.
"""
import cv2
import re
import sys
import os
import random
from os import path
import subprocess
from glob import glob
import numpy as np 
from collections import OrderedDict

from seqgen import frame
import config

# read phones
align_bin  = '/home/paile/codes/kaldi-c09caf9/src/bin/show-alignments'
aligns_dir = path.join(config.DATA_ROOT, 'hmm', 'aligns')

def get_windows(image_wid, wid, step):
    """
    get sliding windows, shape (N, 2). 
    NOTE! this function must be consistent with `seqgen.frame.sliding_windows()`

    [[w1_x1, w1_x2],
     [w2_x1, w2_x2],
     [w3_x1, w3_x2],
     ...
    ]
    """
    windows = []
    for x1 in range(0, image_wid, step):
        x2 = x1+wid-1
        if x2 >= image_wid:
            windows.append((x1, image_wid-1))
            break
        else:
            windows.append((x1, x2))
    return np.array(windows)


def parse_sample(align_ele):
    """
    `align_ele`: clip of an sample in the alignment output, including ["align_line", "trans_line"]

    e.g.
        align_ele: ['train_9399  [ 178 ] [ 429 434 433 ] [ 324 328 ] [ 388 392 390 390 390 390 390 390 390 390 ] ...'
                    'train_9399  sil     r               e           m                                           ...']

    """
    align_line, trans_line = align_ele
    samp_id = align_line.split()[0]
    n_frame = [len(l.strip().split()) for l in re.findall(r'\[(.*?)\]', align_line) ]
    assert trans_line.split()[0] == samp_id, 'samp_id not same between alignment line and transcription line'
    trans = trans_line.split()[1:]
    assert len(n_frame) == len(trans), 'length not equal between aligns and trans, %d vs %d.' % (len(n_frame), len(trans))
    return samp_id, n_frame, trans

def parse_align_output(align_output):
    """
    parse output of `show-alignments`.

    return all_aligns[samp_id]: 
        list of 2-element list [n_frame, trans].
        e.g. all_aligns[train_0] 
                    `- [[1, 15, 2, 2, 2, 2, 3, 4, 3], ['sil', 'a', 'm', 'e', 't', 'h', 'y', 's', 't']]
    """
    lines = align_output.splitlines()
    lines = [l.strip() for l in lines if l.strip()]

    assert len(lines) % 2 == 0, 'number of lines is not even.'
    align_arr = np.array(lines, dtype=object).reshape((-1, 2))
    all_aligns = OrderedDict()
    for align_ele in align_arr:
        samp_id, n_frame, trans = parse_sample(align_ele)
        all_aligns[samp_id] = [n_frame, trans]
    return all_aligns

def get_phones_colors(phones_fn):
    """
    generate random colors for each HMM model.
    """
    with open(phones_fn) as f:
        phones = f.readlines()
        phones = [l.strip().split()[0] for l in phones]
    colors = np.random.randint(0, 255, (len(phones), 3))
    colors[phones.index('sil')] = [0, 0, 0]
    return phones, colors

def get_char_ranges(windows, n_frame):
    """
    return pixel ranges of each char.
    """
    # fill frame ranges of each char
    idx_beg = 0
    char_ranges = []
    for frm_count in n_frame:
        idx_end = idx_beg+frm_count-1
        char_ranges.append((windows[idx_beg, 0], windows[idx_end, 1]))
        idx_beg = idx_end+1
    char_ranges = np.array(char_ranges)

    # cut overlapping alignmetns
    for i in range(char_ranges.shape[0]-1):
        mid = (char_ranges[i, 1] + char_ranges[i+1, 0])/2
        char_ranges[i, 1] = mid-1
        char_ranges[i+1, 0] = mid

    return char_ranges

def draw_segmentation(im, trans, char_ranges, phones, colors, samp_out_pth):
    """
    im      : a grayscale image.
    trans   : e.g. ['sil', 'a', 'm', 'e', 't', 'h', 'y', 's', 't']
    """
    im = np.dstack([im, im, im])
    for i, lab in enumerate(trans):
        c = colors[phones.index(lab)]
        if np.array_equal(c, [0, 0, 0]):
            im[:, char_ranges[i, 0]:char_ranges[i, 1]] = im[:, char_ranges[i, 0]:char_ranges[i, 1]]*0.5 + c*0.5
        else:
            im[:, char_ranges[i, 0]:char_ranges[i, 1]] = im[:, char_ranges[i, 0]:char_ranges[i, 1]]*0.7 + c*0.3
    # save vis result
    print 'saving to:', samp_out_pth
    hei, wid = im.shape[:2]
    samp_out_dir = path.split(samp_out_pth)[0]
    if not path.isdir(samp_out_dir):
        os.makedirs(samp_out_dir)    
    cv2.imwrite(samp_out_pth, cv2.resize(im, (wid*3, hei*3)))


def save_char_frames(im, trans, char_ranges, samp_id, chars_out_dir):
    """
    save char images.
    """
    for i, lab in enumerate(trans):
        x1, x2 = char_ranges[i]
        char_wid = x2-x1+1
        im_char = im[:, x1:x2]
        if char_wid > 30:
            continue
        if char_wid < 20:
            pad_wid = (20-char_wid)/2
            im_char = im[:, max(0, x1-pad_wid):min(im.shape[1], x2+pad_wid)]
        else:
            im_char = im[:, x1:x2]
        char_dir = path.join(chars_out_dir, lab)
        if not path.isdir(char_dir): 
            os.makedirs(char_dir)
        char_out_pth = path.join(char_dir, '%s_%d.png' % (samp_id, i))
        cv2.imwrite(char_out_pth, im_char)


def save_align_result(samp_id, samp_info, samp_align, phones, colors, samp_out_pth, chars_out_dir=None):
    """
    samp_info   : {'image', 'trans', 'frames'}, see `seqgen.frame.prepare_frames()`
    samp_align  : [n_frame, trans], see `parse_align_output()`

    char_ranges : shape (N_chars, 2)
    """
    im = frame.load_image(samp_info['image'])
    windows = get_windows(im.shape[1], config.WIDTH, config.STEP)

    assert samp_info['trans'] == ''.join([l for l in samp_align[1] if l!='sil']), \
        'ground truth and align trans not same. %s vs %s.' % \
        (samp_info['trans'], ''.join([l for l in samp_align[1] if l!='sil']))
    assert sum(samp_align[0]) == len(windows), \
        'sample frames number different. %d vs %d.' % \
        (sum(samp_align[0]), len(windows))

    n_frame, trans = samp_align

    # get char ranges
    char_ranges = get_char_ranges(windows, n_frame)

    # overlap color on chars
    draw_segmentation(im, trans, char_ranges, phones, colors, samp_out_pth)

    # save frames to chars
    if chars_out_dir:
        save_char_frames(im, trans, char_ranges, samp_id, chars_out_dir)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        aligns_out_dir = sys.argv[1]
        chars_out_dir  = None
    elif len(sys.argv) == 3:
        aligns_out_dir = sys.argv[1]
        chars_out_dir  = sys.argv[2]
    else:
        print 'Usage: %s aligns_out_dir chars_out_dir'
        sys.exit(1)

    # set phones and colors
    phones_fn = path.join(aligns_dir, 'phones.txt')
    phones, colors = get_phones_colors(phones_fn)

    # get all sample frames info
    frames_info = frame.get_frames('train')
    # sel_samp_ids = random.sample(frames_info.keys(), 2000)
    sel_samp_ids = frames_info.keys()

    # get all alignments
    iters = sorted(os.walk(aligns_dir).next()[1], key=lambda x: int(x))
    # process each iter
    for it in iters:
        print 'Iter:', it
        iter_dir = path.join(aligns_dir, it)
        model_fn = path.join(iter_dir, it+'.mdl')

        # process each job
        for job_gz in glob(path.join(iter_dir, 'ali.*.gz')):
            print 'Job:', job_gz
            align_ark = 'ark:gunzip -c %s|' % job_gz
            # execute "show-alignment" command
            align_output = subprocess.check_output([align_bin, '--print-args=false', phones_fn, model_fn, align_ark])
            aligns = parse_align_output(align_output)

            # process each sample
            for samp_id in set(sel_samp_ids) & set(aligns.keys()):
                samp_out_dir = path.join(aligns_out_dir, samp_id)
                samp_out_pth = path.join(samp_out_dir, it+'.png')
                if it == iters[-1]:
                    # save char frames
                    save_align_result(samp_id, frames_info[samp_id], aligns[samp_id], phones, colors, samp_out_pth, chars_out_dir)
                else:
                    # only save ailgnment drawing
                    save_align_result(samp_id, frames_info[samp_id], aligns[samp_id], phones, colors, samp_out_pth)
