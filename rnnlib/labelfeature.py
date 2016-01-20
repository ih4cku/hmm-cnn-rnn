import numpy as np
import cv2
from digitmodel import DigitNet

# label getters

def getLabellings(label_fn):
    """
    label file format:
        Each line has a directory path containing frame images followed by 
        the labelling of the sequence separated by a space.
        e.g. "train/19 222"
    
    return:
        (frames_dir, labels)
        e.g. ("train/19", "2 2 2") 
    """
    with open(label_fn) as f:
        labellings = f.read().strip().split('\n')
    labellings = [l.strip().split() for l in labellings]
    labellings = [(frms_dir, ' '.join(list(lab))) for frms_dir, lab in labellings]
    return labellings

# feature getters

def getRawFeatures(imlist):
    """
    `features` shape: (N, D)
    """
    features = np.asarray([cv2.imread(fn, 0).flatten() for fn in imlist])
    return features

def CnnFeatureFactory():
    """
    `features` shape: (N, D)
    use closure to hold the CNN net.
    """
    net = DigitNet()
    def getCnnFeatures(imlist):
        features = net.getBlobs(imlist, ['ip1'])['ip1']
        assert len(features.shape) == 2, 'ip1 blob shape: %s' % (repr(features.shape),)
        return features
    return getCnnFeatures


def NinFeatureFactory():
    """
    `features` shape: (N, D)
    use closure to hold the CNN net.
    """
    net = DigitNet()
    def getCnnFeatures(imlist):
        features = net.getBlobs(imlist, ['pool3'])['pool3']
        assert features.shape[2]==1 and features.shape[3]==1, \
            'features.shape=' + repr(features.shape)
        features = features[..., 0, 0]
        return features
    return getCnnFeatures

