#!/usr/bin/env python
import numpy as np 
import matplotlib.pyplot as plt

"""
train5: 32
train6: 64
train: 128
train4: 32, 32
train3: 64, 64
train2: 128, 128
"""
log_dir = '/home/paile/Desktop/chars/pipeline/rnn/data/vgg_nin/'

# label, color, log_pth
notations = (
    ('1L_32', 'y', log_dir+'train5@2016.01.06-16.29.39.488182.log'),
    ('1L_64', 'g', log_dir+'train6@2016.01.06-16.31.13.769064.log'),
    ('1L_128','b', log_dir+'train@2016.01.06-13.26.24.580487.log'),
    ('2L_32,32', 'c', log_dir+'train4@2016.01.06-16.22.20.734223.log'),
    ('2L_64,64', 'm', log_dir+'train3@2016.01.06-16.21.15.950762.log'),
    ('2L_128,128', 'r', log_dir+'train2@2016.01.06-16.03.12.255743.log')
)

def parse_log(log_pth):
    with open(log_pth) as f:
        lines = f.readlines()
        lines = [l.strip() for l in lines]

    for i, l in enumerate(lines):
        if l.find('training...') == 0:
            idx_beg = i
        if l.find('training finished') == 0:
            idx_end = i
    best = lines[idx_end:]
    lines = lines[idx_beg:idx_end]

    best_epoch = []
    for l in best:
        if l.find('epoch ') == 0:
            best_epoch.append(int(l.split()[1]))
    best_epoch = best_epoch[1]

    errors = []
    for l in lines:
        if l.find('seqError ') == 0:
            errors.append(float(l.split()[1][:-1]))
    errors = np.array(errors).reshape((-1, 2)) * 0.7
    errors[2:] = errors[2:]
    train_err = errors[:, 0] 
    valid_err = errors[:, 1] 
    return train_err, valid_err, best_epoch

N = 50
for lab, col, log in notations:
    tr_err, val_err, best_epoch = parse_log(log)
    tr_err = tr_err[:N]
    val_err= val_err[:N]
    plt.plot(val_err, col+'--', linewidth=2)
    plt.plot(tr_err,  col, label=lab, linewidth=2)
    # if best_epoch > N:
    #     best_epoch = N-5
    # plt.plot([best_epoch, best_epoch], [5, 75], col+'--', linewidth=1)
    
plt.legend()
plt.xlabel('training iteration')
plt.ylabel('sequence error (%)')
plt.ylim([5, 75])
# plt.legend(loc='upper right', shadow=True)
# plt.show()
plt.savefig('rnn_layers.pdf')
print 'done.'