import io
import argparse
import yaml
import logging
import sqlalchemy
import pandas as pd

from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
from sqlalchemy.exc import SQLAlchemyError
from utils import find_project_root

logger = logging.getLogger('__name__')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

if (logger.hasHandlers()):
    logger.handlers.clear()
logger.addHandler(ch)

#Function for service creating and authentication
def get_service(api_name, api_version, scopes, key_file_location):
    try:
        logger.info(f'Started creating service for {api_name} API.')
        credentials = service_account.Credentials.from_service_account_file(
        key_file_location)

        scoped_credentials = credentials.with_scopes(scopes)
        service = build(api_name, api_version, credentials=scoped_credentials)
        
        logger.info(f'Successfully created service for {api_name} API.')
        return service
    
    except Exception as e:
        logger.error(f'Error creating service for {api_name} API: {e}')
        raise

# Function for downloading the files from a google drive repo to the specified directory
def download_files_from_drive(scope,credentials,destination):
    try:
        logger.info(f'Started downloading files task.')
        service = get_service(
            api_name='drive',
            api_version='v3',
            scopes=[scope],
            key_file_location=credentials)

        results = service.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])[0]

        if not items:
            logger.info('No files found.')
            return 
        logger.info('Found files in the Drive.')
        
        folder_content = service.files().list(q="'"+str(items.get("id"))+"'"+" in parents and mimeType='text/csv'").execute()               
        folder_files = folder_content.get('files')
        
        for file in folder_files:
            id_ = file.get('id')
            request = service.files().get_media(fileId=id_)
            fh = io.FileIO(destination / file['name'], mode='wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                logger.info(f"Download {int(status.progress() * 100)}% for file {file['name']}")
                
    except Exception as e:
        logger.error(f'Error loading data from Drive: {e}')

# Function for downloading the files from a database to the specified directory
def download_data_from_database(connection_string, query, destination):
    try:
        engine = sqlalchemy.create_engine(connection_string)
        with engine.connect() as connection:
            df = pd.read_sql_query(query, connection)
            df.to_csv(destination / 'table.csv')
        
    except SQLAlchemyError as e:
        print(f"Error loading data from database: {e}")
        return None

if __name__ == '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--params', dest='params', required=True)
    args = args_parser.parse_args()

    with open(args.params) as param_file:
        params = yaml.safe_load(param_file)

    PROJECT_ROOT = find_project_root()
    DESTINATION_PATH = PROJECT_ROOT / params['data_load']['destination_directory']
    SOURCE = params['data_load']['source']
    
    try:
        logger.info('Starting loading data task.')
        if SOURCE == 'google_drive':
            SCOPE = params['data_load']['google_drive']['scope']
            KEY_FILE_LOCATION = PROJECT_ROOT / params['data_load']['google_drive']['credentials']
            
            download_files_from_drive(scope=SCOPE,credentials=KEY_FILE_LOCATION, destination=DESTINATION_PATH)
            logger.info(f'Successfully downloaded data from Drive.')
            
        elif SOURCE == 'database':
            USER = params['data_load']['database']['user']
            PASSWORD = params['data_load']['database']['pass']
            HOST = params['data_load']['database']['host']
            PORT = params['data_load']['database']['port']
            DRIVER = params['data_load']['database']['driver']
            DATABASE = params['data_load']['database']['database']
            QUERY = params['data_load']['database']['query']
            
            connection_string = f"{DRIVER}://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
            download_data_from_database(connection_string=connection_string, query=QUERY, 
                                        destination=DESTINATION_PATH)
            logger.info(f'Successfully downloaded data from database.')
        
    except Exception as e:
        logger.error(f'Error starting loading task: {e}')