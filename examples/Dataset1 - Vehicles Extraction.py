# %%
from transformer import TelematicZapTransformer
import pandas as pd

# %%
before_df = pd.read_csv('data/before/example-dataset1.csv')
before_df

# %%
format_df = pd.read_csv('data/format/format-example-vehicles.csv')
format_df

# %%
model = TelematicZapTransformer()
after_df = model.transform(before_df, format_df)
after_df

# %%
after_df.to_csv('data/after/transformed-dataset1.csv', index=False)


