import argparse
import logging
import pickle
import numpy as np
import pandas as pd
import yaml
import joblib
import sklearn

from category_encoders import TargetEncoder
from sklearn.compose import ColumnTransformer
from joblib import dump, load
from utils import find_project_root

logger = logging.getLogger('__name__')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

if (logger.hasHandlers()):
    logger.handlers.clear()
logger.addHandler(ch)

#Fits a preprocessing pipeline using TargetEncoder for categorical columns
def fit_preprocessing(data, categorical_columns, target_column, preprocessor_destination_directory) -> (pd.DataFrame, ColumnTransformer):
    try:
        logger.info('Starting preprocessing fit.')
        train_columns = [col for col in data.columns if col not in ['id', 'target']]
        categorical_transformer = TargetEncoder()
        
        preprocessor = ColumnTransformer(
            transformers=[
                ('categorical', categorical_transformer, categorical_columns)
            ], remainder='passthrough')
        
        data_transformed = preprocessor.fit_transform(data[train_columns], data[target_column])
        df_transformed = pd.DataFrame(data_transformed, columns=data.columns)
        
        print("Versão do scikit-learn:", sklearn.__version__)
        pickle.dump(preprocessor, open(preprocessor_destination_directory / "preprocessor.sav", "wb"))
        logger.info('Preprocessing fit completed and saved.')
        return df_transformed, preprocessor
    
    except Exception as e:
        logger.error(f'Error in preprocess fitting: {e}')
        raise
    
    
def transform_preprocessing(data, preprocessor) -> pd.DataFrame:
    try:
        logger.info('Starting data transformation.')
        train_columns = [col for col in data.columns if col not in ['id', 'target']]
        data_transformed = preprocessor.transform(data[train_columns])
        df_transformed = pd.DataFrame(data_transformed, columns=data.columns)
        
        logger.info('Data transformation completed.')
        return df_transformed
    
    except Exception as e:
        logger.error(f'Error during data transformation: {e}')
        raise


if __name__ == '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--params', dest='params', required=True)
    args = args_parser.parse_args()

    with open(args.params) as param_file:
        params = yaml.safe_load(param_file)

    PROJECT_ROOT = find_project_root()
    print(PROJECT_ROOT)
    with open(args.params) as param_file:
        params = yaml.safe_load(param_file)

    
    SOURCE_DIRECTORY = PROJECT_ROOT / params['data_preprocess']['source_directory']
    DESTINATION_DIRECTORY = PROJECT_ROOT / params['data_preprocess']['destination_directory']
    PREPROCESSOR_DIRECTORY = PROJECT_ROOT / params['train']['destination_directory']
    
    CATEGORICAL_COLUMNS = params['train']['categorical_columns']
    TARGET_COLUMN = params['train']['target_column']
    
    train_dataset = pd.read_csv(SOURCE_DIRECTORY / 'train.csv')
    test_dataset = pd.read_csv(SOURCE_DIRECTORY / 'test.csv')
    
    try:
        logger.info('Starting preprocessing task.')
        train_processed, preprocessor = fit_preprocessing(train_dataset, categorical_columns=CATEGORICAL_COLUMNS,
                                                    target_column=TARGET_COLUMN, preprocessor_destination_directory=PREPROCESSOR_DIRECTORY)
        
        test_processed = transform_preprocessing(data=test_dataset, preprocessor=preprocessor)
    
        pickle.dump(train_processed, open(PROJECT_ROOT / DESTINATION_DIRECTORY / "train_processed.pckl", "wb"))
        pickle.dump(test_processed, open(PROJECT_ROOT / DESTINATION_DIRECTORY / "test_processed.pckl", "wb"))
        logger.info(f'Successfully preprocessed data.')
        
    except Exception as e:
        logger.error(f'Error starting preprocessing task: {e}')
        raise


