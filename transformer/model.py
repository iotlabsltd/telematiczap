# model for transforming dataframes and table files 

from itertools import dropwhile
import pandas as pd
from .io import read_dataframe, save_dataframe
from .translate import detect_language, translate_dataframe
from .find import find_dataframe
import optuna
import traceback

class TelematicZapTransformer:
    def __init__(self, drop_duplicates=True):
        self.drop_duplicates=drop_duplicates
        self.params = {
            'min_similarity_column': 0.25, # find_column
            'min_similarity_id': 0.5, # is_column_text
            'min_similarity_address': 0.4, # is_column_text
            'min_similarity_time': 0.5, # is_time
            'min_similarity_date': 0.5, # is_date
            # similarity_columns
            'weight_similarity_time': 0.5, 
            'weight_similarity_date': 0.5, 
            'discount_weight_similarity_date': 0.3, 
            'discount_weight_similarity_time': 0.3, 
            'match_similarity_datetime': 0.5, 
            'unmatch_similarity_datetime': 0.5, 
            'match_similarity_time': 0.5, 
            'min_similarity_colname_id': 0.5, 
            'weight_id_similarity_name': 0.6, 
            'weight_id_similarity_idname': 0.2, 
            'weight_id_similarity_uniqueness': 0.1, 
            'weight_id_similarity_values': 0.1, 
            'weight_string_similarity_name': 0.6, 
            'weight_string_similarity_values': 0.2, 
            'weight_string_similarity_word_count': 0.1,
            'weight_numeric_similarity': 0.8,
            'weight_numeric_similarity_name': 0.7, 
            'weight_numeric_similarity_std': 0.2, 
            'weight_numeric_similarity_mean': 0.1,
            'weight_diftypes_similarity': 0.5
        }

    def translate(self, dataframe: pd.DataFrame, example_dataframe=None, target_language='en'):
        # detect target language using column names
        if example_dataframe is not None:
            target_language = detect_language(example_dataframe)
        # return translated dataframe
        return translate_dataframe(dataframe, lang_to=target_language)
            
    def transform(self, dataframe: pd.DataFrame, example_dataframe=None, translate=True, params={}) -> pd.DataFrame:
        """
        Translate and transform a dataframe given an example for the new schema.    
        
        Args:
            dataframe (pd.DataFrame): the dataframe to transform to a new format
            example_dataframe (pd.DataFrame): a dataframe with the format we want to have
        
        Returns:
            Dataframe translated and transformed, according to example_dataframe.
        """
        if not params:
            params = self.params
        if translate:
            dataframe = self.translate(dataframe, example_dataframe)
        transformed_dataframe = find_dataframe(dataframe, example_dataframe, drop_duplicates=self.drop_duplicates, params=params)
        transformed_dataframe.columns = example_dataframe.columns
        return transformed_dataframe

    def transform_from_file(self, input_file: str, output_file: str, output_example_file: str, 
                read_kwargs={}, write_kwargs={}, example_kwargs={}, clues=None,
                limit_rows=None) -> None:
        """
        Transform a table into a new schema, and saves it as a new file.

        Args:
            input_file (str): path to the input file
            output_file (str): path to the output file
            output_example_file (str): path to the output example file
            **kwargs: any other arguments to pass to the pandas read function
        """
        dataframe = read_dataframe(input_file, **read_kwargs)
        if limit_rows:
            dataframe = dataframe.iloc[:limit_rows]
        example_dataframe = read_dataframe(output_example_file, **example_kwargs)
        transformed_dataframe = self.transform(dataframe, example_dataframe)
        save_dataframe(transformed_dataframe, output_file, **write_kwargs)

    def score(self, transformed_dataset, after_dataset):
        assert transformed_dataset.columns.equals(after_dataset.columns)
        total_score = 0
        for column_name in after_dataset.columns:
            transformed_column = transformed_dataset.loc[:, column_name]
            after_column = after_dataset.loc[:, column_name]
            total_score += int(transformed_column.equals(after_column))
        return total_score / after_dataset.shape[1]

    def fit(self, before_datasets, formats_examples, after_datasets):
        # translate before optimization
        translated_datasets = []
        for before_df, format_df in zip(before_datasets, formats_examples):
            translated_datasets += [self.translate(before_df, format_df)]
        # define optimization objective
        def objective(trial):
            # set object parameters
            params = {
                'min_similarity_column': trial.suggest_float('min_similarity_column', 0.1, 0.6), # find_column
                'min_similarity_id': trial.suggest_float('min_similarity_id', 0.0, 1.0),
                'min_similarity_address': trial.suggest_float('min_similarity_address', 0.0, 1.0), # is_column_text
                'min_similarity_time': trial.suggest_float('min_similarity_time', 0.0, 1.0), # is_time
                'min_similarity_date': trial.suggest_float('min_similarity_date', 0.0, 1.0), # is_date
                # similarity_columns
                'weight_similarity_time': trial.suggest_float('weight_similarity_time', 0.0, 1.0),
                'weight_similarity_date': trial.suggest_float('weight_similarity_date', 0.0, 1.0), 
                'discount_weight_similarity_date': trial.suggest_float('discount_weight_similarity_date', 0.0, 0.6),
                'discount_weight_similarity_time': trial.suggest_float('discount_weight_similarity_time', 0.0, 0.6),
                'match_similarity_datetime': trial.suggest_float('match_similarity_datetime', 0.0, 1.0),
                'unmatch_similarity_datetime': trial.suggest_float('unmatch_similarity_datetime', 0.0, 1.0),
                'match_similarity_time': trial.suggest_float('match_similarity_time', 0.0, 1.0),
                'min_similarity_colname_id': trial.suggest_float('min_similarity_colname_id', 0.0, 1.0),
                'weight_id_similarity_name': trial.suggest_float('weight_id_similarity_name', 0.0, 1.0),
                'weight_id_similarity_idname': trial.suggest_float('weight_id_similarity_idname', 0.0, 0.6), 
                'weight_id_similarity_uniqueness': trial.suggest_float('weight_id_similarity_uniqueness', 0.0, 0.6),
                'weight_id_similarity_values': trial.suggest_float('weight_id_similarity_values', 0.0, 0.6),
                'weight_string_similarity_name': trial.suggest_float('weight_string_similarity_name', 0.0, 1.0),
                'weight_string_similarity_values': trial.suggest_float('weight_string_similarity_values', 0.0, 0.6),
                'weight_string_similarity_word_count': trial.suggest_float('weight_string_similarity_word_count', 0.0, 0.6),
                'weight_numeric_similarity': trial.suggest_float('weight_numeric_similarity', 0.2, 1.0),
                'weight_numeric_similarity_name': trial.suggest_float('weight_numeric_similarity_name', 0.2, 1.0),
                'weight_numeric_similarity_std': trial.suggest_float('weight_numeric_similarity_std', 0.0, 0.6),
                'weight_numeric_similarity_mean': trial.suggest_float('weight_numeric_similarity_mean', 0.0, 0.6),
                'weight_diftypes_similarity': trial.suggest_float('weight_diftypes_similarity', 0.0, 1.0)
            }
            # iterate all datasets, transform them, calculate score, and add to total score
            total_score = 0
            for translated_df, format_df, after_df in zip(translated_datasets, formats_examples, after_datasets):
                try:
                    # transformation
                    transformed_df = self.transform(translated_df, format_df, translate=False, params=params)
                    # calculate and add to total score
                    total_score += self.score(transformed_df, after_df)
                except Exception:
                    print(traceback.format_exc())
            # return average score
            return total_score / len(before_datasets)
        # optimize hyperparameters
        study = optuna.create_study(study_name='telematiczap', storage='sqlite:///optuna.db', load_if_exists=True, direction='maximize')
        study.optimize(objective, n_trials=500)
        # pick the parameters that achieved highest score
        self.params = study.best_params
