import pandas as pd
from matplotlib import pyplot as plt

from constants import LIFE_SCIENCES_TARGET_DIR
#%%

accessibility_data = \
    pd.read_csv(LIFE_SCIENCES_TARGET_DIR / 'accessibility.csv', ) \
        .rename(columns={'Unnamed: 0': 'id', 'voID': 'VoID'}).set_index('id')

accessibility_data['n_accessible'] = accessibility_data.sum(1)
accessibility_data['More than 1\nDiscoverability\nEntry'] = accessibility_data['n_accessible'] > 1
accessibility_data['None'] = accessibility_data['n_accessible'] == 0
accessibility_plot_data = accessibility_data.drop(columns='n_accessible').sum()

#%%

fig = plt.gcf()
fig.set_size_inches(4, 4)
ax = accessibility_plot_data.plot.bar(width=0.8)
ax.set_axisbelow(True)
ax.set_facecolor('lavender')
ax.grid(color='white')
plt.tight_layout()
plt.savefig(LIFE_SCIENCES_TARGET_DIR / 'accessibility.png')
#%%
asdf = accessibility_data.sum(1)
accessibility_data.iloc[0].sum()