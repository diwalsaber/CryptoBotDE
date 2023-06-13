FROM python:3.11.4


RUN pip3 install --no-cache --upgrade pip setuptools

RUN mkdir -p /opt/opa/cryptobot /opt/opa/data_collectors /opt/opa/models

#create application user
RUN groupadd --gid 1000 opag \
    && useradd --uid 1000 --gid 1000 -m opa
RUN chown  -R opa /opt/opa
USER opa

WORKDIR /opt/opa/
ADD tmp/requirements.txt .

RUN pip install -r ./requirements.txt
