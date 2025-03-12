#!/bin/bash

# Vérifier si un message de commit est fourni
if [ -z "$1" ]; then
  echo "Veuillez entrer un message de commit."
  exit 1
fi

# Ajouter tous les fichiers modifiés
git add .

# Faire un commit avec le message fourni
git commit -m "$1"

# Récupérer les dernières modifications du dépôt distant
git push origin main
