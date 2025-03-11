import sqlite3
from bidict import bidict
import json

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

# Fonction pour afficher les transitions avec les valeurs associées
def afficher_transitions_avec_valeurs():
    # Exécuter une requête pour lire tous les enregistrements de la table transitions
    cursor.execute('SELECT id, wavenumber, quantum_numbers_up, quantum_numbers_low FROM transitions')
    rows = cursor.fetchall()

    # Parcourir chaque enregistrement
    for row in rows:
        id_transition = row[0]  # ID de la transition
        wavenumber = row[1]  # Nombre d'ondes
        quantum_numbers_up = row[2]  # Nombres quantiques de l'état supérieur
        quantum_numbers_low = row[3]  # Nombres quantiques de l'état inférieur

        # Convertir les chaînes JSON en listes Python
        try:
            liste_up = json.loads(quantum_numbers_up)
            liste_low = json.loads(quantum_numbers_low)
        except json.JSONDecodeError:
            print(f"Erreur : Impossible de parser les nombres quantiques : {quantum_numbers_up} ou {quantum_numbers_low}")
            continue

        # Convertir les listes en tuples
        tuple_up = tuple(liste_up)
        tuple_low = tuple(liste_low)

        # Récupérer les valeurs associées aux niveaux d'énergie
        valeur_up = niveaux_energie[tuple_up]  # Valeur associée à l'état supérieur
        valeur_low = niveaux_energie[tuple_low]  # Valeur associée à l'état inférieur

        # Afficher les informations de la transition
        print(f"Transition ID: {id_transition}")
        print(f"Wavenumber: {wavenumber}")
        print(f"Niveau supérieur (nombres quantiques: {tuple_up}) -> Valeur associée: {valeur_up}")
        print(f"Niveau inférieur (nombres quantiques: {tuple_low}) -> Valeur associée: {valeur_low}")
        print("-" * 40)  # Séparateur visuel

# Appeler la fonction pour afficher les transitions avec les valeurs associées
afficher_transitions_avec_valeurs()

# Fermer la connexion à la base de données
conn.close()
