FROM python:3.11


RUN pip3 install --no-cache --upgrade pip setuptools

RUN mkdir -p /opt/opa/cryptobot data_collectors
WORKDIR /opt/opa/
ADD cryptobot/ cryptobot/
ADD batch/init_db/* .
ADD data_collectors/__init__.py data_collectors/
ADD data_collectors/history_data_collector_zip.py data_collectors/
ADD config.yml .

RUN pip install -r ./requirements.txt

CMD python init_db.py
