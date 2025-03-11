import os
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import sqlite3
import json
import networkx as nx
from pyvis.network import Network
import ast

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx'}

# Nom du fichier JSON contenant les noms des nombres quantiques
QNAMES_FILE = 'Qnames.json'

# Créer le dossier uploads s'il n'existe pas
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Fonction pour vérifier l'extension des fichiers
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

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

# Route pour la page d'accueil
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Vérifier si un fichier a été téléversé
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # Sauvegarder le fichier téléversé
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)

            # Charger les données du fichier Excel
            df = pd.read_excel(filename)

            # Se connecter à la base de données
            conn = sqlite3.connect('marvel.db')
            cursor = conn.cursor()

            # Insérer les données dans la base de données
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

            # Sauvegarder et fermer la connexion
            conn.commit()
            conn.close()

            return redirect(url_for('index'))
    return render_template('index.html')

# Route pour générer le graphe
@app.route('/generate_graph', methods=['GET'])
def generate_graph():
    # Se connecter à la base de données
    conn = sqlite3.connect('marvel.db')
    cursor = conn.cursor()

    # Récupérer les transitions
    cursor.execute("SELECT id, wavenumber, quantum_numbers_up, quantum_numbers_low FROM transitions")
    transitions = cursor.fetchall()
    conn.close()

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

    # Générer le graphe avec PyVis
    net = Network(notebook=True, directed=True, cdn_resources='remote')
    for nœud, données in G.nodes(data=True):
        net.add_node(nœud, label=données.get("label", nœud))
    for départ, arrivée, données in G.edges(data=True):
        wavenumber = données["weight"]
        id_transition = données["id"]
        net.add_edge(départ, arrivée, value=wavenumber, title=f"Transition {id_transition}\nWavenumber: {wavenumber}")

    # Sauvegarder le graphe en HTML
    net.write_html('templates/graph.html')

    return redirect(url_for('show_graph'))

# Route pour afficher le graphe
@app.route('/graph')
def show_graph():
    return render_template('graph.html')

# Route pour afficher le nombre de composantes connexes
@app.route('/components')
def show_components():
    # Se connecter à la base de données
    conn = sqlite3.connect('marvel.db')
    cursor = conn.cursor()

    # Récupérer les transitions
    cursor.execute("SELECT quantum_numbers_up, quantum_numbers_low FROM transitions")
    transitions = cursor.fetchall()
    conn.close()

    # Créer un graphe orienté
    G = nx.DiGraph()

    # Ajouter les transitions au graphe
    for transition in transitions:
        quantum_numbers_up, quantum_numbers_low = transition

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

        G.add_edge(quantum_numbers_low_str, quantum_numbers_up_str)

    # Calculer le nombre de composantes connexes
    composantes_connexes = list(nx.weakly_connected_components(G))
    nombre_composantes = len(composantes_connexes)

    return render_template('components.html', nombre_composantes=nombre_composantes)

if __name__ == '__main__':
    app.run(debug=True)
