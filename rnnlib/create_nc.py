#!/usr/bin/env python
import netcdf_helpers
import numpy as np 
import os
from os import path
import sys
import cPickle
from glob import glob
import gflags
import labelfeature
import utils
import config
import joblib

FLAGS = gflags.FLAGS
gflags.DEFINE_string('mean_std', None, 'pickle file containing mean and std.')

def parse_args():
    try:
        args = gflags.FLAGS(sys.argv)
    except gflags.FlagsError, errmsg:
        print errmsg
        print '\nFlags:'
        print gflags.FLAGS
        sys.exit(-1)
    return args[1:]


class NcCreator(object):
    def __init__(self, labels, featureReader):
        """
        featureReader: handle of feature reading function
        """
        self.label_fn = None
        self.sequences = []
        self.targetStrings = []
        self.seqTags = []
        self.labels = labels
        self.getFeatures = featureReader

    @staticmethod
    def uniqueLabels(labellings):
        labels = []
        for tag, lab in labellings:
            labels.extend(lab.split())
        return sorted(set(labels))

    @staticmethod
    def normalize(inputs, mean_path):
        print 'Normalizing...',
        if FLAGS.mean_std is None:
            # create mean_std.pickle
            mean = np.mean(inputs, axis=0)
            std = np.std(inputs, axis=0)
            with open(mean_path, 'wb') as f:
                cPickle.dump((mean, std), f, -1)
            print 'Mean and std are dumped to %s.' % mean_path
        else:
            # load mean_std.pickle 
            print 'Loading mean and std from %s' % FLAGS.mean_std
            with open(FLAGS.mean_std, 'rb') as f:
                mean, std = cPickle.load(f)
        inputs = (inputs - mean)/std
        print 'done.'
        return inputs

    def load(self, split):
        # labellings: (frm_dir, 'abc')
        frames_info = joblib.load(split.frames_info_pth)

        # read frame images
        for samp_id in frames_info:
            print 'Reading', path.join(split.frames_dir, samp_id)
            frame_list = [path.join(split.frames_dir, samp_id, l) for l in frames_info[samp_id]['frames']]
            trans = frames_info[samp_id]['trans'].lower()
            print 'Trans:', trans, len(frame_list), 'frames'
            b_ignore = False
            if set(trans) - set(self.labels):
                print 'warning: contain outlier labels:', trans
                continue
            if len(frame_list) < len(trans)+1:
                print 'warning: too few frames %d vs %d, ignore' % (len(frame_list), len(trans))
                continue
            frame_data = self.getFeatures(frame_list)

            assert len(frame_list) == len(frame_data), \
                '%s vs %s' % (len(frame_list), len(frame_data))
            self.sequences.append(frame_data)
            self.targetStrings.append(' '.join(list(trans)))
            self.seqTags.append(samp_id)

    def save(self, ncFilename):
        seqLengths = np.array([seq.shape[0] for seq in self.sequences], dtype='int32')
        seqDims = seqLengths[:, None]
        inputs = np.vstack(self.sequences).astype('float32')

        print '---------------------------------------'
        if config.RNN_NORM:
            default_mean_std = path.join(path.dirname(ncFilename), 'mean_std.pickle')
            inputs = self.normalize(inputs, default_mean_std)

        #create a new .nc file
        f = netcdf_helpers.NetCDFFile(ncFilename, 'w')

        #create the dimensions
        netcdf_helpers.createNcDim(f,'numSeqs',len(seqLengths))
        netcdf_helpers.createNcDim(f,'numTimesteps',len(inputs))
        netcdf_helpers.createNcDim(f,'inputPattSize',len(inputs[0]))
        netcdf_helpers.createNcDim(f,'numDims',1)
        netcdf_helpers.createNcDim(f,'numLabels',len(self.labels))

        #create the variables
        netcdf_helpers.createNcStrings(f,'seqTags',self.seqTags,('numSeqs','maxSeqTagLength'),'sequence tags')
        netcdf_helpers.createNcStrings(f,'labels',self.labels,('numLabels','maxLabelLength'),'labels')
        netcdf_helpers.createNcStrings(f,'targetStrings',self.targetStrings,('numSeqs','maxTargStringLength'),'target strings')
        netcdf_helpers.createNcVar(f,'seqLengths',seqLengths,'i',('numSeqs',),'sequence lengths')
        netcdf_helpers.createNcVar(f,'seqDims',seqDims,'i',('numSeqs','numDims'),'sequence dimensions')
        netcdf_helpers.createNcVar(f,'inputs',inputs,'f',('numTimesteps','inputPattSize'),'input patterns')

        #write the data to disk
        print 'closing file', ncFilename
        f.close()

if __name__ == '__main__':
    args = parse_args()
    if len(args) != 2:
        print 'Usage: %s split_name nc_file' % sys.argv[0]
        print gflags.FLAGS
        sys.exit(1)

    split_name = args[0]
    nc_file = args[1]

    labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    # labels = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    ncc = NcCreator(labels, labelfeature.NinFeatureFactory())
    ncc.load(config.splits[split_name])
    ncc.save(nc_file)