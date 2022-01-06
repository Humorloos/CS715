import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from constants import TARGET_DIR
from utils import load_metadata_json

# matplotlib.use('qt5agg')

capture_ids = ['20201028151938', '20210814083458', '20200513021311', '20190320210945', '20180628150210', ]
# responses = [requests.get(f'https://web.archive.org/web/{capture_id}/https://lod-cloud.net/lod-data.json') for
#              capture_id in capture_ids]
# texts = [response.text for response in responses]
dates = pd.Series(capture_ids).astype("datetime64").dt.date

# for text, date_string in zip(texts, dates.astype(str).values):
#     with open(DATA_DIR.joinpath(f'metadata_{date_string}.json'), 'w') as file_out:
#         file_out.write(text)

metadata_dicts = {}

for date in dates.astype(str):
    metadata_dicts[date] = load_metadata_json(date)

data = pd.DataFrame([[len(metadata_dict) for metadata_dict in metadata_dicts.values()]],
                    columns=metadata_dicts.keys(), index=['total']).T
metadata = pd.Series(metadata_dicts).apply(lambda metadata_dict: pd.DataFrame(metadata_dict))

domains = [col.lower().replace(' ', '_') for col in
           ["Media", "Government", "Publications", "Geography", "Life Sciences", "Cross domain", "User generated",
            "Social Networking", "Total"]]
schmachtenberg_data = {'2014-04-15': [24, 199, 138, 27, 85, 47, 51, 520, 1091],
                       '2011-09-15': [25, 49, 87, 31, 41, 41, 20, 0, 294]}
schmachtenberg_df = pd.DataFrame(schmachtenberg_data, index=domains).T
schmachtenberg_df['linguistics'] = 0

data_2021 = metadata.apply(lambda df: df.loc['domain'].value_counts().drop(['']).T)
data_2021['total'] = data_2021.sum(1)

data_combined = data_2021.append(schmachtenberg_df)
data_combined.index = data_combined.index.astype('datetime64[ns]')

data_combined.drop(columns='total').plot().get_figure().savefig(
    TARGET_DIR.joinpath(f'development_lod-cloud_size_by_domain.png'))
