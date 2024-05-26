FROM python:3.10

WORKDIR /MLOps

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN pip install fastapi uvicorn
RUN dvc init --no-scm

COPY . .

EXPOSE 8000
