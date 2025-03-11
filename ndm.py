import sqlite3
import pandas as pd
from bidict import bidict

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

        # Convertir les nombres quantiques en tuples (exemple : "1 2 3" -> (1, 2, 3))
        tuple_up = tuple(map(int, quantum_numbers_up.strip('[]').split(',')))
        tuple_low = tuple(map(int, quantum_numbers_low.strip('[]').split(',')))

        # Ajouter les tuples au bidictionnaire avec un numéro séquentiel
        if tuple_up not in niveaux_energie:
            niveaux_energie[tuple_up] = compteur
            compteur += 1  # Incrémenter le compteur

        if tuple_low not in niveaux_energie:
            niveaux_energie[tuple_low] = compteur
            compteur += 1  # Incrémenter le compteur

# Appeler la fonction pour explorer la table et remplir le bidictionnaire
explorer_transitions_et_remplir_bidict()

# Fonction pour générer un fichier Excel avec les transitions et les numéros associés
def generer_fichier_excel():
    # Exécuter une requête pour lire tous les enregistrements de la table transitions
    cursor.execute('SELECT id, wavenumber, quantum_numbers_up, quantum_numbers_low FROM transitions')
    rows = cursor.fetchall()

    # Liste pour stocker les données
    donnees = []

    # Parcourir chaque enregistrement
    for row in rows:
        id_transition = row[0]  # ID de la transition
        wavenumber = row[1]  # Nombre d'ondes
        quantum_numbers_up = row[2]  # Nombres quantiques de l'état supérieur
        quantum_numbers_low = row[3]  # Nombres quantiques de l'état inférieur

        # Convertir les nombres quantiques en tuples
        tuple_up = tuple(map(int, quantum_numbers_up.strip('[]').split(',')))
        tuple_low = tuple(map(int, quantum_numbers_low.strip('[]').split(',')))

        # Récupérer les numéros associés aux niveaux d'énergie
        numero_up = niveaux_energie[tuple_up]  # Numéro associé à l'état supérieur
        numero_low = niveaux_energie[tuple_low]  # Numéro associé à l'état inférieur

        # Ajouter les données à la liste
        donnees.append([id_transition, wavenumber, numero_up, numero_low])

    # Créer un DataFrame pandas
    df = pd.DataFrame(donnees, columns=['ID Transition', 'Wavenumber', 'Numéro Supérieur', 'Numéro Inférieur'])

    # Exporter le DataFrame en fichier Excel
    df.to_excel('transitions_avec_numeros.xlsx', index=False)
    print("Fichier Excel généré avec succès : transitions_avec_numeros.xlsx")

# Appeler la fonction pour générer le fichier Excel
generer_fichier_excel()

# Fermer la connexion à la base de données
conn.close()
