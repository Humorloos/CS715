import re

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from dateutil.utils import today
from matplotlib import pyplot as plt

from constants import DATA_DIR, LIFE_SCIENCES_TARGET_DIR, PROJECT_DIR
from utils import load_metadata_json

#%%

with open(DATA_DIR / "NCBO BioPortal.html", 'r', encoding='utf8') as file_in:
    bioportal_soup = BeautifulSoup(file_in.read())

ontologies = pd.DataFrame(
    {'tag': bioportal_soup.find_all('div', attrs={'class': 'ontology'})})


def get_ontology_name(tag):
    name_tag = tag.find('a', attrs={'class': 'ng-binding'})
    if name_tag is not None:
        return re.sub(r'\n|(\s{2,})', '', name_tag.text)
    return None


ontologies['name'] = ontologies['tag'].apply(lambda tag: get_ontology_name(tag))


def get_ontology_last_update(tag):
    update_tag = tag.find('b', text='Uploaded')
    if update_tag is not None:
        return re.sub(r'\n|\s|:', '', update_tag.next_sibling)
    return None


ontologies['last_update'] = ontologies['tag'].apply(
    lambda tag: get_ontology_last_update(tag)).astype('datetime64')


def get_ontology_n_classes(tag):
    n_classes_tag = tag.find('div', attrs={'class': 'badge_count'})
    if n_classes_tag is not None:
        return int(n_classes_tag.text.replace(',', ''))
    return np.nan


ontologies['Number of classes in dataset'] = ontologies['tag'].apply(
    lambda tag: get_ontology_n_classes(tag))

ontologies['Years since last update'] = \
    (today() - ontologies['last_update']).dt.days / 365

ontologies['abbreviation'] = \
    'bioportal-' + \
    ontologies['name'].str.extract(r'\(([^)]+)\)$').iloc[:, 0].str.lower()  #
ontologies['title'] = \
    ontologies['name'].str.extract(r'^(.*) \([^)]+\)$').iloc[:, 0]
#%%

accessibility_data = \
    pd.read_csv(LIFE_SCIENCES_TARGET_DIR / 'accessibility.csv', ) \
        .rename(columns={'Unnamed: 0': 'id'})
metadata_json = load_metadata_json('2021-08-14')
accessibility_data['name'] = accessibility_data['id'] \
    .apply(lambda s: metadata_json[s]['title'])
accessibility_data['is_bioportal'] = \
    accessibility_data['id'].str.startswith('bioportal')

bioportal_ontos = accessibility_data.loc[accessibility_data['is_bioportal']]
bioportal_ontos_matched_by_title = bioportal_ontos['name'].isin(
    ontologies['title'])
asdf = bioportal_ontos.loc[~bioportal_ontos_matched_by_title]
bioportal_ontos_matched_by_title.sum()

bioportal_ontos_matched_by_abbreviation = \
    bioportal_ontos['id'].isin(ontologies['abbreviation'])
bioportal_ontos_matched_by_abbreviation.sum()
len(bioportal_ontos_matched_by_abbreviation)

bioportal_ontos.iloc[:, range(1, 4)].sum()

# none of the bioportal ontologies are accessible via lod cloud metadata
fdsa = bioportal_ontos.loc[bioportal_ontos_matched_by_abbreviation]

#%%

ontologies.plot.scatter('Years since last update', 'Number of classes in dataset')
plt.yscale('log')
plt.savefig(PROJECT_DIR / 'thesis' / 'figures' / 'bio-portal-maintenance.png')
plt.show()

#%%


ontologies[['Years since last update', 'Number of classes in dataset']].corr()
tag = ontologies['tag'].iloc[5]
tag.next_sibling
#%%
