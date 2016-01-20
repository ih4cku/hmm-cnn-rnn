from os import path
from glob import glob

def getFrameFiles(frames_dir, ext='jpg'):
    """
    Get frame images from `frames_dir`, sort with their filenames.
    """
    imlist = glob(path.join(frames_dir, '*.'+ext))
    imlist.sort(key=lambda fn: int(path.splitext(path.basename(fn))[0]))
    return imlist
