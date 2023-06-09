FROM python:3.11


RUN pip3 install --no-cache --upgrade pip setuptools

RUN mkdir -p /opt/opa/cryptobot
WORKDIR /opt/opa/
ADD api/frontend/* .
ADD cryptobot/ cryptobot/
ADD config.yml .

RUN pip install -r ./requirements.txt

EXPOSE 8501
CMD python -m streamlit run Page_Principale.py
