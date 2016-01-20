#!/usr/bin/env python
import untangle
from os import path

img_dir = '/home/paile/research/icdar2003'
xml_pth = '/home/paile/research/icdar2003/word.xml'
xml_obj = untangle.parse(xml_pth)

im_list = xml_obj.imagelist.image
trans = [path.join(img_dir, e['file'])+' '+e['tag'].lower()+'\n' for e in im_list]
lines = [l.encode('utf-8') for l in trans]
with open('ic03_trans.txt', 'w') as f:
    f.writelines(lines)
print 'done.'
