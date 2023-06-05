FROM ubuntu:latest

#create the environment
RUN  apt-get update
RUN  apt-get -y install python3-pip
RUN  apt-get -y install htop

#install packages
RUN  apt-get update
RUN  apt-get install cron
RUN  apt-get update
RUN  apt-get -y  install wget
RUN  apt-get install unzip


#create a new user for the app
RUN rm -rf /usr/crypto/src
RUN mkdir -p /usr/crypto/src
RUN addgroup --system cryptogroup
RUN adduser --system --home /usr/crypto crypto
RUN usermod -g cryptogroup crypto
# Chown all the files to the app user.
RUN chown -R crypto:cryptogroup /usr/crypto

# Switch to 'crypto'
USER crypto

# install requirements first
RUN pip3 install --upgrade pip
RUN pip3 install --upgrade setuptools

WORKDIR /usr/crypto/src
RUN wget https://github.com/diwalsaber/CryptoBotDE/archive/refs/heads/main.zip
RUN unzip main.zip
RUN mv CryptoBotDE-main/* .
RUN pip3 install -r ./requirements.txt


#RUN crontab -l > mycron
#RUN echo "0 0 0 1/1 * ? * python3 -m data_collectors.copy_realtime_to_history_data" >> mycron
#RUN crontab mycron
#RUN rm mycron
RUN sed 's/127.0.0.1/CryptoBot/g' data_collectors/config.yml > data_collectors/config.yml
RUN python3 -m data_collectors.init_db
#RUN python3 -m data_collectors.start_websocket_and_recover_missing_history.py&


#TODO FastAPI


