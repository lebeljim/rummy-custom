class BotStrategique:
    def __init__(self):
        pass

    def executer_tour(self, etat_jeu):
        if etat_jeu.partie_terminee:
            return

        action_effectuee = False
        main_bot_triee = sorted(etat_jeu.main_bot, key=lambda x: (x['couleur'] if not x['joker'] else 'Z', x['valeur']))
        
        for i in range(len(main_bot_triee) - 2):
            for j in range(i + 2, len(main_bot_triee)):
                sous_groupe = main_bot_triee[i:j+1]
                if len(sous_groupe) >= 3:
                    vals = [t['valeur'] for t in sous_groupe if not t['joker']]
                    pts = sum(vals)
                    
                    if etat_jeu.a_ouvert_bot or pts >= 24 or len(sous_groupe) >= 3:
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
                                    for t in sous_groupe:
                                        r = 13 - t['valeur'] if not t['joker'] else 0
                                        if 0 <= r < etat_jeu.lignes:
                                            etat_jeu.grille[r][c] = None
                        if action_effectuee: break
            if action_effectuee: break

        # Vérifier si le bot a gagné en vidant sa main
        if len(etat_jeu.main_bot) == 0:
            etat_jeu.partie_terminee = True
            etat_jeu.message_fin = "Le bot a vidé toutes ses tuiles et remporte la partie ! Merci d'avoir participé."
            return

        if not action_effectuee and etat_jeu.tuiles:
            tuile_piochee = etat_jeu.tuiles.pop()
            etat_jeu.main_bot.append(tuile_piochee)