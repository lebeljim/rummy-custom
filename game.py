import random

COULEURS = ['Rouge', 'Bleu', 'Jaune', 'Noir']
VALEURS = list(range(1, 14))

class Tuile:
    def __init__(self, valeur, couleur, est_joker=False):
        self.valeur = valeur
        self.couleur = couleur
        self.est_joker = est_joker

    def __repr__(self):
        if self.est_joker:
            return "[ 🃏 J ]"
        return f"[{self.valeur:2d} {self.couleur[:1]}]"

class Deck:
    def __init__(self):
        self.tuiles = []
        for _ in range(2):
            for c in COULEURS:
                for v in VALEURS:
                    self.tuiles.append(Tuile(v, c))
        self.tuiles.append(Tuile(0, 'Joker', est_joker=True))
        self.tuiles.append(Tuile(0, 'Joker', est_joker=True))
        random.shuffle(self.tuiles)

    def piger(self):
        return self.tuiles.pop() if self.tuiles else None

class GrilleTable:
    """Représente la surface de jeu 2D."""
    def __init__(self, lignes=15, colonnes=15):
        self.lignes = lignes
        self.colonnes = colonnes
        self.grille = [[None for _ in range(colonnes)] for _ in range(lignes)]

    def poser(self, r, c, tuile):
        self.grille[r][c] = tuile

    def afficher(self):
        print("\n--- TABLE DE JEU ---")
        for r in range(self.lignes):
            ligne_str = []
            contient_tuile = False
            for c in range(self.colonnes):
                t = self.grille[r][c]
                if t is not None:
                    contient_tuile = True
                    ligne_str.append(str(t))
                else:
                    ligne_str.append("  .   ")
            if contient_tuile:
                print(f"L{r:02d}: " + " ".join(ligne_str))
        print("---------------------\n")

    def valider_colonnes(self):
        """Vérifie que les suites verticales sont de même couleur et ordonnées."""
        for c in range(self.colonnes):
            suite_actuelle = []
            for r in range(self.lignes):
                t = self.grille[r][c]
                if t is not None:
                    suite_actuelle.append(t)
                else:
                    suite_actuelle = []
        return True

class Joueur:
    def __init__(self, nom):
        self.nom = nom
        self.main = []
        self.a_ouvert = False

    def afficher_main(self):
        print(f"Main de {self.nom} ({len(self.main)} tuiles) :")
        triee = sorted(self.main, key=lambda t: (t.couleur, t.valeur))
        print(" ".join(str(t) for t in triee))

if __name__ == "__main__":
    pioche = Deck()
    table = GrilleTable(lignes=10, colonnes=10)
    
    # Exemple de pose sur la table pour tester l'affichage
    t1 = Tuile(7, 'Bleu')
    t2 = Tuile(8, 'Bleu')
    t3 = Tuile(9, 'Bleu')
    table.poser(2, 3, t1)
    table.poser(3, 3, t2)
    table.poser(4, 3, t3)
    
    table.afficher()
