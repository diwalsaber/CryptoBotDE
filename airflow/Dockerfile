FROM apache/airflow:2.9.2-python3.9

# Définir ARG et ENV pour la version d'Airflow pour la cohérence
ARG AIRFLOW_VERSION=2.9.2
ENV AIRFLOW_VERSION=${AIRFLOW_VERSION}

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    procps \
    # Remplacer openjdk-11 par openjdk-17 car le 11 n'est plus disponible
    openjdk-17-jre-headless \
    curl \
    gosu \
    && mkdir -p /opt/bitnami/spark/jars && \
    # Téléchargement du driver JDBC PostgreSQL
    curl -L -o /opt/bitnami/spark/jars/postgresql-42.7.3.jar https://jdbc.postgresql.org/download/postgresql-42.7.3.jar && \
    apt-get purge -y --auto-remove curl && \
    apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Définir JAVA_HOME pour OpenJDK 17
# Le chemin exact peut varier, /usr/lib/jvm/java-17-openjdk-amd64 ou -arm64 est courant.
# Si l'architecture n'est pas spécifiée dans le nom du paquet, le chemin pourrait être plus générique.
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64 
# Tentative de chemin plus générique si le précédent ne fonctionne pas selon l'archi:
# ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk
# Ou pour être sûr, on pourrait le déterminer dynamiquement après l'installation.

# Les dépendances Python seront installées en tant qu'utilisateur airflow
USER airflow

# Copier requirements.txt si vous en avez un pour d'autres dépendances
# COPY requirements.txt /requirements.txt 
# RUN pip install --no-cache-dir -r /requirements.txt

# Installer/Mettre à jour les dépendances Airflow, Spark provider, et pyspark
RUN pip install --no-cache-dir \
    "apache-airflow==${AIRFLOW_VERSION}" \
    python-binance==1.0.17 \
    "apache-airflow-providers-apache-spark" \
    pyspark==3.5.0

# La section de patch sed est supprimée car nous mettons à jour la version.

# Revenir à l'utilisateur airflow (déjà le cas, mais pour être explicite si d'autres USER root étaient ajoutés)
USER airflow