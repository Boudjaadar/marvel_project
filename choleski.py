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

# Créer un bidictionnaire vide
niveaux_energie = bidict()

# Compteur pour les numéros séquentiels
compteur = 0

# Charger les nombres quantiques de l'état fondamental depuis Qnames.json
with open('Qnames.json', 'r') as f:
    qnames_data = json.load(f)
    fondamental = tuple(qnames_data['ground_state_numbers'])  # Convertir en tuple

# Lire ground_energy_status depuis le clavier
ground_energy_status = int(input("Entrez la valeur de ground_energy_status (0 'fixed' ou 1 'free') : "))
if ground_energy_status not in [0, 1]:
    raise ValueError("La valeur de ground_energy_status doit être 0 ou 1.")

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
        # Ignorer le niveau fondamental si ground_energy_status == 0
        if ground_energy_status == 1 or tuple_up != fondamental:
            if tuple_up not in niveaux_energie:
                niveaux_energie[tuple_up] = compteur
                compteur += 1  # Incrémenter le compteur

        if ground_energy_status == 1 or tuple_low != fondamental:
            if tuple_low not in niveaux_energie:
                niveaux_energie[tuple_low] = compteur
                compteur += 1  # Incrémenter le compteur

# Appeler la fonction pour explorer la table et remplir le bidictionnaire
explorer_transitions_et_remplir_bidict()

# Fonction pour générer la matrice de design en représentation COO
def generer_matrice_design_coo():
    # Récupérer toutes les transitions
    cursor.execute('SELECT id, quantum_numbers_up, quantum_numbers_low FROM transitions')
    rows = cursor.fetchall()

    # Initialiser des listes pour les indices et les valeurs non nulles
    lignes = []  # Indices de ligne
    colonnes = []  # Indices de colonne
    valeurs = []  # Valeurs non nulles

    # Remplir les listes pour la représentation COO
    for i, row in enumerate(rows):
        quantum_numbers_up = json.loads(row[1])  # Nombres quantiques de l'état supérieur
        quantum_numbers_low = json.loads(row[2])  # Nombres quantiques de l'état inférieur

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
    print(f"Taille de la matrice A : {taille_A}")

    matrice_coo = coo_matrix((valeurs, (lignes, colonnes)), shape=taille_A)
    return matrice_coo

# Générer la matrice de design en représentation COO
matrice_coo = generer_matrice_design_coo()

# Supprimer les doublons dans la matrice COO
matrice_coo.sum_duplicates()

# Convertir la matrice COO en DataFrame pour l'exportation
df_matrice_coo = pd.DataFrame({
    'Ligne': matrice_coo.row,  # Indices de ligne des éléments non nuls
    'Colonne': matrice_coo.col,  # Indices de colonne des éléments non nuls
    'Valeur': matrice_coo.data  # Valeurs des éléments non nuls
})

# Enregistrer la matrice COO dans un fichier Excel
df_matrice_coo.to_excel('matrice_design_coo.xlsx', index=False)
print("La matrice de design en représentation COO a été enregistrée dans 'matrice_design_coo.xlsx'.")

# Convertir la matrice COO en CSR
matrice_csr = matrice_coo.tocsr()

# Afficher des informations sur la matrice CSR
print("Matrice CSR :")
print(f"- Shape : {matrice_csr.shape}")
print(f"- Nombre d'éléments non nuls : {matrice_csr.nnz}")

# Convertir la matrice CSR en DataFrame pour l'exportation
lignes, colonnes = matrice_csr.nonzero()  # Indices de ligne et de colonne
valeurs = matrice_csr.data  # Valeurs non nulles

# Vérifier que les tableaux ont la même longueur
if len(lignes) == len(colonnes) == len(valeurs):
    df_matrice_csr = pd.DataFrame({
        'Ligne': lignes,  # Indices de ligne des éléments non nuls
        'Colonne': colonnes,  # Indices de colonne des éléments non nuls
        'Valeur': valeurs  # Valeurs des éléments non nuls
    })
else:
    # Afficher les incohérences
    print("Incohérence détectée :")
    print(f"- lignes : {lignes}")
    print(f"- colonnes : {colonnes}")
    print(f"- valeurs : {valeurs}")
    raise ValueError("Les tableaux d'indices et de valeurs n'ont pas la même longueur.")

# Enregistrer la matrice CSR dans un fichier Excel
df_matrice_csr.to_excel('matrice_design_csr.xlsx', index=False)
print("La matrice de design en représentation CSR a été enregistrée dans 'matrice_design_csr.xlsx'.")

# Récupérer les valeurs de wavenumber et uncertainty pour construire les poids
cursor.execute('SELECT wavenumber, uncertainty FROM transitions')
rows = cursor.fetchall()

# Extraire les wavenumbers et les incertitudes
wavenumbers = np.array([row[0] for row in rows])
uncertainties = np.array([row[1] for row in rows])

# Calculer les poids w = 1 / (uncertainty ** 2)
weights = 1 / (uncertainties ** 2)
W=diags(weights)
# Calculer le scaling factor (valeur maximale des poids)
# scaling_factor = np.max(weights)
# print(f"Scaling factor (max(weights)) : {scaling_factor}")

# Normaliser les poids
# weights_normalized = weights / scaling_factor

# Construire la matrice diagonale W avec les poids normalisés
#W = diags(weights_normalized)

# Sauvegarder wavenumbers et weights dans le même fichier
data_to_save = np.column_stack((wavenumbers, weights))  # Concaténation des deux tableaux
np.savetxt('wavenumbers_and_weights.txt', data_to_save, fmt='%.8f', header='wavenumber weight', comments='')
print("Les tableaux wavenumber et weight ont été sauvegardés dans 'wavenumbers_and_weights.txt'.")

# Construire le système linéaire M x = y
A = matrice_csr  # La matrice de design en format CSR
b = wavenumbers  # Le vecteur des wavenumbers

# Calculer M = A^T W A
M = A.T @ W @ A

# Convertir M en DataFrame pour l'exportation
M_dense = M.toarray()  # Convertir en format dense
df_M = pd.DataFrame(M_dense)

# Enregistrer M dans un fichier Excel
df_M.to_excel('matrice_M.xlsx', index=False)
print("La matrice M a été enregistrée dans 'matrice_M.xlsx'.")

# Calculer y = A^T W b
y = A.T @ W @ b

# Résoudre le système M x = y en utilisant la décomposition de Cholesky
# Vérifier que M est symétrique et définie positive
try:
    # Factorisation de Cholesky
    c, lower = cho_factor(M.toarray())  # Convertir M en format dense pour Cholesky
    # Résolution du système
    x = cho_solve((c, lower), y)
    print("Résolution du système linéaire réussie.")
except Exception as e:
    print(f"Erreur lors de la résolution du système linéaire : {e}")
    raise

# Sauvegarder les résultats
np.savetxt('energies.txt', x)
print("Les énergies calculées ont été sauvegardées dans 'energies.txt'.")

# Fermer la connexion à la base de données
conn.close()
