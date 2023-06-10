FROM apache/airflow:2.6.1-python3.9
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
USER airflow
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" python-binance==1.0.17
USER airflow