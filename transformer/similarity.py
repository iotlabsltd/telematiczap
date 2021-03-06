# functions for calculating the similarity between strings, columns, etc

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from pandas.api.types import is_datetime64_any_dtype, is_timedelta64_dtype
import re


# this is the pre-trained model with the best avg performance
# more pre-trained models: https://www.sbert.net/docs/pretrained_models.html#sentence-embedding-models
model = SentenceTransformer('paraphrase-mpnet-base-v2') # this may take some time to load

def similarity_str(s1: str, s2: str, nsamples=5) -> float:
    """
    Calculates the similarity between two strings using a pre-trained model with semantic context.
    Note that this is a stochastic method, so the similarity is not guaranteed to be always the same.

    Args:
        s1: first string
        s2: second string
        nsamples: number of samples to use for the similarity calculation

    Returns:
        similarity between s1 and s2
    """
    def sim_str(s1, s2) -> float:
        # calculate the string embeddings
        embeddings1 = model.encode(s1)
        embeddings2 = model.encode(s2)
        # calculate cosine similarity
        return cos_sim(embeddings1, embeddings2).item()
    
    # average similarity of 5 samples of (s1, s2)
    return np.mean([sim_str(s1, s2) for _ in range(nsamples)])


def is_column_text(column: pd.Series, params={}) -> bool:
    """
    Check if a column is a string column.

    Args:
        dataframe (pd.Series): the column to check
    
    Returns:
        bool: True if the column is a string column, False otherwise
    """
    # check column dtype
    if (column.dtype != 'object') and (column.dtype != 'str'):
        return False

    # check for 'id' in the column name
    if similarity_str('id', column.name.lower()) > params.get('min_similarity_id', 0.5):
        return False

    # check for 'address' in the column name
    if similarity_str('address', column.name.lower()) > params.get('min_similarity_address', 0.4):
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


def is_time(x, params={}) -> bool:
    """
    Check if x has time information.
    """
    if type(x) == pd.Series:
        if is_timedelta64_dtype(x):
            return True
        else:
            sample = x.sample(n=min(len(x), 20)).apply(is_time)
            return sample.astype(float).mean() > params.get('min_similarity_time', 0.5)
    if re.search(r'\d{2}:\d{2}', str(x)) is not None:
        if re.search(r'00:00:00', str(x)) is None:
            return True
    return False


def is_date(x, params={}) -> bool:
    """
    Check if x has date information.
    """
    if type(x) == pd.Series:
        if is_datetime64_any_dtype(x):
            return True
        else:
            sample = x.sample(n=min(len(x), 20)).apply(is_date)
            return sample.astype(float).mean() > params.get('min_similarity_date', 0.5)
    return re.search(r'\d{2}[-/\\\.]\d{2}[-/\\\.]\d{2}', str(x)) is not None


def count_columns_with_dates(dataframe: pd.DataFrame) -> int:
    """
    Count the number of columns in a dataframe that have dates

    Args:
        dataframe: The dataframe to check
    
    Returns:
        The number of columns in the dataframe that have dates
    """
    return sum(is_date(dataframe[col]) for col in dataframe.columns)


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


def replace_with_hints(s: str, context=['trip']):
    """
    Adds hints to column name to make it more recognizable.
    This is a very simple heuristic, but it works well in most cases.

    Args:
        s: string to add hints to
        context: list of strings to use as context
    
    Returns:
        string with hints added
    """
    # non-characters
    s = re.sub(r'[\b\.\n\s]+', ' ', s)
    # numbers
    s = re.sub(r'\b(n[ro]?)\b', r'number', s)
    # latitude
    s = re.sub(r'\b(lat)\b', r'latitude', s)
    # longitude
    s = re.sub(r'\b(lon)\b', r'longitude', s)
    # trip context replacements
    if 'trip' in context: # TODO: the context should be inferred from the data
        s = s.replace('departure', 'start')
        s = s.replace('arrival', 'end')
        s = re.sub(r'\b(reg)\b', r'registration', s)
    # stay context replacements
    elif 'stay' in context:
        s = s.replace('arrival', 'start')
        s = s.replace('departure', 'end')
    # default
    return s


def similarity_columns(column1: pd.Series, column2: pd.Series, params={}) -> float:
    """
    Calculates the similarity between two columns samples using a pre-trained model with semantic context.
    
    Args:
        column1: first column
        column2: second column
    
    Returns:
        similarity between column1 and column2
    """
    #if (column1.name == 'Arrival address') and (column2.name == 'name'):
    #    breakpoint()

    # preprocess the column names
    column1_name = column1.name.replace('_', ' ').lower()
    column2_name = column2.name.replace('_', ' ').lower()
    column1_name = replace_with_hints(column1_name)
    column2_name = replace_with_hints(column2_name)
    column1_sample = column1.sample(n=min(30, len(column1)))
    column2_sample = column2.sample(n=min(30, len(column2)))

    # calculate the similarity between the columns names
    name_similarity = similarity_str(column1_name, column2_name)

    # if column is a date
    if is_date(column1, params) or is_date(column2, params):
        if is_date(column1, params) and is_date(column2, params):
            if is_time(column1, params) == is_time(column2, params):
                return params.get('weight_similarity_date', 0.5) * name_similarity + params.get('match_similarity_datetime', 0.5)
            else:
                return params.get('weight_similarity_date', 0.5) * name_similarity + params.get('unmatch_similarity_datetime', 0.3)
        else:
            return params.get('discount_weight_similarity_date', 0.3) * name_similarity

    # if column is a time
    if is_time(column1, params) or is_time(column2, params):
        if is_time(column1, params) and is_time(column2, params):
            return params.get('weight_similarity_time', 0.5) * name_similarity + params.get('match_similarity_time', 0.5)
        else:
            return params.get('discount_weight_similarity_time', 0.3) * name_similarity

    # if column is an id
    column1_id_similarity = max(similarity_str('id', column1_name), similarity_str('serial number', column1_name))
    column2_id_similarity = max(similarity_str('id', column2_name), similarity_str('serial number', column2_name))
    if column1_id_similarity > params.get('min_similarity_colname_id', 0.5) or \
        column2_id_similarity > params.get('min_similarity_colname_id', 0.5):
        # mean id similarity
        id_name_similarity = column1_id_similarity * column2_id_similarity
        # calculate uniqueness similarity
        column1_id_uniqueness = column1.nunique() / len(column1)
        column2_id_uniqueness = column1.nunique() / len(column2)
        uniqueness_similarity = 1 - \
            abs(column1_id_uniqueness - column2_id_uniqueness) / \
            (column1_id_uniqueness + column2_id_uniqueness)
        # id with strings and numbers
        def id_similar_values(sample):
            sample = sample.astype(str)
            contains_numbers = sample.str.contains(r'\d', regex=True).any()
            contains_lowercase = sample.str.contains(r'[a-z]', regex=True).any()
            contains_punctuation = sample.str.contains(r'[^.,:?! ]', regex=True).any()
            return contains_numbers and not contains_lowercase and not contains_punctuation
        values_similarity = id_similar_values(column1_sample) * id_similar_values(column2_sample) 

        # summarize similarity
        return params.get('weight_id_similarity_name', 0.6) * name_similarity + \
            params.get('weight_id_similarity_idname', 0.2) * id_name_similarity + \
            params.get('weight_id_similarity_uniqueness', 0.1) * uniqueness_similarity + \
            params.get('weight_id_similarity_values', 0.1) * values_similarity

    # if the data are strings
    if (column1.dtype == 'object') and (column2.dtype == 'object'):
        # if the data are strings, stringify a sample of values
        sample_size = min(30, len(column1), len(column2))
        column1_sample = column1.sample(n=sample_size).astype(str)
        column2_sample = column2.sample(n=sample_size).astype(str)
        column1_str = ', '.join([column1_name] + column1_sample.tolist())
        column2_str = ', '.join([column2_name] + column2_sample.tolist())
        # calculate the similarity between the strings
        values_similarity = similarity_str(column1_str, column2_str)
        # calculate similarity based on the number of words
        words_count1 = column1_sample.str.split(r'[ ,]').apply(len).mean()
        words_count2 = column2_sample.str.split(r'[ ,]').apply(len).mean()
        word_count_similarity = 1 - abs(words_count1 - words_count2) / (words_count1 + words_count2)
        # weighted average of similarity
        return params.get('weight_string_similarity_name', 0.7) * name_similarity + \
            params.get('weight_string_similarity_values', 0.2) * values_similarity + \
            params.get('weight_string_similarity_word_count', 0.1) * word_count_similarity
    
    # if the column is numeric
    if is_column_numeric(column1) and is_column_numeric(column2):
        # guarantee a minimum sample size for these calculations
        sample_size = min(30, len(column1), len(column2))
        if sample_size <= 15:
            return name_similarity * params.get('weight_numeric_similarity', 0.8)
        # calculate the similarity between the columns means and stds
        column1_std, column2_std = column1.std(), column2.std()
        column1_mean, column2_mean = column1.mean(), column2.mean()
        std_similarity = 1 - abs(column1_std - column2_std) / (column1_std + column2_std)
        mean_similarity = 1 - abs(column1_mean - column2_mean) / (column1_mean + column2_mean)
        return params.get('weight_numeric_similarity_name', 0.7) * name_similarity + \
            params.get('weight_numeric_similarity_std', 0.2) * std_similarity + \
            params.get('weight_numeric_similarity_mean', 0.1) * mean_similarity

    # if columns are of different types
    if str(column1.dtype) != str(column2.dtype):
        return params.get('weight_diftypes_similarity', 0.5) * name_similarity

    # otherwise, return 0
    return 0

