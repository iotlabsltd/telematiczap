# %%
# imports
from transformer import TelematicZapTransformer
import pandas as pd

# %%
# training dataset
before_datasets=[
    pd.read_csv('data/before/dataset1.csv', encoding="ISO-8859-1"),
    pd.read_excel('data/before/dataset2.xls'),
    pd.read_excel('data/before/dataset2.xls'),
    pd.read_excel('data/before/dataset3.xlsx'),
    pd.read_excel('data/before/dataset3.xlsx'),
    pd.read_excel('data/before/dataset4.xls'),
    pd.read_excel('data/before/dataset4.xls'),
    pd.read_excel('data/before/dataset5.xlsx', sheet_name='Trips'),
    pd.read_excel('data/before/dataset5.xlsx'),
    pd.read_excel('data/before/dataset6.xls'),
    pd.read_excel('data/before/dataset6.xls'),
]
formats_examples=[
    pd.read_csv('data/format/konetik_vehicles.csv'),
    pd.read_csv('data/format/konetik_trips.csv'),
    pd.read_csv('data/format/konetik_vehicles.csv'),
    pd.read_csv('data/format/konetik_trips.csv'),
    pd.read_csv('data/format/konetik_vehicles.csv'),
    pd.read_csv('data/format/konetik_trips.csv'),
    pd.read_csv('data/format/konetik_vehicles.csv'),
    pd.read_csv('data/format/konetik_trips.csv'),
    pd.read_csv('data/format/konetik_vehicles.csv'),
    pd.read_csv('data/format/konetik_trips.csv'),
    pd.read_csv('data/format/konetik_vehicles.csv'),
]
after_datasets=[
    pd.read_csv('data/target/dataset1_vehicles.csv'),
    pd.read_csv('data/target/dataset2_trips.csv'),
    pd.read_csv('data/target/dataset2_vehicles.csv'),
    pd.read_csv('data/target/dataset3_trips.csv'),
    pd.read_csv('data/target/dataset3_vehicles.csv'),
    pd.read_csv('data/target/dataset4_trips.csv'),
    pd.read_csv('data/target/dataset4_vehicles.csv'),
    pd.read_csv('data/target/dataset5_trips.csv'),
    pd.read_csv('data/target/dataset5_vehicles.csv'),
    pd.read_csv('data/target/dataset6_trips.csv'),
    pd.read_csv('data/target/dataset6_vehicles.csv'),
]

# %%
# parameter optimization using optuna
model = TelematicZapTransformer()
model.fit(before_datasets, formats_examples, after_datasets)
print(model.params)
