#chosir la version de python 
FROM python:3.13-slim

#python ne crée pas de fichier .pyc (pour eviter les problème)
ENV PYTHONDONTWRITEBYTECODE=1

#voir les message python en direcr (pas de delais)
ENV PYTHONUNBUFFERED=1

#la maison de l'app dans le conteneur
WORKDIR /app

#on install les outils nécessaires
RUN apt-get update \ 
    && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

#on copie les dependance neccessaire au bon fontionnement de du site 
COPY requirements.txt .

#installation de tout les packages copier dans le requirement.txt
RUN pip install --no-cache-dir -r requirements.txt

#copy de tout le backend django
COPY src/ .

# Créer le dossier db
RUN mkdir -p /app/db

# Donner les permissions
RUN chmod 755 /app/db

#creation de dossier pour les fichiers statics et medias
RUN mkdir -p staticfiles media 

#collecter les fichiers static au meme endroit
RUN python manage.py collectstatic --noinput

#on ecoute sur le port 8000
EXPOSE 8000
CMD [ "gunicorn", "--bind", "0.0.0.0:8000", "sanba_finflow:wsgi:application" ]

