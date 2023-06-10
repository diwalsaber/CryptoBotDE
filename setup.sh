#!/bin/bash

# Cloner le dépôt
git clone https://github.com/diwalsaber/CryptoBotDE.git

# Se déplacer dans le répertoire du projet
cd CryptoBotDE

# Créer la variable d'environnement AIRFLOW_UID
echo -e "AIRFLOW_UID=$(id -u)" > .env

# Créer les répertoires nécessaires pour les volumes montés
mkdir -p ./airflow/logs ./airflow/plugins ./airflow/config

# Construire et lancer les conteneurs Docker
docker-compose up --build -d
