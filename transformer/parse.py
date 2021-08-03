# functions for parsing files and dates

import numpy as np
import pandas as pd
from pathlib import Path
import datefinder
import re



def is_column_text(column: pd.Series) -> bool:
    """
    Check if a column is a string column.

    Args:
        dataframe (pd.Series): the column to check
    
    Returns:
        bool: True if the column is a string column, False otherwise
    """
    # check column dtype
    if column.dtype != 'object' or column.dtype != 'str':
        return False

    # check for 'id' in the column name
    if 'id' in column.name.lower():
        return False

    # check if at least some values are strings
    if not any(isinstance(x, str) for x in column):
        return False

    # check if column is filled with nans
    clean = column.dropna()
    clean = clean.str.strip()
    clean = clean[clean.str.lower() != 'nan']
    clean = clean[clean != '']
    if len(clean) == 0:
        return False

    # check if values are id-like
    if all(isinstance(x, str) for x in column):
        clean_sample = clean.sample(n=min(10, len(clean)))
        max_words = clean_sample.apply(lambda x: len(x.split(' '))).max()
        contains_numbers = clean_sample.str.contains(r'\d', regex=True).any()
        contains_lowercase = clean_sample.str.contains(
            r'[a-z]', regex=True).any()
        contains_punctuation = clean_sample.str.contains(
            r'[^\w\s]', regex=True).any()
        if (max_words == 1) and not contains_punctuation and (contains_numbers or not contains_lowercase):
            return False

    # otherwise, this is a text column
    return True




def is_column_time(column: pd.Series) -> bool:
    """
    Check if a column is a datetime or timedelta column.
    
    Args:
        column (pd.Series): the column to check
    
    Returns:
        bool: True if the column is a datetime or timedelta column, False otherwise
    """
    return 'time' in str(column.dtype)


def is_column_numeric(column: pd.Series) -> bool:
    """
    Check if a column is a numeric column.
    
    Args:
        column (pd.Series): the column to check
    
    Returns:
        bool: True if the column is a numeric column, False otherwise
    """
    try:
        return np.issubdtype(column.dtype, np.number)
    except Exception:
        return False


def has_time_information(x) -> bool:
    """
    Check if x has time information.
    """
    if type(x) == pd.Series:
        return has_time_information(x.iloc[0])
    if re.search(r'00:00:00', str(x)):
        return False
    else:
        return re.search(r'\d{2}:\d{2}', str(x))


__base_date = pd.to_datetime('1950-01-01')
def parse_datetime(date_str: str) -> pd.Timestamp:
    """
    Automatically determine the date format of a string.

    Args:
        date_str (str): string of datetime to parse

    Returns:
        pandas.Timestamp: a parsed timestamp
    """
    matches = datefinder.find_dates(date_str, base_date=__base_date)
    date_matched = next(matches)
    # return timedelta if the date matches the __base_date
    if date_matched.date() == __base_date:
        return date_matched - __base_date
    # otherwise, return the datetime matched
    else:
        return date_matched



def parse_datetime_column(column: pd.Series) -> pd.Series:
    """
    Parse a column of strings to a column of pd.Timestamp or pd.Timedelta.

    Args:
        column (pd.Series): a column of strings to parse

    Returns:
        pd.Series: a column of pd.Timestamp or pd.Timedelta.
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
    folder_path = filepath.rsplit('/', 1)[0]
    Path(folder_path).mkdir(parents=True, exist_ok=True)
    # saves the dataframe to a file based on the filetype
    if filepath.endswith('.csv'):
        dataframe.to_csv(filepath, index=False, **kwargs)
    elif filepath.endswith('.json'):
        dataframe.to_json(filepath, index=False, **kwargs)
    elif filepath.endswith('.xlsx'):
        dataframe.to_excel(filepath, index=False, **kwargs)
    else:
        raise ValueError('Unknown filetype')




