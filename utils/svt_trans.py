#!/usr/bin/env python
import untangle 
import cv2
import sys
import os
from os import path

def cropRect(im, rect):
    x = int(rect['x'])
    y = int(rect['y'])
    wid = int(rect['width'])
    hei = int(rect['height'])

    return im[y:y+hei, x:x+wid, ...]

def processXLM(xml_pth, image_out_dir, label_out_pth):
    xml_obj = untangle.parse(xml_pth)
    label_lines = []
    for image in xml_obj.tagset.image:
        im_pth = path.join(svt_root_dir, image.imageName.cdata)
        im_basename = path.splitext(path.basename(im_pth))[0]
        im = cv2.imread(im_pth)
        for i, tagged_rect in enumerate(image.taggedRectangles.taggedRectangle):
            word = tagged_rect.tag.cdata
            im_rect_pth = path.join(image_out_dir, '%s_%d.png' % (im_basename, i))
            im_word = cropRect(im, tagged_rect)
            if not path.isdir(image_out_dir):
                os.makedirs(image_out_dir)
            cv2.imwrite(im_rect_pth, im_word)
            print im_rect_pth, im_word.shape
            label_lines.append(im_rect_pth+' '+word+'\n')
    with open(label_out_pth, 'w') as f:
        f.writelines(label_lines)
    print xml_pth, 'done.'

        
svt_root_dir = '/home/paile/research/svt/svt1'
image_out_dir = '/home/paile/research/svt/svt1/words'

processXLM('train.xml', path.join(image_out_dir, 'train'), path.join(image_out_dir, 'train.txt'))
processXLM('test.xml',  path.join(image_out_dir, 'test'),  path.join(image_out_dir, 'test.txt'))