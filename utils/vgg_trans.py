import sys
import os
from os import path
import random

image_dir = '/home/paile/research/mjsynth/mnt/ramdisk/max/90kDICT32px'
anno_pth  = '/home/paile/research/vggtext/annotation_train.txt'
trans_dir = '/home/paile/research/vggtext'

with open(anno_pth) as f:
    lines = f.readlines()
    lines = [path.normpath(path.join(image_dir, l.split()[0])) for l in lines]

labels = [l.split('_')[1] for l in lines]
trans = [' '.join(z)+'\n' for z in zip(lines, labels)]

train_trans = random.sample(trans, 100000)
test_trans = random.sample(trans, 1000)

with open(path.join(trans_dir, 'train_10w.txt'), 'w') as f:
    f.writelines(train_trans)

with open(path.join(trans_dir, 'test_10w.txt'), 'w') as f:
    f.writelines(test_trans)

print 'done.'