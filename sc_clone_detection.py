from collections import Counter
import json
import random
import re
import time
from pygments.lexers.jvm import JavaLexer
from pygments.token import Comment
from bleu_ignoring import corpus_bleu, SmoothingFunction
from CodeBLEU.code_bleu import code_bleu
from nltk.util import ngrams
import numpy as np

def print_results(tl, bl, cl):
    print('BLEU:')
    TP = ((bl == 1) & (tl == 1)).sum()
    FP = ((bl == 1) & (tl == 0)).sum()
    FN = ((bl == 0) & (tl == 1)).sum()
    TN = ((bl == 0) & (tl == 0)).sum()
    print(f'    TP: {TP}, FP: {FP}, TN: {TN}, FN: {FN}')
    print(f'    Accuracy: {(TP + TN)/(TP+TN+FP+FN)}')
    print(f'    Precision: {TP/(TP+FP)}')
    print(f'    Recall: {TP/(TP+FN)}')
    print(f'    F1: {(2*TP)/(2*TP + FP + FN)}')
    print()
    print('CrystalBLEU:')
    TP = ((cl == 1) & (tl == 1)).sum()
    FP = ((cl == 1) & (tl == 0)).sum()
    FN = ((cl == 0) & (tl == 1)).sum()
    TN = ((cl == 0) & (tl == 0)).sum()
    print(f'    TP: {TP}, FP: {FP}, TN: {TN}, FN: {FN}')
    print(f'    Accuracy: {(TP + TN)/(TP+TN+FP+FN)}')
    print(f'    Precision: {TP/(TP+FP)}')
    print(f'    Recall: {TP/(TP+FN)}')
    print(f'    F1: {(2*TP)/(2*TP + FP + FN)}')

sm_func = SmoothingFunction(epsilon=0.0001).method1

lexer = JavaLexer()
code = {}
with open('sc_clone/data.jsonl') as f:
    tmp = f.read().split('\n')

all_ngrams = Counter()

for j in tmp:
    try:
        this = json.loads(j)
        tok = [i[1] for i in lexer.get_tokens(this['func']) if not (re.fullmatch('\s+', i[1]) or (i[0] in Comment))]
        code[this['idx']] = tok
        if random.random() < 0.3:
            for i in range(1, 5):
                all_ngrams += Counter(ngrams(tok, i))
    except:
        break

most_common_dict = dict(all_ngrams.most_common(500))

print(len(code.items()))

with open('sc_clone/test.txt') as f:
    tmp = f.read().split('\n')

blues = [[], []]
crystals = [[], []]
for j in tmp[:3000]:
    x = re.split('\s+', j)
    if len(x) == 3:
        c1, c2, label = x
        # if (c1 not in code) or (c2 not in code):
        #     continue
        code1 = code[c1]
        code2 = code[c2]
        bleuscore = corpus_bleu([[code1]], [code2], smoothing_function=sm_func)
        crystalbleuscore = corpus_bleu([[code1]], [code2], smoothing_function=sm_func, ignoring=most_common_dict)
        blues[int(label)].append(bleuscore)
        crystals[int(label)].append(crystalbleuscore)

f_b = np.mean(blues[0])
t_b = np.mean(blues[1])
f_c = np.mean(crystals[0])
t_c = np.mean(crystals[1])

th_b = (f_b + t_b)/2
th_c = (f_c + t_c)/2

print(f_b, t_b, th_b)
print(f_c, t_c, th_c)

true_label = []
bleu_label = []
crystal_label = []

intra_h = []
intra_r = []
inter_h = []
inter_r = []

bs = [[], []]
cs = [[], []]

for j in tmp[3000:30000]:
    x = re.split('\s+', j)
    if len(x) == 3:
        c1, c2, label = x
        # if (c1 not in code) or (c2 not in code):
        #     continue
        # if label == '0' and random.random() < 0.9:
        #     continue
        code1 = code[c1]
        code2 = code[c2]
        if int(label) == 0:
            inter_h.append(code2)
            inter_r.append([code1])
        else:
            intra_h.append(code2)
            intra_r.append([code1])
        bleuscore = corpus_bleu([[code1]], [code2], smoothing_function=sm_func)
        bs[int(label)].append(bleuscore)
        crystalbleuscore = corpus_bleu([[code1]], [code2], smoothing_function=sm_func, ignoring=most_common_dict)
        cs[int(label)].append(crystalbleuscore)
        l_b = 1 if bleuscore > th_b else 0
        l_c = 1 if crystalbleuscore > th_c else 0
        bleu_label.append(l_b)
        crystal_label.append(l_c)
        true_label.append(int(label))


with open('sc_clone_scores.npy', 'wb') as f:
    np.save(f, np.array(bs[0]))
    np.save(f, np.array(bs[1]))
    np.save(f, np.array(cs[0]))
    np.save(f, np.array(cs[1]))
print_results(np.array(true_label), np.array(bleu_label), np.array(crystal_label))


print(len(inter_h), len(intra_h))
print('BLEU inter')
start_time = time.process_time()
bleu_inter = corpus_bleu(inter_r, inter_h, smoothing_function=sm_func)
print(time.process_time() - start_time)
print('BLEU intra')
start_time = time.process_time()
bleu_intra = corpus_bleu(intra_r, intra_h, smoothing_function=sm_func)
print(time.process_time() - start_time)
print('CrystalBLEU inter')
start_time = time.process_time()
crystal_inter = corpus_bleu(inter_r, inter_h, smoothing_function=sm_func, ignoring=most_common_dict)
print(time.process_time() - start_time)
print('CrystalBLEU intra')
start_time = time.process_time()
crystal_intra = corpus_bleu(intra_r, intra_h, smoothing_function=sm_func, ignoring=most_common_dict)
print(time.process_time() - start_time)
print('CodeBLEU inter')
start_time = time.process_time()
code_inter = code_bleu(inter_r, inter_h)
print(time.process_time() - start_time)
print('codeBLEU intra')
start_time = time.process_time()
code_intra = code_bleu(intra_r, intra_h)
print(time.process_time() - start_time)

print(f'BLEU distinguishability = {bleu_intra/bleu_inter}')
print(f'CrystalBLEU distinguishability = {crystal_intra/crystal_inter}')