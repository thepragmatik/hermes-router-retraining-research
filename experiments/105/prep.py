import pandas as pd, numpy as np
wt = pd.read_parquet('/Users/rath/transfer-bundle/analysis/winrate_table.parquet')
print(wt['split'].value_counts())
tr = wt[wt['split'] == 'train']
print('train rows', len(tr))
probs = np.load('results/v1_train_probs.npy')
print('probs', probs.shape)
sc = tr['strong_correct'].values
wc = tr['weak_correct'].values
unacc = ((wc == 0) & (sc == 1)).astype(int)
print('weak wrong frac:', (wc == 0).mean(), 'risk (weak wrong & strong right):', unacc.mean())
np.save('/tmp/v1p.npy', probs)
np.save('/tmp/sc.npy', sc.astype(np.int8))
np.save('/tmp/wc.npy', wc.astype(np.int8))
np.save('/tmp/unacc.npy', unacc.astype(np.int8))
np.save('/tmp/cost_s.npy', tr['cost_s'].values)
np.save('/tmp/cost_w.npy', tr['cost_w'].values)
np.save('/tmp/eval_name.npy', tr['eval_name'].values.astype('U'))
print('saved')
