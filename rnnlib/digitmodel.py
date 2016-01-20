import caffe
from caffe.proto import caffe_pb2
import cv2
from os import path
import numpy as np
import cPickle
import time
from ConfigParser import SafeConfigParser

def chunks(l, n):
    """ 
    Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        print 'chunk [%d/%d]' % (i, len(l))
        yield l[i:i+n]

class DigitNet(object):
    """
    Get root model dir from 'config.ini'

    Model parameters:
        arch_file    = 'models/deploy.prototxt'
        weights_file = 'weights/last.caffemodel'
        mean_file    = 'data/mean.binaryproto'
        names_file   = 'lists/cls_names.pickle'
    """
    def __init__(self):
        conf = SafeConfigParser()
        conf.read(path.join(path.dirname(__file__), 'config.ini'))
        model_dir = conf.get('cnn', 'model_dir')

        arch_file    = path.join(model_dir, 'models/deploy.prototxt')
        weights_file = path.join(model_dir, 'weights/last.caffemodel')
        # mean_file    = path.join(model_dir, 'data/mean.binaryproto')
        # names_file   = path.join(model_dir, 'lists/cls_names.pickle')

        # with open(names_file, 'rb') as f:
            # self.cls_names = cPickle.load(f)
        caffe.set_mode_gpu()
        # self.mean = self.loadMean(mean_file)
        self.net = caffe.Net(arch_file, weights_file, caffe.TEST)
        # (N, K, H, W)
        self.input_shape = self.net.blobs[self.net.inputs[0]].data.shape

    @staticmethod
    def loadMean(mean_file):
        blob = caffe_pb2.BlobProto()
        with open(mean_file, 'rb') as f:
            s = f.read()
        blob.ParseFromString(s)
        mean = caffe.io.blobproto_to_array(blob).astype('float32')
        return mean

    def readImage(self, imfn):
        """
        Read gray image, data range [0, 255], type is 'float32'.

        Parameter:
            adjust - hist equalize
        """
        im = cv2.imread(imfn, 0)
        im = cv2.resize(im, self.input_shape[2:])
        im = im.astype('float32')
        return im

    def predict(self, imlist, adjust=False):
        """
        predict image and return top k category index
        """
        # read 100 images to memory each time
        _t = time.time()
        predictions = []
        for imfns in chunks(imlist, 100):
            predictions.append(self.getBlobs(imlist)['prob'])
        elapse = time.time() - _t
        print 'Prediction done in %f seconds.' % elapse

        predictions = np.vstack(predictions)
        return predictions

    def getBlobs(self, imlist, blobs=[]):
        caffe_in = np.asarray([self.readImage(fn) for fn in imlist])
        caffe_in = caffe_in[:, None, :, :] # (N, K, H, W)
        # caffe_in -= self.mean
        outputs = self.net.forward_all(blobs, **{self.net.inputs[0]: caffe_in})
        return outputs
