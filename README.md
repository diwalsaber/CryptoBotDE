# CryptoBotDE

## Présentation

CryptoBotDE est une application de trading de cryptomonnaies basée sur des modèles d'apprentissage automatique. L'application est composée d'un frontend Streamlit, d'un backend FastAPI, d'un service de données personnalisé pour la collecte de données historiques, et d'Apache Airflow pour l'automatisation des tâches.

## Structure du projet

Le projet est structuré en trois parties principales : le backend, le frontend et une partie data.
```
CryptoBotDE/
├── README.md
├── airflow/
│   ├── Dockerfile
│   ├── config/
│   ├── dags/
│   │   ├── update_db_dag.py
│   ├── logs/
│   └── plugins/
├── backend/
│   ├── Dockerfile
│   ├── lstm.h5
│   ├── main.py
│   ├── requirements.txt
│   └── scaler.job
├── data/
│   ├── Dockerfile
│   ├── binance_to_db.py
│   └── requirements.txt
├── docker-compose.yml
├── frontend/
│   ├── Dockerfile
│   ├── home.py
│   ├── pages/
│   │   ├── dashboard.py
│   │   └── prediction.py
│   └── requirements.txt
└── logs/
```

### Backend

Le backend de l'application est construit avec FastAPI et contient les éléments suivants :

- `Dockerfile` : Un script qui contient les commandes nécessaires pour construire une image Docker pour le backend de l'application.
- `lstm.h5` : Un modèle LSTM (Long Short-Term Memory) sauvegardé. Les réseaux LSTM sont souvent utilisés pour les données de séries temporelles comme les prix des actions, données météorolpgiques, etc.
- `main.py` : Le script principal qui exécute l'application backend.
- `requirements.txt` : Un fichier qui liste toutes les dépendances Python requises pour exécuter l'application backend.
- `scaler.job` : Le modèle de normalisation utilisé avant l'entraînement des données.

### Frontend

Le frontend de l'application est construit avec Streamlit et contient les éléments suivants :

Le frontend de l'application est construit avec Streamlit et contient les éléments suivants :

- `Dockerfile` : Un script qui contient les commandes nécessaires pour construire une image Docker pour le frontend de l'application.
- `home.py` : Le script principal qui exécute l'application frontend.
- `pages/` : Contient les scripts pour les différentes pages de l'application frontend.
- `requirements.txt` : Un fichier qui liste toutes les dépendances Python requises pour exécuter l'application frontend.

## Data (Service de données)

Ce projet comprend un service de données nommé `history`, qui est un service personnalisé défini dans le fichier `docker-compose.yml`. Ce service est responsable de la collecte et du stockage des données historiques nécessaires pour l'application.

Ce service utilise une image Docker construite à partir d'un Dockerfile situé dans le répertoire `./data/`. Les logs de ce service sont stockés dans le répertoire `./logs/`.

Une fois l'application lancée avec Docker Compose, ce service est accessible via le port 8087.

Notez que ce service dépend du service `timescaledb` pour le stockage des données. Assurez-vous que le service de base de données est opérationnel avant d'essayer d'utiliser le service de données.

## Airflow

Le service Airflow, situé dans le répertoire airflow/, est utilisé pour automatiser la collecte et l'insertion de données en temps réel dans la base de données toutes les 15 minutes. Le fichier DAG qui définit cette tâche est update_db_dag.py dans le répertoire dags/.

## Installation et exécution

Pour installer et exécuter ce projet, vous devez avoir Docker et Docker Compose installés sur votre machine. Une fois que c'est fait, vous pouvez construire et exécuter l'application avec les commandes suivantes :

### Cloner le dépôt
`git clone https://github.com/diwalsaber/CryptoBotDE.git`
`cd CryptoBotDE`

### Création de la variable d'environnement AIRFLOW_UID

`echo -e "AIRFLOW_UID=$(id -u)" > .env`

 La variable d'environnement doit être créée dans le même répertoire où se trouve votre fichier docker-compose.yml. Cela créera un fichier .env contenant la variable d'environnement AIRFLOW_UID avec la valeur de votre ID utilisateur.

### Création des dépendance pour airflow
Si les répertoires nécessaires pour les volumes montés ne sont pas existant il faut les créer en exécutant la commande suivante :

`mkdir -p ./airflow/dags ./airflow/logs ./airflow/plugins ./airflow/config`

### Construire et lancer les conteneurs Docker

`docker-compose up --build -d`

Une fois l'application en cours d'exécution, vous pouvez accéder aux différentes interfaces de l'application en ouvrant votre navigateur web et en naviguant vers les adresses suivantes :

- Streamlit (frontend) : http://localhost:8501
- FastAPI (backend) : http://localhost:8001/docs
- Adminer (gestionnaire de base de données) : http://localhost:8087
Pour vous connecter à Adminer, utilisez les informations suivantes :

| Informations | Valeurs      |
|--------------|--------------|
| Système      | PostgreSQL   |
| Serveur      | timescaledb  |
| Utilisateur  | postgres     |
| Mot de passe | postgres     |
| Base de données | postgres |


- Airflow (automatisation) : http://localhost:8080
Pour vous connecter à Airflow, utilisez les informations suivantes :

| Informations | Valeurs |
|--------------|---------|
| Utilisateur  | airflow |
| Mot de passe | airflow |


### Utilisation d'Airflow
Pour utiliser le service Airflow, suivez les étapes ci-dessous :

Naviguez vers l'interface utilisateur d'Airflow à l'adresse http://localhost:8080.
Allez à l'onglet DAGs et activez le DAG update_db_dag.
Pour exécuter le DAG, déclenchez-le manuellement pour la première fois en cliquant sur le lien du DAG update_db_dag, puis sur le bouton "Trigger DAG" en haut de l'écran.


Pour arrêter et supprimer les conteneurs, le réseau et les volumes, utilisez la commande suivante :

`docker-compose down`

Pour arrêter et supprimer les conteneurs, les volumes et vider  tous les caches, utilisez la commande suivante :

`docker compose down --volumes --remove-orphans`

`docker system prune --all --force --volumes`