import sqlite3
from bidict import bidict
import json
import pandas as pd
from scipy.sparse import coo_matrix  # Pour la représentation COO

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

# Lire ground_energy_status depuis le clavier
ground_energy_status = int(input("Entrez la valeur de ground_energy_status (0 'fixed' ou 1 'free') : "))
if ground_energy_status not in [0, 1]:
    raise ValueError("La valeur de ground_energy_status doit être 0 ou 1.")

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
        num_up = niveaux_energie[tuple_up]
        num_low = niveaux_energie[tuple_low]

        # Ajouter les éléments non nuls
        if num_up != fondamental_num:
            lignes.append(i)
            colonnes.append(num_up)
            valeurs.append(1)  # 1 pour le niveau supérieur

        if num_low != fondamental_num:
            lignes.append(i)
            colonnes.append(num_low)
            valeurs.append(-1)  # -1 pour le niveau inférieur

        # Gérer le cas du niveau fondamental
        if num_up == fondamental_num:
            lignes.append(i)
            colonnes.append(num_up)
            valeurs.append(0 if ground_energy_status == 0 else -1)  # 0 ou -1 selon ground_energy_status

        if num_low == fondamental_num:
            lignes.append(i)
            colonnes.append(num_low)
            valeurs.append(0 if ground_energy_status == 0 else -1)  # 0 ou -1 selon ground_energy_status

    # Créer la matrice COO
    matrice_coo = coo_matrix((valeurs, (lignes, colonnes)), shape=(len(rows), compteur))
    return matrice_coo

# Générer la matrice de design en représentation COO
matrice_coo = generer_matrice_design_coo()

# Convertir la matrice COO en DataFrame pour l'exportation
df_matrice_coo = pd.DataFrame({
    'Ligne': matrice_coo.row,
    'Colonne': matrice_coo.col,
    'Valeur': matrice_coo.data
})

# Enregistrer le DataFrame dans un fichier Excel
df_matrice_coo.to_excel('matrice_design_coo.xlsx', index=False)
print("La matrice de design en représentation COO a été enregistrée dans 'matrice_design_coo.xlsx'.")

# Fermer la connexion à la base de données
conn.close()
