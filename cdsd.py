import pandas as pd

# Définition des noms des colonnes
column_names = [
    "Molecule Number", "Isotopologue Index", "Vacuum Wavenumber", "Intensity",
    "Einstein A-coefficient", "Air-broadened Half-width", "Self-broadened Half-width",
    "Lower State Energy", "Temperature Exponent (γ_air)", "Air Pressure Shift",
    "Upper State v1", "Upper State v2", "Upper State l2", "Upper State v3",
    "Upper State r", "Lower State v1", "Lower State v2", "Lower State l2",
    "Lower State v3", "Lower State r", "Temp Exponent (γ_self)", "Self Pressure Shift",
    "Branch", "Lower State J", "Lower State Wang Symmetry", "Uncertainty Indices",
    "Reference Indices", "Upper State Weight", "Lower State Weight"
]

def safe_int(value, default=0):
    """ Convertit en entier, retourne `default` si vide ou invalide """
    return int(value) if value.strip().isdigit() else default

def safe_float(value, default=0.0):
    """ Convertit en float, retourne `default` si vide ou invalide """
    try:
        return float(value.strip())
    except ValueError:
        return default

def read_cdsd_file(filename):
    data = []

    with open(filename, 'r') as file:
        for line_num, line in enumerate(file, start=1):  # Ajout du numéro de ligne pour debug
            line = line.rstrip("\n")  # Supprimer le saut de ligne

            if len(line) < 134:
                print(f"⚠️ Ligne {line_num} ignorée (trop courte) : {repr(line)}")
                continue  # Ignore la ligne et passe à la suivante

            row = [
                safe_int(line[0:2]),     # Molecule Number
                line[2:3].strip(),       # Isotopologue Index
                safe_float(line[3:15]),  # Vacuum Wavenumber
                safe_float(line[15:25]), # Intensity
                safe_float(line[25:35]), # Einstein A-coefficient
                safe_float(line[35:40]), # Air-broadened Half-width
                safe_float(line[40:45]), # Self-broadened Half-width
                safe_float(line[45:55]), # Lower State Energy
                safe_float(line[55:59]), # Temperature Exponent (γ_air)
                safe_float(line[59:67]), # Air Pressure Shift
                safe_int(line[67:69]),   # Upper State v1
                safe_int(line[69:71]),   # Upper State v2
                safe_int(line[71:73]),   # Upper State l2
                safe_int(line[73:75]),   # Upper State v3
                safe_int(line[75:76]),   # Upper State r
                safe_int(line[76:78]),   # Lower State v1
                safe_int(line[78:80]),   # Lower State v2
                safe_int(line[80:82]),   # Lower State l2
                safe_int(line[82:84]),   # Lower State v3
                safe_int(line[84:85]),   # Lower State r
                safe_float(line[85:89]), # Temp Exponent (γ_self)
                safe_float(line[89:97]), # Self Pressure Shift
                line[97:98].strip(),     # Branch
                safe_int(line[98:101]),  # Lower State J
                line[101:102].strip(),   # Lower State Wang Symmetry
                line[102:108].strip(),   # Uncertainty Indices
                line[108:120].strip(),   # Reference Indices
                safe_float(line[120:127]), # Upper State Weight
                safe_float(line[127:134])  # Lower State Weight
            ]

            data.append(row)

    df = pd.DataFrame(data, columns=column_names)
    return df

# 📌 Lecture du fichier (remplace 'cdsd296v1' par le vrai nom de ton fichier)
df_cdsd = read_cdsd_file('cdsd296v1')

# 📌 Affichage des premières lignes du fichier sous forme de tableau
print(df_cdsd.head())
