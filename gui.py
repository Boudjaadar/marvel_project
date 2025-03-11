import tkinter as tk

# Créer une fenêtre
window = tk.Tk()
window.title("Mon Application")

# Ajouter un label
label = tk.Label(window, text="Bonjour, Tkinter!")
label.pack()

# Ajouter un bouton
button = tk.Button(window, text="Cliquez-moi", command=lambda: print("Bouton cliqué!"))
button.pack()

# Lancer la boucle principale
window.mainloop()
