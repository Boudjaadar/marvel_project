import pandas as pd
import sqlite3
import json
import os

# Nom du fichier JSON contenant les noms des nombres quantiques
QNAMES_FILE = 'Qnames.json'

def load_quantum_names():
    """Charge les noms des nombres quantiques depuis le fichier JSON."""
    if os.path.exists(QNAMES_FILE):
        try:
            with open(QNAMES_FILE, 'r') as f:
                data = json.load(f)
                print("Noms des nombres quantiques chargés depuis le fichier :", data['quantum_names'])
                return data['quantum_names']
        except (json.JSONDecodeError, KeyError):
            print("Erreur : Le fichier JSON est invalide ou corrompu.")
            return None
    else:
        print(f"Erreur : Le fichier '{QNAMES_FILE}' est introuvable.")
        return None

# Charger les noms des nombres quantiques depuis le fichier JSON
quantum_numbers_names = load_quantum_names()
if not quantum_numbers_names:
    exit(1)  # Arrêter le script si les noms ne peuvent pas être chargés

# Charger le fichier Excel
df = pd.read_excel('transitions.xlsx')

# Créer ou se connecter à la base de données SQLite
conn = sqlite3.connect('marvel.db')
cursor = conn.cursor()

# Créer la table dans la base de données SQLite avec la nouvelle structure
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transitions (
        id INTEGER PRIMARY KEY,
        wavenumber REAL,
        uncertainty REAL,
        quantum_numbers_up TEXT,
        quantum_numbers_low TEXT,
        line_status INTEGER,
        src_status INTEGER,
        src TEXT
    )
''')

# Fonction pour transformer les nombres quantiques en JSON sans associer les noms
def convert_to_json(quantum_numbers_str):
    """Convertit une chaîne de nombres quantiques en JSON."""
    if not quantum_numbers_str or pd.isna(quantum_numbers_str):  # Vérifie si la chaîne est vide ou NaN
        return json.dumps([])  # Retourne une liste vide sous forme de JSON
    try:
        quantum_numbers = list(map(int, quantum_numbers_str.split(' ')))
        return json.dumps(quantum_numbers)  # Stocker les nombres quantiques sous forme de liste JSON
    except ValueError:
        print(f"Erreur : Impossible de convertir '{quantum_numbers_str}' en nombres quantiques.")
        return json.dumps([])  # Retourne une liste vide en cas d'erreur

# Insertion des données dans la base SQLite
for index, row in df.iterrows():
    # Extraire l'ID si la colonne existe, sinon laisser SQLite l'auto-générer
    id_value = row.get('id')  # Si la colonne 'id' existe dans le fichier Excel
    wavenumber = row['wavenumber']
    uncertainty = row.get('uncertainty', 0.0)  # Valeur par défaut si la colonne n'existe pas
    quantum_numbers_up = convert_to_json(row.get('quantum_numbers_up', ''))  # Gère les valeurs manquantes
    quantum_numbers_low = convert_to_json(row.get('quantum_numbers_low', ''))  # Gère les valeurs manquantes
    line_status = row.get('line_status', 0)  # Valeur par défaut si la colonne n'existe pas
    src_status = row.get('src_status', 0)  # Valeur par défaut si la colonne n'existe pas
    src = row.get('src', '')  # Valeur par défaut si la colonne n'existe pas
    
    if id_value is not None:  # Si l'ID est fourni dans le fichier Excel
        cursor.execute('''
            INSERT INTO transitions (id, wavenumber, uncertainty, quantum_numbers_up, quantum_numbers_low, line_status, src_status, src)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (id_value, wavenumber, uncertainty, quantum_numbers_up, quantum_numbers_low, line_status, src_status, src))
    else:  # Si l'ID n'est pas fourni, laisser SQLite l'auto-générer
        cursor.execute('''
            INSERT INTO transitions (wavenumber, uncertainty, quantum_numbers_up, quantum_numbers_low, line_status, src_status, src)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (wavenumber, uncertainty, quantum_numbers_up, quantum_numbers_low, line_status, src_status, src))

# Sauvegarder et fermer la connexion
conn.commit()
conn.close()

print("Données insérées avec succès !")
