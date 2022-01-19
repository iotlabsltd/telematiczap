# %%
from transformer import TelematicZapTransformer
import pandas as pd

# %%
before_df = pd.read_excel('data/before/example-dataset2.xls')
before_df

# %%
format_df = pd.read_csv('data/format/format-example-trips.csv')
format_df

# %%
model = TelematicZapTransformer()
after_df = model.transform(before_df, format_df)
after_df

# %%
after_df.to_csv('data/after/transformed-dataset2.csv', index=False)


