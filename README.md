# CryptoBotDE

## Présentation

CryptoBotDE est un bot de trading de cryptomonnaies qui utilise une approche de développement front-end et back-end séparée. Le projet utilise Docker, FastAPI, et Streamlit pour la création et le déploiement des applications web.

## Structure du projet

Le projet est structuré en trois parties principales : le backend, le frontend et une partie data.

### Backend

Le backend de l'application est construit avec FastAPI et contient les éléments suivants :

- `Dockerfile` : Un script qui contient les commandes nécessaires pour construire une image Docker pour le backend de l'application.
- `lstm.h5` : Un modèle LSTM (Long Short-Term Memory) sauvegardé. Les réseaux LSTM sont souvent utilisés pour les données de séries temporelles comme les prix des actions, données météorolpgiques, etc.
- `main.py` : Le script principal qui exécute l'application backend.
- `requirements.txt` : Un fichier qui liste toutes les dépendances Python requises pour exécuter l'application backend.
- `scaler.job` : Le modèle de normalisation utilisé avant l'entraînement des données.

### Frontend

Le frontend de l'application est construit avec Streamlit et contient les éléments suivants :

- `Dockerfile` : Un script qui contient les commandes nécessaires pour construire une image Docker pour le frontend de l'application.
- `requirements.txt` : Un fichier qui liste toutes les dépendances Python requises pour exécuter l'application frontend.
- `ui.py` : Le script principal qui exécute l'application frontend.

## Data (Service de données)

Ce projet comprend un service de données nommé `history`, qui est un service personnalisé défini dans le fichier `docker-compose.yml`. Ce service est responsable de la collecte et du stockage des données historiques nécessaires pour l'application.

Ce service utilise une image Docker construite à partir d'un Dockerfile situé dans le répertoire `./data/`. Les logs de ce service sont stockés dans le répertoire `./logs/`.

Une fois l'application lancée avec Docker Compose, ce service est accessible via le port 8000.

Notez que ce service dépend du service `timescaledb` pour le stockage des données. Assurez-vous que le service de base de données est opérationnel avant d'essayer d'utiliser le service de données.


## Installation et exécution

Pour installer et exécuter ce projet, vous devez avoir Docker et Docker Compose installés sur votre machine. Une fois que c'est fait, vous pouvez construire et exécuter l'application avec les commandes suivantes :

### Cloner le dépôt
`git clone https://github.com/diwalsaber/CryptoBotDE.git`
`cd CryptoBotDE`

### Construire et lancer les conteneurs Docker
`docker-compose up -d`

Une fois l'application en cours d'exécution, vous pouvez accéder aux différentes interfaces de l'application en ouvrant votre navigateur web et en naviguant vers les adresses suivantes :

Streamlit (frontend) : http://localhost:8501
FastAPI (backend) : http://localhost:8001/docs
Adminer (gestionnaire de base de données) : http://localhost:8080
Pour vous connecter à Adminer, utilisez les informations suivantes :

Système : PostgreSQL
Serveur : timescaledb
Utilisateur : postgres
Mot de passe : postgres
Base de données : postgres

Pour arrêter et supprimer les conteneurs, le réseau et les volumes, utilisez la commande suivante :

`docker-compose down`