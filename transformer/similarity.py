# functions for calculating the similarity between strings, columns, etc
import numpy as np
import pandas as pd
from .parse import has_time_information, is_column_text, is_column_numeric, is_column_time
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from pandas.api.types import is_datetime64_any_dtype, is_timedelta64_dtype


# this is the pre-trained model with the best avg performance
# more pre-trained models: https://www.sbert.net/docs/pretrained_models.html#sentence-embedding-models
model = SentenceTransformer('paraphrase-mpnet-base-v2') # this may take some time to load


def similarity_str(s1: str, s2: str) -> float:
    """
    Calculates the similarity between two strings using a pre-trained model with semantic context.
    
    Args:
        s1: first string
        s2: second string

    Returns:
        similarity between s1 and s2
    """
    embeddings1 = model.encode(s1)
    embeddings2 = model.encode(s2)
    return cos_sim(embeddings1, embeddings2).item()



def similarity_columns(column1: pd.Series, column2: pd.Series) -> float:
    """
    Calculates the similarity between two columns samples using a pre-trained model with semantic context.
    
    Args:
        column1: first column
        column2: second column
    
    Returns:
        similarity between column1 and column2
    """
    # return 0 similarity in case the types are different
    # calculate the similarity between the columns names
    name_similarity = similarity_str(column1.name, column2.name)

    # if the columns match in dtype: timedelta or datetime
    if is_column_time(column1) and is_column_time(column2):
        values_similarity = 1.0
        # if the columns have time information
        if has_time_information(column1) and has_time_information(column2):
            values_similarity = 0.8
            # if their type is the same
            if ((is_datetime64_any_dtype(column1) and is_datetime64_any_dtype(column2))
            or (is_timedelta64_dtype(column1) and is_timedelta64_dtype(column2))):
                values_similarity = 1.0
        # otherwise:
        return name_similarity*0.5 + values_similarity*0.5

    # if only one of the columns is a timedelta or datetime
    if is_column_time(column1) or is_column_time(column2):
        return 0

    # if the data are strings
    if (column1.dtype == 'object') and (column2.dtype == 'object'):
        # if the data are strings, stringify a sample of values
        sample_size = min(30, len(column1), len(column2))
        column1_sample = column1.sample(n=sample_size).astype(str).tolist()
        column2_sample = column2.sample(n=sample_size).astype(str).tolist()
        column1_str = ', '.join([column1.name] + column1_sample)
        column2_str = ', '.join([column2.name] + column2_sample)
        # calculate the similarity between the strings
        values_similarity = similarity_str(column1_str, column2_str)
        return name_similarity * 0.5 + values_similarity * 0.5
    
    # if the column is numeric
    if is_column_numeric(column1) and is_column_numeric(column2):
        # guarantee a minimum sample size for these calculations
        sample_size = min(30, len(column1), len(column2))
        if sample_size <= 1:
            return name_similarity 
        # calculate the similarity between the columns statistics
        column1_std, column2_std = column1.std(), column2.std()
        column1_mean, column2_mean = column1.mean(), column2.mean()
        if (column1_mean == column2_mean) or (column1_std == column2_std):
            return 1
        else:
            std_similarity = 1 - abs(column1_std - column2_std) / (column1_std + column2_std)
            mean_similarity = 1 - abs(column1_mean - column2_mean) / (column1_mean + column2_mean)
            return name_similarity*.8 + std_similarity*.1 + mean_similarity*.1

    # if column is an id
    if ('id' in column1.name) and ('id' in column2.name):
        if (str(column1.dtype) == str(column2.dtype)):
            return name_similarity*0.5 + 0.5
        else:
            return name_similarity*0.6 + 0.4

    # if columns are of different types
    if str(column1.dtype) != str(column2.dtype):
        return name_similarity*0.5

    # otherwise, return 0
    return 0

