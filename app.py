import os
from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import sqlite3
import json
import networkx as nx
from pyvis.network import Network
import ast

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'uploads'

# Nom du fichier JSON contenant les noms des nombres quantiques
QNAMES_FILE = 'Qnames.json'

# Fonction pour charger les noms des nombres quantiques
def load_quantum_names():
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

# Fonction pour convertir les nombres quantiques en JSON
def convert_to_json(quantum_numbers_str):
    if not quantum_numbers_str or pd.isna(quantum_numbers_str):
        return json.dumps([])
    try:
        quantum_numbers = list(map(int, quantum_numbers_str.split(' ')))
        return json.dumps(quantum_numbers)
    except ValueError:
        print(f"Erreur : Impossible de convertir '{quantum_numbers_str}' en nombres quantiques.")
        return json.dumps([])

# Fonction pour créer la table transitions si elle n'existe pas
def create_transitions_table():
    conn = sqlite3.connect('marvel.db')
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()

# Route pour la page d'accueil (téléversement de fichiers)
@app.route('/', methods=['GET', 'POST'])
def index():
    show_graph_button = False  # Par défaut, le bouton est caché

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("Aucun fichier sélectionné.", "error")
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash("Aucun fichier sélectionné.", "error")
            return redirect(request.url)

        if file and file.filename.endswith('.xlsx'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            # Charger les données Excel
            df = pd.read_excel(filepath)

            # Connexion à la base de données
            conn = sqlite3.connect('marvel.db')
            cursor = conn.cursor()

            # Insérer les données dans la table transitions
            for index, row in df.iterrows():
                id_value = row.get('id')
                wavenumber = row['wavenumber']
                uncertainty = row.get('uncertainty', 0.0)
                quantum_numbers_up = convert_to_json(row.get('quantum_numbers_up', ''))
                quantum_numbers_low = convert_to_json(row.get('quantum_numbers_low', ''))
                line_status = row.get('line_status', 0)
                src_status = row.get('src_status', 0)
                src = row.get('src', '')

                if id_value is not None:
                    cursor.execute('''
                        INSERT INTO transitions (id, wavenumber, uncertainty, quantum_numbers_up, quantum_numbers_low, line_status, src_status, src)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (id_value, wavenumber, uncertainty, quantum_numbers_up, quantum_numbers_low, line_status, src_status, src))
                else:
                    cursor.execute('''
                        INSERT INTO transitions (wavenumber, uncertainty, quantum_numbers_up, quantum_numbers_low, line_status, src_status, src)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (wavenumber, uncertainty, quantum_numbers_up, quantum_numbers_low, line_status, src_status, src))

            conn.commit()
            conn.close()
            flash("Données insérées avec succès !", "success")
            show_graph_button = True  # Afficher le bouton après un téléversement réussi
            return render_template('index.html', show_graph_button=show_graph_button)

        else:
            flash("Format de fichier non supporté. Veuillez téléverser un fichier Excel (.xlsx).", "error")
            return redirect(request.url)

    return render_template('index.html', show_graph_button=show_graph_button)

# Route pour afficher le graphe et les informations
@app.route('/graph')
def graph():
    # Connexion à la base de données
    conn = sqlite3.connect("marvel.db")
    cursor = conn.cursor()

    # Récupérer les transitions
    cursor.execute("SELECT id, wavenumber, quantum_numbers_up, quantum_numbers_low FROM transitions")
    transitions = cursor.fetchall()
    conn.close()

    if not transitions:
        flash("Aucune transition trouvée dans la base de données.", "error")
        return redirect(url_for('index'))

    # Créer un graphe orienté
    G = nx.DiGraph()

    # Ajouter les transitions au graphe
    for transition in transitions:
        id_transition, wavenumber, quantum_numbers_up, quantum_numbers_low = transition

        try:
            quantum_numbers_low = ast.literal_eval(quantum_numbers_low)
            quantum_numbers_up = ast.literal_eval(quantum_numbers_up)

            if isinstance(quantum_numbers_low, list):
                quantum_numbers_low = tuple(quantum_numbers_low)
            if isinstance(quantum_numbers_up, list):
                quantum_numbers_up = tuple(quantum_numbers_up)
        except (ValueError, SyntaxError):
            pass

        quantum_numbers_low_str = str(quantum_numbers_low)
        quantum_numbers_up_str = str(quantum_numbers_up)

        if quantum_numbers_low_str not in G:
            G.add_node(quantum_numbers_low_str, label=quantum_numbers_low_str)
        if quantum_numbers_up_str not in G:
            G.add_node(quantum_numbers_up_str, label=quantum_numbers_up_str)

        G.add_edge(quantum_numbers_low_str, quantum_numbers_up_str, weight=wavenumber, id=id_transition)

    # Nombre de composantes connexes
    composantes_connexes = list(nx.weakly_connected_components(G))
    nombre_composantes = len(composantes_connexes)

    # Générer le graphe PyVis
    net = Network(notebook=True, directed=True, cdn_resources='remote')
    for nœud, données in G.nodes(data=True):
        net.add_node(nœud, label=données.get("label", nœud))
    for départ, arrivée, données in G.edges(data=True):
        net.add_edge(départ, arrivée, value=données["weight"], title=f"Transition {données['id']}\nWavenumber: {données['weight']}")

    net.write_html("templates/graph.html")

    return render_template('graph.html', nombre_composantes=nombre_composantes)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Créer la table transitions si elle n'existe pas
    create_transitions_table()
    
    app.run(debug=True, port=5001)  # Changer le port si nécessaire
