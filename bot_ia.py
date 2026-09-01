import random

class BotStrategique:
    def __init__(self):
        pass

    def executer_tour(self, etat_jeu):
        """
        Logique améliorée du bot : 
        1. Cherche à poser des suites depuis sa main.
        2. Tente de se greffer aux suites existantes sur la grille s'il a déjà ouvert.
        """
        action_effectuee = False
        
        # 1. Tentative de poser des groupes valides depuis sa main
        main_bot_triee = sorted(etat_jeu.main_bot, key=lambda x: (x['couleur'] if not x['joker'] else 'Z', x['valeur']))
        
        for i in range(len(main_bot_triee) - 2):
            for j in range(i + 2, len(main_bot_triee)):
                sous_groupe = main_bot_triee[i:j+1]
                if len(sous_groupe) >= 3:
                    vals = [t['valeur'] for t in sous_groupe if not t['joker']]
                    pts = sum(vals)
                    
                    if etat_jeu.a_ouvert_bot or pts >= 24 or len(sous_groupe) >= 3:
                        # Cherche une colonne libre ou une extension possible
                        for c in range(etat_jeu.colonnes):
                            col_occupee = any(etat_jeu.grille[r][c] is not None for r in range(etat_jeu.lignes))
                            if not col_occupee:
                                for t in sous_groupe:
                                    r = 13 - t['valeur'] if not t['joker'] else 0
                                    if 0 <= r < etat_jeu.lignes and etat_jeu.grille[r][c] is None:
                                        etat_jeu.grille[r][c] = t
                                
                                if etat_jeu.valider_table():
                                    for t in sous_groupe:
                                        if t in etat_jeu.main_bot:
                                            etat_jeu.main_bot.remove(t)
                                    etat_jeu.a_ouvert_bot = True
                                    action_effectuee = True
                                    break
                                else:
                                    # Annulation si invalide
                                    for t in sous_groupe:
                                        r = 13 - t['valeur'] if not t['joker'] else 0
                                        if 0 <= r < etat_jeu.lignes:
                                            etat_jeu.grille[r][c] = None
                        if action_effectuee: break
            if action_effectuee: break

        # Si le bot n'a rien pu poser, il pige
        if not action_effectuee and etat_jeu.tuiles:
            tuile_piochee = etat_jeu.tuiles.pop()
            etat_jeu.main_bot.append(tuile_piochee)