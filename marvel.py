import json

# Nom du fichier JSON
QNAMES_FILE = 'Qnames.json'

def save_quantum_data(quantum_names, ground_state_numbers):
    """Enregistre les noms des nombres quantiques et les nombres quantiques de l'état fondamental dans un fichier JSON."""
    data = {
        'quantum_names': quantum_names,
        'ground_state_numbers': ground_state_numbers
    }
    with open(QNAMES_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Les données quantiques ont été enregistrées dans '{QNAMES_FILE}'.")

def get_quantum_names_from_user():
    """Demande à l'utilisateur de saisir les noms des nombres quantiques."""
    quantum_names = input("Entrez les noms des nombres quantiques (séparés par des espaces, par exemple 'v1 v2 l v3 J') : ").split(' ')
    return quantum_names

def get_ground_state_numbers_from_user():
    """Demande à l'utilisateur de saisir les nombres quantiques de l'état fondamental."""
    ground_state_numbers = input("Entrez les nombres quantiques de l'état fondamental (séparés par des espaces, par exemple '0 0 0 0') : ").split(' ')
    # Convertir les nombres en entiers
    ground_state_numbers = [int(num) for num in ground_state_numbers]
    return ground_state_numbers

def main():
    # Demander à l'utilisateur de saisir les noms des nombres quantiques
    quantum_names = get_quantum_names_from_user()

    # Demander à l'utilisateur de saisir les nombres quantiques de l'état fondamental
    ground_state_numbers = get_ground_state_numbers_from_user()

    # Enregistrer les données dans le fichier JSON (écrase le fichier existant)
    save_quantum_data(quantum_names, ground_state_numbers)

    # Utiliser les noms des nombres quantiques et les nombres de l'état fondamental dans le projet
    print("Noms des nombres quantiques utilisés :", quantum_names)
    print("Nombres quantiques de l'état fondamental :", ground_state_numbers)

if __name__ == "__main__":
    main()
