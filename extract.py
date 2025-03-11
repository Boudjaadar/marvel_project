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
quantum_names = load_quantum_names()
if not quantum_names:
    exit(1)  # Arrêter le script si les noms ne peuvent pas être chargés

# Se connecter à la base de données SQLite
conn = sqlite3.connect('marvel.db')
cursor = conn.cursor()

# Construire la requête SQL pour extraire les nombres quantiques sous forme de liste JSON
query = """
SELECT 
    id, 
    wavenumber, 
    quantum_numbers_up AS quantum_up,
    quantum_numbers_low AS quantum_down
FROM transitions;
"""

# Exécuter la requête
cursor.execute(query)
rows = cursor.fetchall()

# Afficher les résultats
for row in rows:
    id, wavenumber, quantum_up, quantum_down = row
    # Convertir les chaînes JSON en listes Python
    quantum_up = json.loads(quantum_up)
    quantum_down = json.loads(quantum_down)
    print(f"ID: {id}, Wavenumber: {wavenumber}, Quantum Up: {quantum_up}, Quantum Down: {quantum_down}")

# Fermer la connexion
conn.close()
