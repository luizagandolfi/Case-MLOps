import argparse
import logging
import pickle
import pandas as pd
import yaml
import joblib
import sklearn

from joblib import dump
from sklearn.ensemble import GradientBoostingRegressor
from utils import find_project_root

logger = logging.getLogger('__name__')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

if (logger.hasHandlers()):
    logger.handlers.clear()
logger.addHandler(ch)

def train(model_class, model_params, data):
    try:
        logger.info('Starting model training.')
        model = model_class(**model_params)
        target_column = params['train']['target_column']
        train_columns = [col for col in data.columns if col not in ['id', 'target']]
        
        model.fit(data[train_columns], data[target_column])
        return model
    
    except Exception as e:
        logger.error(f'Error during model training: {e}')
        raise

if __name__ == '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--params', dest='params', required=True)
    args = args_parser.parse_args()

    with open(args.params) as param_file:
        params = yaml.safe_load(param_file)

    PROJECT_ROOT = find_project_root()
    DATA_SOURCE_DIRECTORY = PROJECT_ROOT / params['data_preprocess']['destination_directory']
    MODEL_DESTINATION_DIRECTORY = PROJECT_ROOT / params['train']['destination_directory']

    MODEL = getattr(sklearn.ensemble, params['model']['name'])
    MODEL_PARAMS = params['model']['parameters']
    
    try:
        logger.info('Starting training task.')
        train_data = pd.read_pickle(DATA_SOURCE_DIRECTORY / "train_processed.pckl")
        trained_model = train(model_class=MODEL, model_params=MODEL_PARAMS, data=train_data)
        pickle.dump(trained_model, open(MODEL_DESTINATION_DIRECTORY / "model.sav", "wb"))
        logger.info('Successfully trained and saved the model.')
        
    except Exception as e:
        logger.error(f'Error starting training task: {e}')
        raise
