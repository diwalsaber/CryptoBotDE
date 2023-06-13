FROM python:3.11.4


RUN pip3 install --no-cache --upgrade pip setuptools

RUN mkdir -p /opt/opa/cryptobot /opt/opa/pages
#create application user
RUN groupadd --gid 1000 opag \
    && useradd --uid 1000 --gid 1000 -m opa
RUN chown  -R opa /opt/opa
USER opa

WORKDIR /opt/opa/
ADD api/frontend2/*.py .
ADD api/frontend2/requirements.txt .
ADD api/frontend2/pages pages
ADD cryptobot/ cryptobot/
ADD config.yml .
RUN ls -l
RUN pip install -r ./requirements.txt

EXPOSE 8501
CMD python -m streamlit run home.py
