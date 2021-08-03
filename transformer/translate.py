# functions for detecting language and translating

import pandas as pd
from langdetect import detect as detect_str
from deep_translator import GoogleTranslator
from .find import find_text_columns


def detect_dataframe(dataframe, where='columns') -> str:
    """
    Detect the language of a dataframe.

    Args:
        dataframe (pd.DataFrame): the dataframe to detect the language of
        where (str): either 'columns' or 'values'
    
    Returns:
        str: the language of the dataframe
    """
    if where == 'columns':
        return detect_str(str(dataframe.columns.values)[1:-1])
    elif where == 'values':
        text_columns = dataframe[find_text_columns(dataframe)]
        return detect_str(text_columns.sample(20).to_string()[:5000])
    else:
        raise ValueError('where must be either "columns" or "values"')



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
    if lang_from == 'auto':
        lang_from = detect_str(x)
    if len(x) > 15000:
        # The maximum character limit on a single text is 15k.
        first15000 = translate_str(x[:15000], lang_from, lang_to)
        latter = translate_str(x[15000:], lang_from, lang_to)
        return first15000 + latter
    else:
        translator = GoogleTranslator(source=lang_from, target=lang_to)
        translation = translator.translate(x)
        return translation


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
        ret = [ fmt%(name,i) if (i!=0 or not ignoreFirst) else name
                      for i in range(dups.sum()) ]
        idx.loc[dups] = ret
    return pd.Index(idx)


def translate_dataframe(dataframe, lang_from='auto', lang_to='en') -> pd.DataFrame:
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
        lang_columns = detect_dataframe(dataframe, where='columns')
        lang_values = detect_dataframe(dataframe, where='values')
    else:
        lang_columns = lang_from
        lang_values = lang_from
    # copy the input dataframe
    translated_dataframe = dataframe.copy()
    # translate the values
    if lang_values != lang_to:
        translator = GoogleTranslator(source=lang_values, target=lang_to)
        text_columns = find_text_columns(dataframe)
        def translate_text_column(column):
            def translate_text_only(x):
                # if x is not a string, return it
                if type(x) != str: return x
                # keep only the first 5000 characters (limitation of google translate api)
                x = x.strip()[:5000]
                # if x is nan or an empty string, return it
                if x.lower() == 'nan': return x
                if len(x) == 0: return x
                # translate x, and return it
                return translator.translate(x)
            # map the translated unique values to the original values
            return column.map({x: translate_text_only(x) for x in column.unique()})
        translated_dataframe[text_columns] = dataframe[text_columns].apply(translate_text_column)
    # translate the columns
    if lang_columns != lang_to:
        translator = GoogleTranslator(source=lang_columns, target=lang_to)
        translated_columns= pd.Series([translator.translate(c) for c in translated_dataframe.columns])
        original_columns = pd.Series(translated_dataframe.columns)
        dups = pd.Series(translated_columns).duplicated(keep=False)
        translated_columns[dups] = translated_columns[dups] + ' (' + original_columns[dups] + ')'
        translated_dataframe.columns = translated_columns
        
    # return the translated dataframe
    return translated_dataframe
