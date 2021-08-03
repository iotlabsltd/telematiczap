# functions for transforming dataframes and table files 

import pandas as pd
from .parse import read_dataframe, save_dataframe
from .translate import detect_str, detect_dataframe, translate_dataframe
from .find import find_dataframe_by_colnames, find_dataframe


def transform_dataframe(dataframe: pd.DataFrame, example_dataframe=None, example_columns=None) -> pd.DataFrame:
    """
    Translate and transform a dataframe given an example for the new schema.    
    
    Args:
        dataframe (pd.DataFrame): the dataframe to transform
        example_dataframe (pd.DataFrame): an exemplar dataframe
        columns (list): the columns to keep
    
    Returns:
        Dataframe translated and transformed, according to example_dataframe.
    """
    if example_dataframe is not None:
        example_language = detect_dataframe(example_dataframe)
        translated_dataframe = translate_dataframe(dataframe, lang_to=example_language)
        found_dataframe = find_dataframe(translated_dataframe, example_dataframe)
        found_dataframe.columns = example_dataframe.columns
        return found_dataframe
    elif example_columns is not None:
        output_language = detect_str(' '.join(example_columns))
        translated_dataframe = translate_dataframe(dataframe, lang_to=output_language)
        found_dataframe = find_dataframe_by_colnames(translated_dataframe, example_columns)
        return found_dataframe
    else:
        raise ValueError('Please provide either example_dataframe or example_columns.')
    


def transform(input_file: str, output_file: str, output_example_file: str, 
              read_kwargs={}, write_kwargs={}, example_kwargs={}, clues=None) -> None:
    """
    Transform a table into a new schema, and saves it as a new file.

    Args:
        input_file (str): path to the input file
        output_file (str): path to the output file
        output_example_file (str): path to the output example file
        **kwargs: any other arguments to pass to the pandas read function
    """
    dataframe = read_dataframe(input_file, **read_kwargs)
    example_dataframe = read_dataframe(output_example_file, **example_kwargs)
    transformed_dataframe = transform_dataframe(dataframe, example_dataframe)
    save_dataframe(transformed_dataframe, output_file, **write_kwargs)



