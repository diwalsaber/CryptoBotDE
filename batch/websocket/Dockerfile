FROM python:3.11


RUN pip3 install --no-cache --upgrade pip setuptools

RUN mkdir -p /opt/opa/cryptobot
WORKDIR /opt/opa/
ADD cryptobot/ cryptobot/
ADD batch/websocket/start_realtime_data_collector_websocket.py .
ADD batch/websocket/realtime_data_collector.py .
ADD batch/websocket/requirements.txt .
ADD config.yml .

RUN pip install -r ./requirements.txt

CMD python start_realtime_data_collector_websocket.py
