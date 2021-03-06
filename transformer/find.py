# functions for finding stuff in dataframes

import pandas as pd
import numpy as np
from .similarity import similarity_str, similarity_columns, is_column_text, is_time, is_date, count_columns_with_dates
from .io import parse_datetime_column
from datetime import time
import geopy


def find_location(address: str, geolocator=None):    
    geolocator = geopy.ArcGIS() if geolocator is None else geolocator
    location = geolocator.geocode(address)
    try:
        return (location.latitude, location.longitude)
    except AttributeError:
        return (np.nan, np.nan)

def find_address(latitude: float, longitude: float, geolocator=None):    
    geolocator = geopy.ArcGIS() if geolocator is None else geolocator
    location = geolocator.geocode(f"{latitude}, {longitude}")
    try:
        return location.address
    except AttributeError:
        return ''

def find_location_columns(addresses: pd.Series):
    return pd.DataFrame(
        [find_location(address) for address in addresses], 
        columns=['latitude', 'longitude'], index=addresses.index
    )

def find_address_column(latitudes: pd.Series, longitudes: pd.Series):
    return pd.Series(
        [find_address(latitude, longitude) for latitude, longitude in zip(latitudes, longitudes)],
        index=latitudes.index, name='address'
    )




def find_text_columns(dataframe: pd.DataFrame, params={}) -> list:
    """
    Find text columns in a dataframe.

    Args:
        dataframe (pd.DataFrame): the dataframe to check

    Returns:
        list: a list of column names with text
    """
    return [
        x 
        for x in dataframe.columns 
        if is_column_text(dataframe[x], params=params)
    ]




def find_column(dataframe: pd.DataFrame, example_column: pd.Series, params={}, rename=True) -> pd.Series:
    """
    Return the column from the dataframe that is most similar to the example
    
    Args:
        dataframe: The dataframe to search
        example_column: The example of a column schema to search for
        min_similarity: The minimum similarity to consider
        rename: If true (default), rename the found column to the name of the example column
    
    Returns:
        The column found that is most similar to the example_column
    """
    # find columns' similarities
    similarities = dataframe.apply(lambda column: similarity_columns(column, example_column, params))
    if np.max(similarities) < params.get('min_similarity_column', 0.25): return None
    # find the most similar column
    column = dataframe.iloc[:, np.argmax(similarities)]
    # replace the name of the column with the name of the example_column
    if rename:
        column.name = example_column.name
    # return the most similar column
    return column




def find_dataframe(dataframe: pd.DataFrame, example_dataframe: pd.DataFrame, params={},
    rename=True, print_similarities=False, drop_duplicates=True) -> pd.DataFrame:
    """
    Finds and returns the most similar columns to example_dataframe found in the dataframe.

    Args:
        dataframe: The dataframe to search
        example_dataframe: An example of the data to search for
        min_similarity: The minimum similarity to consider
        rename: If true (default), rename the found columns to the name of the example columns
    
    Returns:
        The dataframe found, using the same schema as example_dataframe
    """
    assert rename is True, 'rename not implemented'
    # initialize the output_dataframe
    output_dataframe = pd.DataFrame(columns=example_dataframe.columns)
    # drop irrelevant columns filled with nans, 0s, or empty strings
    dataframe = dataframe.dropna(axis=1, how='all')
    dataframe = dataframe.loc[:, (dataframe != 0).any(axis=0)]
    dataframe = dataframe.loc[:, (dataframe != '').any(axis=0)]
    # calculate similarity between every could of dataframe and every column of example_dataframe
    similarities = pd.DataFrame(index=dataframe.columns, columns=example_dataframe.columns, dtype=float)
    for col_name in dataframe.columns:
        for example_col_name in example_dataframe.columns:
            col = dataframe[col_name]
            example_col = example_dataframe[example_col_name]
            similarities.loc[col_name, example_col_name] = similarity_columns(col, example_col, params=params)
    # print similarities
    if print_similarities:
        print(similarities)
    # iterate through the similarities matrix to find the most similar match-ups,
    # and then remove them from the similarities matrix, so they are aren't reused.
    while min(similarities.shape) > 0:
        # find the most similar columns
        col_name = similarities.max(axis=1).idxmax()
        example_col_name = similarities.max(axis=0).idxmax()
        similarity = similarities.loc[col_name, example_col_name]
        # if the similarity is too low, ignore the column
        if similarity < params.get('min_similarity_column', 0.25): break
        # find the column that is most similar to the example column
        similar_col = dataframe.loc[:, col_name]
        example_col = example_dataframe.loc[:, example_col_name]
        output_dataframe[example_col_name] = similar_col
        # drop the matched similarities
        similarities = similarities.drop(columns=example_col_name)
        print(col_name, '-->', example_col_name)
        # if this is a date, normalize it
        if is_date(similar_col, params=params):
            output_dataframe[example_col_name] = pd.to_datetime(similar_col)
        # if this is the last column with dates in it, then keep it
        if not is_date(similar_col, params=params) or count_columns_with_dates(dataframe[similarities.index]) > 1:
            similarities = similarities.drop(index=col_name)
        # if the datatype is a time (datetime, timestamp, datetime.time or timedelta)
        if is_date(example_col, params=params) and is_time(example_col, params=params) and is_date(similar_col, params=params) and not is_time(similar_col, params=params):
            # make sure example_col is a datetime
            example_col = parse_datetime_column(example_col)
            # look for missing time column
            time_col_missing = find_column(dataframe[similarities.index], example_col.dt.time, params=params, rename=False)
            if time_col_missing is not None:
                # normalize time column found to be pd.timedelta
                try:
                    time_col_missing = time_col_missing.apply(time.isoformat).apply(pd.to_timedelta)
                except TypeError:
                    # occurs when time_col_missing is made of strings instead of time
                    time_col_missing = time_col_missing.apply(pd.to_timedelta)
                # add missing times to dates
                output_dataframe[example_col_name] = output_dataframe[example_col_name] + time_col_missing
                print(col_name, '+', time_col_missing.name, '-->', example_col_name)                    
                # drop time column from the original dataframe
                similarities = similarities.drop(index=time_col_missing.name)
    # replace columns
    output_dataframe.columns = example_dataframe.columns
    # return after removing the duplicates
    return output_dataframe.drop_duplicates() if drop_duplicates else output_dataframe
    




def find_column_by_name(dataframe: pd.DataFrame, column_name: str) -> pd.Series:
    """
    Return the column from the dataframe that is most similar to the example
    
    Args:
        dataframe: The dataframe to search
        column_name: An example of the column name to search for
    
    Returns:
        The column found whose name is most similar to the column_name
    """
    # find candidate columns
    similarities = [similarity_str(column_name, col) for col in dataframe.columns]
    found_column = dataframe.iloc[:, np.argmax(similarities)]
    found_column.name = column_name
    return found_column




def find_dataframe_by_colnames(dataframe: pd.DataFrame, column_names, params={}) -> pd.Series:
    """
    Return the columns from the dataframe that are most similar to the example
    
    Args:
        dataframe: The dataframe to search
        column_names: An example of the column names to search for
        min_similarity: The minimum similarity to consider
    
    Returns:
        The dataframe whose columns names' are most similar to the column_names
    """
    # initialize the output_dataframe
    output_dataframe = pd.DataFrame(columns=column_names)
    # calculate similarity between every could of dataframe and every column of example_dataframe
    similarities = pd.DataFrame(index=dataframe.columns, columns=column_names, dtype=float)
    for col_name in dataframe.columns:
        for example_col_name in column_names:
            similarities.loc[col_name, example_col_name] = similarity_str(col_name, example_col_name)
    while min(similarities.shape) > 0:
        # find the most similar columns
        col_name = similarities.max(axis=1).idxmax()
        example_col_name = similarities.max(axis=0).idxmax()
        similarity = similarities.loc[col_name, example_col_name]
        similarities = similarities.drop(columns=example_col_name)
        # if the similarity is too low, ignore the column
        if similarity < params.get('min_similarity_column', 0.25): continue
        # find the column that is most similar to the example column
        output_dataframe.loc[:,example_col_name] = dataframe.loc[:,col_name]
        # drop index from the similarities
        similarities = similarities.drop(index=col_name)
    return output_dataframe
