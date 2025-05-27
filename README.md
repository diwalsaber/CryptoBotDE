# CryptoBotDE

## Présentation

CryptoBotDE est une application de trading de cryptomonnaies basée sur des modèles d'apprentissage automatique. L'application est composée d'un frontend Streamlit, d'un backend FastAPI, d'un service de données personnalisé pour la collecte de données historiques, et d'Apache Airflow pour l'automatisation des tâches.

## Architecture des Données

Le système de gestion des données de CryptoBotDE est conçu pour assurer à la fois un chargement initial robuste des données historiques et des mises à jour incrémentales efficaces.

### Flux de Données - Chargement Initial

1.  **Source** : API Binance (pour les données de marché historiques de BTCUSDT).
2.  **Traitement** : Le script `data/binance_to_db.py` (exécuté par le service Docker `history`) récupère un volume important de données historiques.
3.  **Staging en Parquet** : Avant l'insertion en base, les données collectées sont converties en DataFrame Pandas et sauvegardées temporairement au format Apache Parquet dans le répertoire `data/parquet_files_output/` (sur l'hôte). Ce format colonnaire est optimisé pour le stockage et les requêtes analytiques, offrant une compression efficace et une préservation des types de données. Cette étape de staging permet également de découpler la collecte de l'écriture en base et facilite d'éventuelles analyses ou traitements batch ultérieurs sur les fichiers Parquet.
4.  **Stockage Final** : Les données sont ensuite lues depuis les fichiers Parquet et insérées dans une base de données TimescaleDB, optimisée pour les séries temporelles.

### Flux de Données - Mises à Jour Incrémentales

1.  **Source** : API Binance.
2.  **Orchestration** : Un DAG Apache Airflow (`airflow/dags/update_db_dag.py`) s'exécute toutes les 15 minutes.
3.  **Traitement** : Le DAG récupère les dernières bougies de 15 minutes pour BTCUSDT.
4.  **Stockage Direct** : Ces nouvelles données sont directement insérées dans la table TimescaleDB correspondante, assurant ainsi la fraîcheur des informations pour le backend et le frontend.

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

Lors du chargement initial, ce service récupère les données de Binance, les sauvegarde temporairement au format Apache Parquet dans le répertoire `data/parquet_files_output/` (mappé depuis `/app/parquet_data` dans le conteneur), puis les insère dans TimescaleDB. L'utilisation de Parquet permet un stockage efficace et facilite d'éventuels traitements de données futurs.

Ce service utilise une image Docker construite à partir d'un Dockerfile situé dans le répertoire `./data/`. Les logs de ce service sont stockés dans le répertoire `./logs/`.

Une fois l'application lancée avec Docker Compose, ce service est accessible via le port 8087.

Notez que ce service dépend du service `timescaledb` pour le stockage des données. Assurez-vous que le service de base de données est opérationnel avant d'essayer d'utiliser le service de données.

## Airflow

Le service Airflow, situé dans le répertoire airflow/, est utilisé pour automatiser la collecte et l'insertion de données en temps réel dans la base de données toutes les 15 minutes. Le fichier DAG qui définit cette tâche est update_db_dag.py dans le répertoire dags/.

## Installation et exécution

Pour installer et exécuter ce projet, vous devez avoir Docker et Docker Compose installés sur votre machine.

### Configuration des Clés API

Avant de lancer l'application, vous devez configurer vos clés API Binance. Ces clés sont nécessaires pour que le service de collecte de données (`history`) et Apache Airflow puissent accéder à l'API Binance.

Modifiez le fichier `docker-compose.yml` et renseignez vos clés dans les sections `environment` des services suivants :
-   `history`
-   `airflow-worker`
-   `airflow-scheduler`
-   `airflow-webserver` (recommandé pour la cohérence)

Voici un exemple pour un service :

```yaml
services:
  history: # Ou airflow-worker, etc.
    # ... autres configurations ...
    environment:
      BINANCE_API_KEY: "VOTRE_VRAIE_CLE_API"
      BINANCE_API_SECRET: "VOTRE_SECRET_API"
    # ... autres configurations ...
```

**Important** : Ne committez jamais vos clés API réelles dans un dépôt public. Si vous clonez ce projet, assurez-vous que `docker-compose.yml` avec vos clés n'est pas suivi par Git (par exemple, en l'ajoutant à `.gitignore` si ce n'est pas un fichier que vous partagez avec des clés). Pour ce projet, les clés sont lues depuis les variables d'environnement pour éviter de les écrire en dur dans le code.

Une fois que c'est fait, vous pouvez construire et exécuter l'application avec les commandes suivantes :

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

### Execution globale avec `setup.sh`
Vous pouvez aussi simplement lancer la commande suivante (assurez-vous qu'il soit exécutable avec la commande : `chmod +x setup.sh`):

`./setup.sh`

Elle resume les principales commandes décrites plus haut.


### Utilisation d'Airflow
Pour utiliser le service Airflow, suivez les étapes ci-dessous :

Naviguez vers l'interface utilisateur d'Airflow à l'adresse http://localhost:8080.
Allez à l'onglet DAGs et activez le DAG update_db_dag.
Pour exécuter le DAG, déclenchez-le manuellement pour la première fois en cliquant sur le lien du DAG update_db_dag, puis sur le bouton "Trigger DAG" en haut de l'écran.

### Fermeture des dockers
Pour arrêter et supprimer les conteneurs, le réseau et les volumes, utilisez la commande suivante :

`docker-compose down`

Pour arrêter et supprimer les conteneurs, les volumes et vider  tous les caches, utilisez la commande suivante :

`docker compose down --volumes --remove-orphans`

`docker system prune --all --force --volumes`


## Déploiement avec Google Cloud Compute

Pour déployer l'application sur une machine virtuelle Google Compute Engine, suivez les étapes ci-dessous :

1. Installez [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) sur votre machine locale.

2. Connectez-vous à votre compte Google Cloud en utilisant la commande `gcloud auth login`.

3. Configurez votre projet Google Cloud avec la commande `gcloud config set project YOUR_PROJECT_ID`.

4. Créez une instance de VM avec la commande `gcloud compute instances create INSTANCE_NAME`.

5. Connectez-vous à votre instance VM en utilisant la commande `gcloud compute ssh INSTANCE_NAME`.

6. Une fois connecté à la VM, installez Docker et Docker Compose en suivant les instructions appropriées pour le système d'exploitation de la VM.

7. Clonez le dépôt sur la VM avec la commande `git clone https://github.com/diwalsaber/CryptoBotDE.git`.

8. Naviguez dans le dossier du projet avec `cd CryptoBotDE`.

9. Suivez les instructions d'installation et d'exécution fournies ci-dessus pour construire et lancer les conteneurs Docker.

Veuillez noter que vous devrez également configurer les règles du pare-feu Google Cloud pour permettre le trafic vers les ports utilisés par vos services. Vous pouvez le faire dans la console Google Cloud en naviguant vers `VPC Network -> Firewall -> Create Firewall Rule`.

Accédez à votre application déployée en utilisant l'adresse IP externe de votre VM et le port sur lequel votre service est exposé. Par exemple, si votre service est accessible sur le port 8080, vous pouvez y accéder en utilisant `http://EXTERNAL_IP:8080`.

## Accéder à l'application déployée

Une fois l'application déployée sur Google Compute Engine, vous pouvez y accéder avec les adresses suivantes :
### Version Production
- Streamlit (frontend) : http://34.155.175.241:8501
- FastAPI (backend) : http://34.155.175.241:8001/docs
- Adminer (gestionnaire de base de données) : http://34.155.175.241:8087
- Airflow (automatisation) : http://34.155.175.241:8080
### Version Dev (AWS)
- FastAPI (backend) : http://13.37.231.40:8000/docs
- Streamlit (frontend) : http://13.37.231.40:8501


Remplacez `http://EXTERNAL_IP/` par l'adresse IP externe de votre machine virtuelle Google Compute Engine.