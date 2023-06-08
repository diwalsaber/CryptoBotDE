FROM python:3.11


RUN pip3 install --no-cache --upgrade pip setuptools

RUN mkdir -p /opt/opa/cryptobot /opt/opa/data_collectors /opt/opa/models
WORKDIR /opt/opa/
ADD api/backend/* .
ADD cryptobot/ cryptobot/
ADD data_collectors/ data_collectors/
ADD config.yml .

RUN pip install -r ./requirements.txt

EXPOSE 8000
CMD uvicorn apiapp:api --host 0.0.0.0 --port 8000
