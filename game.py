import random

COULEURS = ['Rouge', 'Bleu', 'Jaune', 'Noir']
VALEURS = list(range(1, 14))

class Tuile:
    def __init__(self, valeur, couleur, est_joker=False):
        self.valeur = valeur          # 1 à 13, ou 0 si Joker
        self.couleur = couleur        # 'Rouge', 'Bleu', 'Jaune', 'Noir', ou 'Joker'
        self.est_joker = est_joker

    def __repr__(self):
        if self.est_joker:
            return "[ 🃏 JOKER ]"
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

class Joueur:
    def __init__(self, nom):
        self.nom = nom
        self.main = []
        self.a_ouvert = False

    def afficher_main(self):
        print(f"\nMain de {self.nom} ({len(self.main)} tuiles) :")
        triee = sorted(self.main, key=lambda t: (t.couleur, t.valeur))
        print(" ".join(str(t) for t in triee))

def test_initial():
    pioche = Deck()
    print(f"Total tuiles dans la pioche : {len(pioche.tuiles)}")
    j1 = Joueur("Jimmy")
    j2 = Joueur("Robot")

    for _ in range(14):
        j1.main.append(pioche.piger())
        j2.main.append(pioche.piger())

    j1.afficher_main()
    j2.afficher_main()
    print(f"\nTuiles restantes dans la pioche : {len(pioche.tuiles)}")

if __name__ == "__main__":
    test_initial()
