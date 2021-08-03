# functions for finding stuff in dataframes

import pandas as pd
import numpy as np
from .similarity import similarity_str, similarity_columns
from .parse import is_column_text, has_time_information, is_column_time
from datetime import time



def find_text_columns(dataframe: pd.DataFrame) -> list:
    """
    Find text columns in a dataframe.

    Args:
        dataframe (pd.DataFrame): the dataframe to check

    Returns:
        list: a list of column names with text
    """
    return [x for x in dataframe.columns if is_column_text(dataframe[x])]




def find_column(dataframe: pd.DataFrame, example_column: pd.Series, min_similarity=0.2, rename=True) -> pd.Series:
    """
    Return the column from the dataframe that is most similar to the example
    
    Args:
        dataframe: The dataframe to search
        example_column: The example of a column schema to search for
    
    Returns:
        The column found that is most similar to the example_column
    """
    # find columns' similarities
    similarities = dataframe.apply(lambda column: similarity_columns(column, example_column))
    if np.max(similarities) < min_similarity: return None
    # find the most similar column
    column = dataframe.iloc[:, np.argmax(similarities)]
    # replace the name of the column with the name of the example_column
    if rename:
        column.name = example_column.name
    # return the most similar column
    return column




def count_columns_with_dates(dataframe: pd.DataFrame) -> int:
    """
    Count the number of columns in a dataframe that have dates

    Args:
        dataframe: The dataframe to check
    
    Returns:
        The number of columns in the dataframe that have dates
    """
    return sum(pd.api.types.is_datetime64_any_dtype(dataframe[col]) for col in dataframe.columns)




def find_dataframe(dataframe: pd.DataFrame, example_dataframe: pd.DataFrame, min_similarity=0.2, rename=True) -> pd.DataFrame:
    """
    Finds and returns the most similar columns to example_dataframe found in the dataframe.

    Args:
        dataframe: The dataframe to search
        example_dataframe: An example of the data to search for
    
    Returns:
        The dataframe found, using the same schema as example_dataframe
    """
    assert rename is True, 'rename not implemented'
    # initialize the output_dataframe
    output_dataframe = pd.DataFrame(columns=example_dataframe.columns)
    # calculate similarity between every could of dataframe and every column of example_dataframe
    similarities = pd.DataFrame(index=dataframe.columns, columns=example_dataframe.columns, dtype=float)
    for col_name in dataframe.columns:
        for example_col_name in example_dataframe.columns:
            col = dataframe[col_name]
            example_col = example_dataframe[example_col_name]
            similarities.loc[col_name, example_col_name] = similarity_columns(col, example_col)
    while min(similarities.shape) > 0:
        # find the most similar columns
        max_index = similarities.max(axis=1).idxmax()
        max_column = similarities.max(axis=0).idxmax()
        similarity = similarities.loc[max_index, max_column]
        # if the similarity is too low, ignore the column
        if similarity < min_similarity: break
        # find the column that is most similar to the example column
        output_dataframe[max_column] = dataframe.loc[:, max_index]
        # drop the matched similarities
        similarities = similarities.drop(columns=max_column)
        print(max_index, '-->', max_column)
        # if this is the last column with dates in it, then keep it
        if not pd.api.types.is_datetime64_any_dtype(output_dataframe[max_column]) or count_columns_with_dates(dataframe[similarities.index]) > 1:
            similarities = similarities.drop(index=max_index)
        # if the datatype is a time (datetime, timestamp, or timedelta)
        if is_column_time(output_dataframe[max_column]):
            date_example_has_time = has_time_information(example_dataframe[max_column].iloc[0])
            date_most_similar_has_time = has_time_information(output_dataframe[max_column].iloc[0])
            # if the found datetime column is missing the time, then we need to find the time column and add to it
            if date_example_has_time and not date_most_similar_has_time:
                missing_timedelta_example = example_dataframe[max_column].dt.time
                missing_timedelta_found = find_column(dataframe[similarities.index], missing_timedelta_example, min_similarity, rename=False)
                if missing_timedelta_found is not None:
                    missing_timedelta_found = missing_timedelta_found.apply(time.isoformat).apply(pd.to_timedelta)
                    output_dataframe[max_column] = output_dataframe[max_column] + missing_timedelta_found
                    similarities = similarities.drop(index=missing_timedelta_found.name)
                    print(max_index, '+', missing_timedelta_found.name, '-->', max_column)
    return output_dataframe




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




def find_dataframe_by_colnames(dataframe: pd.DataFrame, column_names, min_similarity=0.2) -> pd.Series:
    """
    Return the columns from the dataframe that are most similar to the example
    
    Args:
        dataframe: The dataframe to search
        column_names: An example of the column names to search for
    
    Returns:
        The columns found whose names are most similar to the column_names
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
        max_index = similarities.max(axis=1).idxmax()
        max_column = similarities.max(axis=0).idxmax()
        similarity = similarities.loc[max_index, max_column]
        similarities = similarities.drop(columns=max_column)
        # if the similarity is too low, ignore the column
        if similarity < min_similarity: continue
        # find the column that is most similar to the example column
        output_dataframe.loc[:,max_column] = dataframe.loc[:,max_index]
        # drop index from the similarities
        similarities = similarities.drop(index=max_index)
    return output_dataframe
