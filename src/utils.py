from pathlib import Path
import yaml
from typing import Optional
import pickle
import pandas as pd

import logging
logger = logging.getLogger('__name__')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

if (logger.hasHandlers()):
    logger.handlers.clear()
logger.addHandler(ch)

def find_project_root() -> Optional[Path]:
    current = Path(".").resolve()
    
    while True:
        if (current / ".git").exists():
            return current
        
        if current.parent == current:
            print("WARNING: No .git dir found")
            return current
              
        current = current.parent

def return_models():
    PROJECT_ROOT = find_project_root()
    print(PROJECT_ROOT)
    with open(PROJECT_ROOT / "params.yaml") as param_file:
        params = yaml.safe_load(param_file)
        
    MODEL_PATH = PROJECT_ROOT / params['train']['destination_directory']
    
    model = pickle.loads((MODEL_PATH / "model.sav").read_bytes())
    preprocessor = pickle.loads((MODEL_PATH / "preprocessor.sav").read_bytes())
    
    return model, preprocessor