import argparse
import pickle
import pandas as pd
import numpy as np
import logging
import yaml

from sklearn.metrics import (mean_squared_error,mean_absolute_percentage_error,mean_absolute_error)
from joblib import load
from utils import find_project_root

logger = logging.getLogger('__name__')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

if (logger.hasHandlers()):
    logger.handlers.clear()
logger.addHandler(ch)

if __name__ == '__main__':

    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--params', dest='params', required=True)
    args = args_parser.parse_args()

    with open(args.params) as param_file:
        params = yaml.safe_load(param_file)

    PROJECT_ROOT = find_project_root()
    DESTINATION_DIRECTORY: str = params['data_preprocess']['destination_directory']

    try:
        logger.info('Starting evaluation task.')
        logger.info('Loading models and data.')
        model = load(PROJECT_ROOT / "outputs" / "model"/"model.sav") 
        test = pd.read_pickle(PROJECT_ROOT / DESTINATION_DIRECTORY / "test_processed.pckl")
        
        target_column = params['train']['target_column']
        train_columns = [col for col in test.columns if col not in ['id', 'target']]

        logger.info('Predicting values')
        predictions = model.predict(test[train_columns])
        target = test[target_column]

        logger.info('Calculating metrics')
        metrics = {}

        metrics["RMSE"] = np.sqrt(mean_squared_error(predictions, target))
        metrics["MAPE"] = mean_absolute_percentage_error(predictions, target)
        metrics["MAE"] = mean_absolute_error(predictions, target)


        logger.info('Saving metrics')
        with open(PROJECT_ROOT / "outputs" / "metrics.yaml", 'w') as file:
            yaml.dump(metrics, file, default_flow_style=False)
            
        logger.info('Successfully evaluated model and saved metrics.')
        logger.info(f'Metrics: {metrics}')
    
    except Exception as e:
        logger.error(f'Error starting evaluation task: {e}')
        raise