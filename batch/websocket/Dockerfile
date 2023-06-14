FROM python:3.11.4


RUN pip3 install --no-cache --upgrade pip setuptools
RUN mkdir -p /opt/opa/cryptobot
#create application user
RUN groupadd --gid 1000 opag \
    && useradd --uid 1000 --gid 1000 -m opa
RUN chown  -R opa /opt/opa
USER opa
WORKDIR /opt/opa/
ADD cryptobot/ cryptobot/
ADD batch/websocket/start_realtime_data_collector_websocket.py .
ADD batch/websocket/realtime_data_collector.py .
ADD batch/websocket/requirements.txt .
ADD config.yml .

RUN pip install -r ./requirements.txt

CMD python start_realtime_data_collector_websocket.py
