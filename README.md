# README for pipeline used for reproducibility and scalability of the model.
This part of the readme file is based on the production of a simple but effective pipeline for the productivization of a notebook and its data.

## Assumptions
For these assignments, i assume that i can not modify or improve the notebook in a data science point of view, its model or its data. Here the focus is the pipeline and API themselves.

## Installation
1. Clone the repository:
```bash
 git clone https://github.com/luizagandolfi/MLOps.git
```
## If you want to run the pipeline locally, follow these steps:
Install dependencies:
```cmd
 pip install -r requirements
 ```
Initiate DVC (it must be used just the first time you run the pipeline):
dvc init

Run pipeline:
dvc repro

## If you want to run the pipeline in docker, follow these steps:
Initialize Docker, it was done with Docker Desktop.

```cmd
 docker-compose up
```
It will initiate the pipeline and the api in docker. If you want to run just the pipeline, exit api by pressing CTRL-C (in cmd) and run only the pipeline by executing "docker-compose run pipeline". DVC will be initiated and the pipeline will be executed.

 ## Explanation:
 The pipeline is composed mainly by four stages: Data Loading (data_load.py), Data Preprocessing (data_preprocess.py), Training the model (train.py) and Evaluating the model (evaluating.py). Besides, there is the file "params.yaml" that is used to control certain variables that can be changed in the pipeline, sush as directories, source of data (drive or certain database) and training parameters, assuring that way that, by modifying only this file, the pipeline will execute with the desired specifications.

 The pipeline itself was achieved with DVC, which is a tool for ML pipeline automation. Everytime the pipeline is executed, the output directories are automatically updated with the latest data and models produced, that will be used in the api.

 # data_load.py
 This script is responsible to bring the data used for the rest of the pipeline to inside the project. In this case, it is downloaded from a file in google drive, once the data can not be in the same repository as the code, by compliance. Using this file and specificating the source in params.yaml (in this case, the pipeline will run just with 'google_drive', but in the future, changing it to 'database' will allow the data to be downloaded from a database), the code (using 'google_drive' as source) will get the credentials of a service account that was set for this project and will be used to access the folder in Google Drive that contains the data. In params.yaml is also set the scope of this service account, saying it can only read (and download) the files, without making changes to them. This is done by the function "get_service" and the finding and downloading of the files in "data/raw" is done by the function "download_files_from_drive".

 # data_preprocess.py
 This script is responsible for preprocessing the data downloaded in the previous step. It trains a preprocessor (that will be saved in "outputs/model" for further utilization in the api) and process the training data in function "fit_preprocessing" and process other data (in test file and the ones brought by api) in "transform_preprocessing". After processing the train and test data, they are saved in "data/processed" for utilization in the train step.

 # train.py
 This script is responsible for training the model with the processed data of the previous step. It takes the type of model and the parameters for training in the params.yaml file and saves the model in "outputs/model".

 # evaluate.py
 This script is responsible for evaluation of the model with the trained model of the previous step and the test data processed in data preprocess step. The metrics used are the same as the ones used in the given notebook. After the metrics calculation, they are saved in "output".

 # pipeline
 The pipeline is executed in full using the file "dvc.yaml" that specified the stages, order, dependencies and outputs. It is executed locally by typing "dvc repro" in the cmd. If a parameter is changed, we run again the pipeline and the changes will be applied to the code.


# README for api for model usage.
This part of the readme file is based on the serving of a pipeline.

## Assumptions
For this assignment, i assumed i could use the automatic swagger-ui, available by putting /docs at the end of localhost:8000.

## If you want to run the api locally, follow these steps:
Install dependencies:
```cmd
 pip install -r requirements
 cd src
 uvicorn api:app --port 8000
 ```
## If you want to run the api in docker, follow these steps:
```cmd
 docker-compose up
```
It will initiate the pipeline and the api. The api will be initiated and can be used.After, if you want to run just the api, exit by pressing CTRL-C (in cmd) and run the api by executing "docker-compose run api". Next, go to a web browser and type localhost:8000/docs, and you will be redirected to the FastAPI Swagger-UI.

It was required that the api used some sort of security, so in order to use the api, the user must first click in the green button "Authorize" in superior right corner. The username is "user1" and the password is "secret". After the authorization, go to Generate Prediction, click in "Try it out", fill the required informations, with the correct type of data, and click in execute. The answer will be displayed below in a json, like that: {"predicted_valuation": 5806.114791605412}.

## Explanation

The framework used for the API is FastAPI and the security is granted by OAuth2PasswordBearer, that obtains an access token using username and password and JSON Web Token (JWT) for user authentication. From other scripts are user utils.py for model returning for prediction and data_preprocessor.py for input transforming to feed the models. The models used are "preprocessor.sav" for input processing and "model.sav" for valuation prediction.

# Last considerations
The API and the pipeline are different services run in different containers that share the same volumes.
The model used is the same as the original given, without improvements.
API performance was not tested nor improved.

## Further improvements
1. Implementation of unitary tests;
2. Implementation of a fine tunning stage;
3. Further security api tests;
4. API and pipeline performance tests and enhancement.
