import sqlite3
from bidict import bidict
import json
import pandas as pd
from scipy.sparse import coo_matrix, csr_matrix, diags
import numpy as np
from scipy.linalg import cho_factor, cho_solve

# Se connecter à la base de données SQLite
conn = sqlite3.connect('marvel.db')
cursor = conn.cursor()

# Charger les nombres quantiques de l'état fondamental depuis Qnames.json
with open('Qnames.json', 'r') as f:
    qnames_data = json.load(f)
    fondamental = tuple(qnames_data['ground_state_numbers'])  # Convertir en tuple

# Lire ground_energy_status depuis le clavier
ground_energy_status = int(input("Entrez la valeur de ground_energy_status (0 'fixed' ou 1 'free') : "))
if ground_energy_status not in [0, 1]:
    raise ValueError("La valeur de ground_energy_status doit être 0 ou 1.")

# Fonction pour explorer les transitions d'une composante connexe et remplir le bidictionnaire
def explorer_transitions_et_remplir_bidict(component_id):
    global compteur  # Utiliser le compteur global

    # Récupérer les transitions de la composante connexe
    cursor.execute('''
        SELECT id, wavenumber, uncertainty, quantum_numbers_up, quantum_numbers_low 
        FROM components 
        WHERE component = ?
    ''', (component_id,))
    rows = cursor.fetchall()

    # Parcourir chaque enregistrement
    for row in rows:
        quantum_numbers_up = row[3]  # Nombres quantiques de l'état supérieur
        quantum_numbers_low = row[4]  # Nombres quantiques de l'état inférieur

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
        # Ignorer le niveau fondamental si ground_energy_status == 0
        if ground_energy_status == 1 or tuple_up != fondamental:
            if tuple_up not in niveaux_energie:
                niveaux_energie[tuple_up] = compteur
                compteur += 1  # Incrémenter le compteur

        if ground_energy_status == 1 or tuple_low != fondamental:
            if tuple_low not in niveaux_energie:
                niveaux_energie[tuple_low] = compteur
                compteur += 1  # Incrémenter le compteur

# Fonction pour générer la matrice de design en représentation COO pour une composante connexe
# ici
def generer_matrice_design_coo(component_id):
    # Récupérer les transitions de la composante connexe
    cursor.execute('''
        SELECT id, wavenumber, uncertainty, quantum_numbers_up, quantum_numbers_low 
        FROM components 
        WHERE component = ?
    ''', (component_id,))
    rows = cursor.fetchall()

    # Initialiser des listes pour les indices et les valeurs non nulles
    lignes = []  # Indices de ligne
    colonnes = []  # Indices de colonne
    valeurs = []  # Valeurs non nulles

    # Remplir les listes pour la représentation COO
    for i, row in enumerate(rows):
        quantum_numbers_up = json.loads(row[3])  # Nombres quantiques de l'état supérieur
        quantum_numbers_low = json.loads(row[4])  # Nombres quantiques de l'état inférieur

        # Convertir en tuples
        tuple_up = tuple(quantum_numbers_up)
        tuple_low = tuple(quantum_numbers_low)

        # Récupérer les numéros associés
        num_up = niveaux_energie.get(tuple_up, None)  # Utiliser None si le niveau n'est pas dans le dictionnaire
        num_low = niveaux_energie.get(tuple_low, None)

        # Ajouter les éléments non nuls
        if num_up is not None and (ground_energy_status == 1 or tuple_up != fondamental):
            lignes.append(i)
            colonnes.append(num_up)
            valeurs.append(1)  # 1 pour le niveau supérieur

        if num_low is not None and (ground_energy_status == 1 or tuple_low != fondamental):
            lignes.append(i)
            colonnes.append(num_low)
            valeurs.append(-1)  # -1 pour le niveau inférieur

    # Créer la matrice COO avec la taille correcte
    nombre_transitions = len(rows)  # Nombre de transitions
    nombre_niveaux_energie = compteur  # Nombre de niveaux d'énergie
    taille_A = (nombre_transitions, nombre_niveaux_energie)  # Taille de la matrice A
    print(f"Taille de la matrice A pour la composante {component_id} : {taille_A}")

    matrice_coo = coo_matrix((valeurs, (lignes, colonnes)), shape=taille_A)
    return matrice_coo, rows
# Récupérer la liste des composantes connexes
cursor.execute('SELECT DISTINCT component FROM components')
components = cursor.fetchall()

# Boucle sur chaque composante connexe
for component in components:
    component_id = component[0]
    print(f"\nTraitement de la composante connexe {component_id}...")

    # Réinitialiser le bidictionnaire et le compteur pour chaque composante
    niveaux_energie = bidict()
    compteur = 0

    # Explorer les transitions et remplir le bidictionnaire
    explorer_transitions_et_remplir_bidict(component_id)

    # Générer la matrice de design en représentation COO
    matrice_coo, rows = generer_matrice_design_coo(component_id)

    # Supprimer les doublons dans la matrice COO
    matrice_coo.sum_duplicates()

    # Convertir la matrice COO en CSR
    matrice_csr = matrice_coo.tocsr()

    # Récupérer les valeurs de wavenumber et uncertainty pour construire les poids
    wavenumbers = np.array([row[1] for row in rows])
    uncertainties = np.array([row[2] for row in rows])
    # Calculer les poids w = 1 / (uncertainty ** 2)
    weights = 1 / (uncertainties ** 2)
    W = diags(weights)

    # Construire le système linéaire M x = y
    A = matrice_csr  # La matrice de design en format CSR
    b = wavenumbers  # Le vecteur des wavenumbers

    # Calculer M = A^T W A
    M = A.T @ W @ A

    # Calculer y = A^T W b
    y = A.T @ W @ b

    # Résoudre le système M x = y en utilisant la décomposition de Cholesky
    try:
        # Factorisation de Cholesky
        c, lower = cho_factor(M.toarray())  # Convertir M en format dense pour Cholesky
        # Résolution du système
        x = cho_solve((c, lower), y)
        print(f"Résolution du système linéaire pour la composante {component_id} réussie.")
    except Exception as e:
        print(f"Erreur lors de la résolution du système linéaire pour la composante {component_id} : {e}")
        continue

    # Sauvegarder les résultats
    np.savetxt(f'energies_component_{component_id}.txt', x)
    print(f"Les énergies calculées pour la composante {component_id} ont été sauvegardées dans 'energies_component_{component_id}.txt'.")

# Fermer la connexion à la base de données
conn.close()
