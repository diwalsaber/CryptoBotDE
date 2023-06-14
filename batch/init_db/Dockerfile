FROM python:3.11.4

RUN apt-get update
RUN apt-get install cron -y

RUN pip3 install --no-cache --upgrade pip setuptools
#create application user
#RUN groupadd --gid 1000 opag \
#    && useradd --uid 1000 --gid 1000 -m opa
RUN mkdir -p /opt/opa/cryptobot data_collectors
#RUN chown  -R opa /opt/opa

#USER opa
# install the application
WORKDIR /opt/opa/
ADD cryptobot/ cryptobot/
ADD batch/init_db/* .
ADD data_collectors/__init__.py data_collectors/
ADD data_collectors/history_data_collector_zip.py data_collectors/
ADD config.yml .
RUN pip install -r ./requirements.txt


# Add the cron job
RUN echo "* * * * * python /opt/opa/download_data.py" > crontab.txt
# Run the command on container startup
RUN crontab crontab.txt
CMD cron -f