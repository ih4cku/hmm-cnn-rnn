import os
from os import path
from collections import OrderedDict
import cv2
import cPickle
import sys
import glog

import config
import utils

def sliding_windows(im, wid, step):
    for x1 in range(0, im.shape[1], step):
        x2 = x1 + wid
        yield im[:, x1:x2]
        if x2 > im.shape[1]: 
            return

# io
def norm_height(im):
    hei, wid = im.shape
    scale = float(config.HEIGHT) / hei
    im = cv2.resize(im, (int(wid * scale), config.HEIGHT))
    return im

def load_image(image_pth):
    im = cv2.imread(image_pth, 0)
    im = norm_height(im)
    return im

# frames
def extract_frames(im, samp_id, frames_dir):
    """
    perform sliding windows on word image and save to disk.
    return frames filename list.

    e.g. ['0.jpg', '1.jpg', '2.jpg', '3.jpg', '4.jpg', ...]
    """
    out_dir = path.join(frames_dir, samp_id)
    if not path.isdir(out_dir):
        os.makedirs(out_dir)
    frame_pths = []
    for i_frm, im_sub in enumerate(sliding_windows(im, config.WIDTH, config.STEP)):
        frm_fn = '%d.jpg' % (i_frm,)
        frm_out_pth = path.join(out_dir, frm_fn)
        cv2.imwrite(frm_out_pth, im_sub)
        frame_pths.append(frm_fn)
    return frame_pths

def get_frames(split_name):
    """
    return `frames_info` of split_name

    see: `prepare_frames()`
    """
    split = config.splits[split_name]
    with open(split.frames_info_pth) as f:
        frames_info = cPickle.load(f)
    return frames_info


def prepare_frames(split_name):
    """
    extract fraems for dataset `split_name`.
    pickle to disk.

    frames_info[samp_id]
                |- image: image path
                |- trans: word label (without space)
                `- frames: frame images filename list
    e.g. 
        frames_info[train_0]: {
            'frames': ['0.jpg', '1.jpg', '2.jpg', '3.jpg', '4.jpg', ...], 
            'image': '/home/paile/research/mjsynth/mnt/ramdisk/max/90kDICT32px/378/5/54_amethyst_2482.jpg', 
            'trans': 'amethyst'
        }
    """
    print 'processing:', split_name, '-------------------------'
    # read split info
    split = config.splits[split_name]
    trans_path = split.trans_pth
    frames_dir = split.frames_dir
    if path.isdir(frames_dir):
        glog.warning('%s already exists.', frames_dir)
        sys.exit(-1)
    print 'trans_path:', trans_path
    print 'frames_dir:', frames_dir

    # read trans
    all_trans = utils.read_table(trans_path)

    # assign sample id
    trans_ids = ['%s_%d' % (split_name, i) for i in range(len(all_trans))]
    all_trans = OrderedDict(zip(trans_ids, all_trans))

    # frames info
    frames_info = OrderedDict()
    err_images = []
    for samp_id in all_trans:
        try:
            image_pth = all_trans[samp_id][0]
            im = load_image(image_pth)
            frame_pths = extract_frames(im, samp_id, frames_dir)
            frames_info[samp_id] = {}
            frames_info[samp_id]['image']  = image_pth
            frames_info[samp_id]['trans']  = all_trans[samp_id][1]
            frames_info[samp_id]['frames'] = frame_pths
        except Exception, e:
            err_images.append(image_pth+'\n')
            print 'Error:', image_pth

    if len(err_images) != 0:
        with open('err_images.txt', 'w') as f:
            f.writelines(err_images)

    # save
    with open(split.frames_info_pth, 'w') as f:
        cPickle.dump(frames_info, f)
    print 'frames info save to', split.frames_info_pth
