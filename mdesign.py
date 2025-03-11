import sqlite3
from bidict import bidict
import json
import numpy as np
import pandas as pd  # Bibliothèque Pandas pour les DataFrames

# Se connecter à la base de données SQLite
conn = sqlite3.connect('marvel.db')
cursor = conn.cursor()

# Créer un bidictionnaire vide
niveaux_energie = bidict()

# Compteur pour les numéros séquentiels
compteur = 0

# Fonction pour explorer la table des transitions et remplir le bidictionnaire
def explorer_transitions_et_remplir_bidict():
    global compteur  # Utiliser le compteur global

    # Exécuter une requête pour lire tous les enregistrements de la table transitions
    cursor.execute('SELECT id, wavenumber, quantum_numbers_up, quantum_numbers_low FROM transitions')
    rows = cursor.fetchall()

    # Parcourir chaque enregistrement
    for row in rows:
        quantum_numbers_up = row[2]  # Nombres quantiques de l'état supérieur
        quantum_numbers_low = row[3]  # Nombres quantiques de l'état inférieur

        # Convertir les chaînes JSON en listes Python
        try:
            liste_up = json.loads(quantum_numbers_up)  # Convertir "[1, 2, 3]" en [1, 2, 3]
            liste_low = json.loads(quantum_numbers_low)  # Convertir "[0, 1, 2]" en [0, 1, 2]
        except json.JSONDecodeError:
            print(f"Erreur : Impossible de parser les nombres quantiques : {quantum_numbers_up} ou {quantum_numbers_low}")
            continue

        # Convertir les listes en tuples
        tuple_up = tuple(liste_up)
        tuple_low = tuple(liste_low)

        # Ajouter les tuples au bidictionnaire avec un numéro séquentiel
        if tuple_up not in niveaux_energie:
            niveaux_energie[tuple_up] = compteur
            compteur += 1  # Incrémenter le compteur

        if tuple_low not in niveaux_energie:
            niveaux_energie[tuple_low] = compteur
            compteur += 1  # Incrémenter le compteur

# Appeler la fonction pour explorer la table et remplir le bidictionnaire
explorer_transitions_et_remplir_bidict()

# Charger les nombres quantiques de l'état fondamental depuis Qnames.json
with open('Qnames.json', 'r') as f:
    qnames_data = json.load(f)
    fondamental = tuple(qnames_data['ground_state_numbers'])  # Convertir en tuple

# Récupérer le numéro attribué à l'état fondamental
if fondamental in niveaux_energie:
    fondamental_num = niveaux_energie[fondamental]
else:
    raise ValueError("L'état fondamental n'a pas été trouvé dans le bidictionnaire.")

# Fonction pour générer la matrice de design
def generer_matrice_design():
    # Récupérer toutes les transitions
    cursor.execute('SELECT id, quantum_numbers_up, quantum_numbers_low FROM transitions')
    rows = cursor.fetchall()

    # Nombre de transitions
    nb_transitions = len(rows)

    # Initialiser une matrice carrée de zéros
    matrice_design = np.zeros((nb_transitions, compteur), dtype=int)

    # Remplir la matrice de design
    for i, row in enumerate(rows):
        quantum_numbers_up = json.loads(row[1])  # Nombres quantiques de l'état supérieur
        quantum_numbers_low = json.loads(row[2])  # Nombres quantiques de l'état inférieur

        # Convertir en tuples
        tuple_up = tuple(quantum_numbers_up)
        tuple_low = tuple(quantum_numbers_low)

        # Récupérer les numéros associés
        num_up = niveaux_energie[tuple_up]
        num_low = niveaux_energie[tuple_low]

        # Remplir la matrice
        if num_up != fondamental_num:
            matrice_design[i, num_up] = 1  # 1 pour le niveau supérieur
        if num_low != fondamental_num:
            matrice_design[i, num_low] = -1  # -1 pour le niveau inférieur

    return matrice_design

# Générer la matrice de design
matrice_design = generer_matrice_design()

# Convertir la matrice de design en DataFrame Pandas
df_matrice_design = pd.DataFrame(matrice_design)

# Ajouter des noms de colonnes pour plus de clarté
df_matrice_design.columns = [f"Niveau_{i}" for i in range(compteur)]

# Enregistrer le DataFrame dans un fichier Excel
df_matrice_design.to_excel('matrice_design.xlsx', index=False)
print("La matrice de design a été enregistrée dans 'matrice_design.xlsx'.")

# Fermer la connexion à la base de données
conn.close()
