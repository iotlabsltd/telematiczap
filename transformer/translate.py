# functions for detecting language and translating

from cgitb import text
from enum import unique
import pandas as pd
from langdetect import detect as detect_str
from deep_translator import GoogleTranslator
from .find import find_text_columns
from functools import lru_cache
from collections import defaultdict
import swifter


def detect_language(dataframe, where='columns') -> str:
    """
    Detect the language of a dataframe.

    Args:
        dataframe (pd.DataFrame): the dataframe to detect the language of
        where (str): either 'columns' or 'values'
    
    Returns:
        str: the language of the dataframe
    """
    assert where in ('columns', 'values')
    # look for language in column names
    if where == 'columns':
        return detect_str('. '.join(dataframe.columns))
    # look for language in values
    elif where == 'values':
        text_columns = dataframe[find_text_columns(dataframe)]
        languages_found = defaultdict(int)
        for _ in range(100):
            sample = text_columns.apply(lambda col: col.sample().to_string()[:500])
            language_found = detect_str(sample.to_string())
            languages_found[language_found] += 1
        return max(languages_found, key=languages_found.get)


@lru_cache(maxsize=128)
def translate_str(x: str, lang_from='auto', lang_to='en') -> str:
    """
    Translate a string from any language to another language.

    Args:
        x (str): the string to be translated
        lang_from (str): the language of the string
        lang_to (str): the language to translate to

    Returns:
        str: the translated string
    """
    # if x is not a string, return it
    if type(x) != str: return x
    if x.isnumeric(): return x
    # if x is nan or an empty string, return it
    if x.lower() == 'nan': return x
    if len(x) == 0: return x
    # detect language if 'auto'
    if lang_from == 'auto':
        lang_from = detect_str(x)
    # maximum character limit on a single text is 5k.
    if len(x) > 5000:
        first15000 = translate_str(x[:5000], lang_from, lang_to)
        latter = translate_str(x[5000:], lang_from, lang_to)
        return first15000 + latter
    # translate 
    translator = GoogleTranslator(source=lang_from, target=lang_to)
    return translator.translate(x)


# renaming duplicate column names
# credits to https://stackoverflow.com/a/55405151
def dedup_index(idx, fmt='%s.%03d', ignoreFirst=True):
    # fmt:          A string format that receives two arguments: 
    #               name and a counter. By default: fmt='%s.%03d'
    # ignoreFirst:  Disable/enable postfixing of first element.
    idx = pd.Series(idx)
    duplicates = idx[idx.duplicated()].unique()
    for name in duplicates:
        dups = idx==name
        ret = [fmt%(name,i) if (i!=0 or not ignoreFirst) else name for i in range(dups.sum()) ]
        idx.loc[dups] = ret
    return pd.Index(idx)


def translate_dataframe(dataframe, lang_from='auto', lang_to='en', params={}) -> pd.DataFrame:
    """
    Translate a dataframe from any language to another.

    Args:
        dataframe (pd.DataFrame): the dataframe to be translated
        lang_from (str): the language of the dataframe
        lang_to (str): the language to translate to
    
    Returns:
        pd.DataFrame: the translated dataframe
    """
    # detect the language of the text
    if lang_from == 'auto':
        # detect the language using columns
        lang_columns = detect_language(dataframe, where='columns')
        lang_values = detect_language(dataframe, where='values')
    else:
        lang_columns = lang_from
        lang_values = lang_from
    # copy the input dataframe
    translated_dataframe = dataframe.copy()
    # translate the column names
    if lang_columns != lang_to:
        translated_columns= pd.Series([translate_str(c, lang_columns, lang_to) for c in translated_dataframe.columns])
        original_columns = pd.Series(translated_dataframe.columns)
        dups = pd.Series(translated_columns).duplicated(keep=False)
        translated_columns[dups] = translated_columns[dups] + ' (' + original_columns[dups] + ')'
        translated_dataframe.columns = translated_columns
    # translate the values
    if lang_values != lang_to:
        # find text columns to translate (exclude addresses)
        columns_to_translate = [
            column_name 
            for column_name in find_text_columns(translated_dataframe, params=params)
            if detect_language(translated_dataframe.loc[:, [column_name]], 'values') != lang_to
        ]
        # define function for translating a single column
        def batch_translate_column(column):
            # filter out unique strings
            column_strings = column[column.map(type)==str]
            unique_strings = column_strings.unique()
            # concatenate strings into batches of around 5000 characters
            separator = '.\n\n\n'
            string_batches = [unique_strings[0]]
            for unique_string in unique_strings[1:]:
                concatenated_string = string_batches[-1] + separator + unique_string
                if len(concatenated_string) < 5000:
                    string_batches[-1] = concatenated_string
                else:
                    string_batches.append(unique_string)
            # translate batches using all cores
            def translate_batch(batch):
                return translate_str(batch, lang_values, lang_to)
            print('Translating column',column.name)
            translated_batches = pd.Series(string_batches).swifter.apply(translate_batch)
            # flatten the batches into a list of strings
            translated_strings = [
                string
                for string_batch in translated_batches
                for string in string_batch.split(separator)
            ]
            # create dictionary with translations
            translation_dictionary = {
                original: translated
                for original, translated in zip(unique_strings, translated_strings)
            }
            # map column values using the translation dictionary
            return column.map(translation_dictionary)
        # translate dataframe using all cores
        translated_dataframe[columns_to_translate] = translated_dataframe[columns_to_translate].apply(batch_translate_column)
    # return the translated dataframe
    return translated_dataframe
