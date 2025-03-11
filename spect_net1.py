import sqlite3
import networkx as nx
from pyvis.network import Network
import ast

# Connexion à la base de données
conn = sqlite3.connect("marvel.db")
cursor = conn.cursor()

# Récupérer les transitions
cursor.execute("SELECT id, wavenumber, quantum_numbers_up, quantum_numbers_low FROM transitions")
transitions = cursor.fetchall()
conn.close()

# Vérification des données
if not transitions:
    print("\n❌ Aucune transition trouvée dans la base de données.")
    exit()
else:
    print(f"\n✅ {len(transitions)} transitions récupérées.")


# Créer un graphe orienté
G = nx.DiGraph()

# Ajouter les transitions au graphe
for transition in transitions:
    id_transition, wavenumber, quantum_numbers_up, quantum_numbers_low = transition
    
    # Convertir les nombres quantiques en tuples (si nécessaire)
    try:
        quantum_numbers_low = ast.literal_eval(quantum_numbers_low)
        quantum_numbers_up = ast.literal_eval(quantum_numbers_up)
        
        # Convertir les listes en tuples
        if isinstance(quantum_numbers_low, list):
            quantum_numbers_low = tuple(quantum_numbers_low)
        if isinstance(quantum_numbers_up, list):
            quantum_numbers_up = tuple(quantum_numbers_up)
    except (ValueError, SyntaxError):
        pass  # Garder sous forme de chaîne en cas d'échec
    
    # Convertir en chaînes pour PyVis
    quantum_numbers_low_str = str(quantum_numbers_low)
    quantum_numbers_up_str = str(quantum_numbers_up)
    
    # Ajouter les nœuds
    if quantum_numbers_low_str not in G:
        G.add_node(quantum_numbers_low_str, label=quantum_numbers_low_str)
    if quantum_numbers_up_str not in G:
        G.add_node(quantum_numbers_up_str, label=quantum_numbers_up_str)
    
    # Ajouter l'arête avec poids et ID de transition
    G.add_edge(quantum_numbers_low_str, quantum_numbers_up_str, weight=wavenumber, id=id_transition)
# Afficher le nombres de nœuds et arêtes pour vérification
nombre_noeuds = G.number_of_nodes()
nombre_aretes = G.number_of_edges()

print("Nombre de nœuds :", nombre_noeuds)
print("Nombre d'arêtes :", nombre_aretes)
# Détection des nœuds isolés
noeuds_isoles = [n for n in G.nodes if G.in_degree(n) == 0 and G.out_degree(n) == 0]
if noeuds_isoles:
    print("\n⚠️ Nœuds isolés détectés :", noeuds_isoles)
else:
    print("\n✅ Aucun nœud isolé détecté.")

# Vérification de la connectivité
composantes_connexes = list(nx.weakly_connected_components(G))
print("\nNombre de composantes connexes :", len(composantes_connexes))
if len(composantes_connexes) > 1:
    print("⚠️ Le réseau n'est pas entièrement connexe.")
else:
    print("✅ Le réseau est connexe.")

# Détection des cycles
try:
    cycles = list(nx.find_cycle(G))
    print("\n🔄 Cycles détectés :", cycles)
except nx.NetworkXNoCycle:
    print("\n✅ Aucun cycle détecté.")

# Calcul du chemin critique
try:
    chemin_critique = nx.dag_longest_path(G, weight="weight")
    poids_total = sum(G.edges[chemin_critique[i], chemin_critique[i+1]]['weight']
                      for i in range(len(chemin_critique) - 1))
    print("\n⭐ Chemin critique :", chemin_critique)
    print("⚡ Poids total du chemin critique :", poids_total)
except nx.NetworkXUnfeasible:
    print("\n❌ Impossible de calculer le chemin critique : le graphe contient des cycles.")

# Création du réseau PyVis
net = Network(notebook=True, directed=True, cdn_resources='remote')

# Ajouter les nœuds et les arêtes
for nœud, données in G.nodes(data=True):
    color = "red" if nœud in noeuds_isoles else "blue"
    net.add_node(nœud, label=données.get("label", nœud), color=color)

for départ, arrivée, données in G.edges(data=True):
    wavenumber = données["weight"]
    id_transition = données["id"]
    net.add_edge(départ, arrivée, value=wavenumber, title=f"Transition {id_transition}\nWavenumber: {wavenumber}")

# Activer la physique et les boutons
net.toggle_physics(True)
net.show_buttons(filter_=['physics'])

# Génération et affichage
net.write_html("spectroscopic_network.html")
print("\n✅ Graphe généré : ouvrez spectroscopic_network.html dans un navigateur.")



