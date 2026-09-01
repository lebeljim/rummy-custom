import random
import copy

COULEURS = ['Rouge', 'Bleu', 'Jaune', 'Noir']
VALEURS = list(range(1, 14))

class MoteurRummy:
    def __init__(self):
        self.reinitialiser()

    def reinitialiser(self):
        self.tuiles = []
        for _ in range(2):
            for c in COULEURS:
                for v in VALEURS:
                    self.tuiles.append({'valeur': v, 'couleur': c, 'joker': False})
        self.tuiles.append({'valeur': 0, 'couleur': 'Joker', 'joker': True})
        self.tuiles.append({'valeur': 0, 'couleur': 'Joker', 'joker': True})
        random.shuffle(self.tuiles)

        self.main_joueur = [self.tuiles.pop() for _ in range(14)]
        self.main_bot = [self.tuiles.pop() for _ in range(14)]
        self.a_ouvert_joueur = False
        self.a_ouvert_bot = False
        self.partie_terminee = False
        self.message_fin = ""
        
        self.lignes = 13
        self.colonnes = 8
        self.grille = [[None for _ in range(self.colonnes)] for _ in range(self.lignes)]
        self.grille_debut_tour = copy.deepcopy(self.grille)
        self.main_debut_tour = list(self.main_joueur)

    def valider_table(self):
        colonnes_couleur = {}
        for c in range(self.colonnes):
            couleur_col = None
            for r in range(self.lignes):
                t = self.grille[r][c]
                if t is not None and not t['joker']:
                    if couleur_col is None:
                        couleur_col = t['couleur']
                    elif t['couleur'] != couleur_col:
                        return False
            if couleur_col is not None:
                if couleur_col not in colonnes_couleur:
                    colonnes_couleur[couleur_col] = []
                colonnes_couleur[couleur_col].append(c)

        for clr, cols in colonnes_couleur.items():
            if len(cols) > 2:
                return False
            if len(cols) == 2:
                if abs(cols[0] - cols[1]) < 3:
                    return False

        valides = [[False for _ in range(self.colonnes)] for _ in range(self.lignes)]
        for c in range(self.colonnes):
            r = 0
            while r < self.lignes:
                if self.grille[r][c] is not None:
                    segment = []
                    while r < self.lignes and self.grille[r][c] is not None:
                        segment.append((r, self.grille[r][c]))
                        r += 1
                    if len(segment) >= 3:
                        ok = True
                        for i in range(len(segment) - 1):
                            if segment[i+1][0] != segment[i][0] + 1:
                                ok = False
                        if ok:
                            for sr, _ in segment:
                                valides[sr][c] = True
                else:
                    r += 1

        for r in range(self.lignes):
            c = 0
            while c < self.colonnes:
                if self.grille[r][c] is not None:
                    segment = []
                    while c < self.colonnes and self.grille[r][c] is not None:
                        segment.append((c, self.grille[r][c]))
                        c += 1
                    if len(segment) >= 3:
                        ok = True
                        val_att = 13 - r
                        for sc, t in segment:
                            if not t['joker'] and t['valeur'] != val_att:
                                ok = False
                        for i in range(len(segment) - 1):
                            t1, t2 = segment[i][1], segment[i+1][1]
                            if not t1['joker'] and not t2['joker'] and t1['couleur'] == t2['couleur']:
                                ok = False
                        if ok:
                            for sc, _ in segment:
                                valides[r][sc] = True
                else:
                    c += 1

        for r in range(self.lignes):
            for c in range(self.colonnes):
                if self.grille[r][c] is not None and not valides[r][c]:
                    return False
        return True