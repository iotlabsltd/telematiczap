# functions for parsing files and dates

import numpy as np
import pandas as pd
import os
import datefinder
from pandas.api.types import is_datetime64_any_dtype, is_timedelta64_dtype



__base_date = pd.to_datetime('1950-01-01')
def parse_datetime(date_str: str) -> pd.Timestamp:
    """
    Automatically determine the date format of a string.

    Args:
        date_str (str): string of datetime to parse

    Returns:
        pandas.Timestamp or datetime.time
    """
    matches = datefinder.find_dates(date_str, base_date=__base_date)
    date_matched = next(matches)
    # return datetime.time if the date matches the __base_date
    if date_matched.date() == __base_date:
        return date_matched.time()
    # otherwise, return the datetime matched
    else:
        return date_matched



def parse_datetime_column(column: pd.Series) -> pd.Series:
    """
    Parse a column of strings to a column of pd.Timestamp or datetime.time.

    Args:
        column (pd.Series): a column of strings to parse

    Returns:
        pd.Series: a column of pd.Timestamp or datetime.time.
    """
    # if column is all nans, return column
    if column.isnull().all():
        return column
    # try to parse the column
    try:
        return column.apply(parse_datetime)
    # if parsing fails, return the column
    except Exception:
        return column



def read_dataframe(filepath_or_buffer: str, **kwargs) -> pd.DataFrame:
    """
    Finds the appropriate pandas read function for the filetype.

    Args:
        filepath_or_buffer (str): path to the file to read
        **kwargs: any other arguments to pass to the pandas read function
    
    Returns:
        pandas.DataFrame: dataframe read from the file
    """
    if filepath_or_buffer.endswith('.csv'):
        
        df = pd.read_csv(filepath_or_buffer, date_parser=parse_datetime, infer_datetime_format=True, **kwargs)
    elif filepath_or_buffer.endswith('.tsv'):
        df = pd.read_csv(filepath_or_buffer, sep='\t', date_parser=parse_datetime, infer_datetime_format=True, **kwargs)
    elif filepath_or_buffer.endswith('.xlsx') or filepath_or_buffer.endswith('.xls'):
        df = pd.read_excel(filepath_or_buffer, date_parser=parse_datetime, **kwargs)
    elif filepath_or_buffer.endswith('.json'):
        df = pd.read_json(filepath_or_buffer, date_parser=parse_datetime, infer_datetime_format=True, **kwargs)
    elif filepath_or_buffer.endswith('.h5'):
        df = pd.read_hdf(filepath_or_buffer, date_parser=parse_datetime, infer_datetime_format=True, **kwargs)
    elif filepath_or_buffer.endswith('.feather'):
        df = pd.read_feather(filepath_or_buffer, date_parser=parse_datetime, infer_datetime_format=True, **kwargs)
    else:
        raise ValueError('File format not supported')
    
    # fix wrong date and time formats
    df = df.apply(parse_datetime_column, axis=0)
    return df


def save_dataframe(dataframe: pd.DataFrame, filepath: str, **kwargs):
    """
    Save a dataframe to a file.

    Args:
        dataframe (pandas.DataFrame): dataframe to save
        filepath (str): path to the output file
        **kwargs: any other arguments to pass to the pandas save function
    """
    # create the folders if they don't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    # saves the dataframe to a file based on the filetype
    if filepath.endswith('.csv'):
        dataframe.to_csv(filepath, index=False, **kwargs)
    elif filepath.endswith('.json'):
        dataframe.to_json(filepath, index=False, **kwargs)
    elif filepath.endswith('.xlsx'):
        dataframe.to_excel(filepath, index=False, **kwargs)
    else:
        raise ValueError('Unknown filetype')




