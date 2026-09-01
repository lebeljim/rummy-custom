import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.parse
import urllib.request
import copy
import os
import subprocess

COULEURS = ['Rouge', 'Bleu', 'Jaune', 'Noir']
VALEURS = list(range(1, 14))

def generer_reponse_ia(prompt_systeme, historique):
    url = "http://localhost:11434/api/generate"
    contexte = "\n".join([f"{'IA' if m['role']=='bot' else 'Joueur'}: {m['texte']}" for m in historique[-6:]])
    prompt_complet = f"{prompt_systeme}\n\nHistorique récent:\n{contexte}\nIA (réponds en 1 seule phrase naturelle et amicale):"
    
    payload = {
        "model": "llama3.2:3b",
        "prompt": prompt_complet,
        "stream": False,
        "options": {
            "temperature": 0.75,
            "num_predict": 60
        }
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5.0) as res:
            data = json.loads(res.read().decode('utf-8'))
            rep = data.get('response', '').strip().replace('"', '')
            if rep:
                return rep
    except Exception as e:
        print("Erreur IA:", e)
        pass
    
    secours = [
        "C'est à ton tour, mon ami.",
        "Je surveille tes tuiles, vas-y.",
        "Intéressant, montre-moi ton prochain coup.",
        "La table se remplit bien, à toi."
    ]
    return random.choice(secours)

def generer_audio(texte):
    chemin_mp3 = os.path.expanduser('~/rummy-custom/reponse.mp3')
    try:
        subprocess.run(['python3', '-m', 'edge_tts', '--voice', 'fr-CA-AntoineNeural', '--text', texte, '--write-media', chemin_mp3], check=True)
    except Exception as e:
        print("Erreur Audio:", e)

class EtatJeu:
    def __init__(self):
        self.system_prompt = (
            "Tu es un ami québécois qui joue à une partie de Rummy amicale. "
            "Tu es chaleureux, naturel, conversationnel et intelligent. "
            "Ne te répète jamais. Prends en compte l'historique de la conversation. "
            "Réponds toujours par une seule phrase courte, comme un vrai humain qui discute en jouant."
        )
        self.reinitialiser()

    def ajouter_message_bot(self, texte, avec_voix=True):
        if texte and texte.strip():
            self.chat_history.append({'role': 'bot', 'texte': texte.strip()})
            if len(self.chat_history) > 30:
                self.chat_history.pop(0)
            if avec_voix:
                generer_audio(texte.strip())

    def ajouter_message_user(self, texte):
        if texte and texte.strip():
            self.chat_history.append({'role': 'user', 'texte': texte.strip()})
            rep_ia = generer_reponse_ia(self.system_prompt, self.chat_history)
            self.ajouter_message_bot(rep_ia, avec_voix=True)

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
        
        self.lignes = 13
        self.colonnes = 8
        self.grille = [[None for _ in range(self.colonnes)] for _ in range(self.lignes)]
        self.chat_history = []
        self.grille_debut_tour = copy.deepcopy(self.grille)
        self.main_debut_tour = list(self.main_joueur)
        self.ajouter_message_bot("Salut! La table est prête, on va avoir du fun.", avec_voix=True)

    def piger_joueur(self):
        self.grille = copy.deepcopy(self.grille_debut_tour)
        self.main_joueur = list(self.main_debut_tour)
        if self.tuiles:
            self.main_joueur.append(self.tuiles.pop())
            if random.random() < 0.3:
                phrases_pige = ["Une de plus pour toi.", "La pioche peut être traître.", "Bonne chance avec celle-là."]
                self.ajouter_message_bot(random.choice(phrases_pige), avec_voix=True)
        self.grille_debut_tour = copy.deepcopy(self.grille)
        self.main_debut_tour = list(self.main_joueur)
        self.tour_du_bot()

    def poser_depuis_main(self, idx_main, r, c):
        if 0 <= idx_main < len(self.main_joueur) and self.grille[r][c] is None:
            self.grille[r][c] = self.main_joueur.pop(idx_main)
            return True
        return False

    def deplacer_sur_grille(self, r1, c1, r2, c2):
        if self.grille[r1][c1] is not None and self.grille[r2][c2] is None:
            self.grille[r2][c2] = self.grille[r1][c1]
            self.grille[r1][c1] = None
            return True
        return False

    def deplacer_colonne_entiere(self, c1, c2):
        if 0 <= c1 < self.colonnes and 0 <= c2 < self.colonnes:
            for r in range(self.lignes):
                self.grille[r][c1], self.grille[r][c2] = self.grille[r][c2], self.grille[r][c1]
            return True
        return False

    def ramener_dans_main(self, r, c):
        if self.grille[r][c] is not None:
            t = self.grille[r][c]
            if not t.get('joker'):
                self.main_joueur.append(t)
                self.grille[r][c] = None
                return True
        return False

    def echanger_dans_main(self, idx1, idx2):
        if 0 <= idx1 < len(self.main_joueur) and 0 <= idx2 < len(self.main_joueur):
            self.main_joueur[idx1], self.main_joueur[idx2] = self.main_joueur[idx2], self.main_joueur[idx1]
            return True
        return False

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

    def valider_fin_tour_joueur(self):
        points_debut = sum(t['valeur'] for t in self.main_debut_tour)
        points_fin = sum(t['valeur'] for t in self.main_joueur)
        points_poses = points_debut - points_fin
        
        if len(self.main_joueur) == len(self.main_debut_tour):
            return False

        if not self.a_ouvert_joueur:
            if points_poses < 24:
                self.ajouter_message_bot("Il te faut 24 points pour ta première ouverture, réessaie.", avec_voix=True)
                self.grille = copy.deepcopy(self.grille_debut_tour)
                self.main_joueur = list(self.main_debut_tour)
                return False
            self.a_ouvert_joueur = True

        if not self.valider_table():
            self.ajouter_message_bot("La table n'est pas valide, vérifie tes suites.", avec_voix=True)
            self.grille = copy.deepcopy(self.grille_debut_tour)
            self.main_joueur = list(self.main_debut_tour)
            return False

        if len(self.main_joueur) == 0:
            self.ajouter_message_bot("Wow, tu as vidé ta main ! Superbe partie.", avec_voix=True)
            return True

        if random.random() < 0.2:
            self.ajouter_message_bot("Beau jeu, à mon tour.", avec_voix=True)

        self.grille_debut_tour = copy.deepcopy(self.grille)
        self.main_debut_tour = list(self.main_joueur)
        self.tour_du_bot()
        return True

    def tour_du_bot(self):
        main_bot_triee = sorted(self.main_bot, key=lambda x: (x['couleur'], x['valeur']))
        coup_trouve = False

        if self.a_ouvert_bot:
            for idx, t in enumerate(list(self.main_bot)):
                r = 13 - t['valeur']
                for c in range(self.colonnes):
                    if self.grille[r][c] is None:
                        self.grille[r][c] = t
                        if self.valider_table():
                            self.main_bot.remove(t)
                            coup_trouve = True
                            break
                        else:
                            self.grille[r][c] = None
                if coup_trouve: break

        if not coup_trouve:
            for i in range(len(main_bot_triee) - 2):
                for j in range(i + 2, len(main_bot_triee)):
                    sous_groupe = main_bot_triee[i:j+1]
                    if len(sous_groupe) >= 3:
                        clr = sous_groupe[0]['couleur']
                        if all(t['couleur'] == clr for t in sous_groupe):
                            vals = [t['valeur'] for t in sous_groupe]
                            if vals == list(range(vals[0], vals[0] + len(vals))):
                                pts = sum(vals)
                                if self.a_ouvert_bot or pts >= 24:
                                    for c in range(self.colonnes):
                                        col_occupee = any(self.grille[r][c] is not None for r in range(self.lignes))
                                        if not col_occupee:
                                            for t in sous_groupe:
                                                r = 13 - t['valeur']
                                                self.grille[r][c] = t
                                            if self.valider_table():
                                                for t in sous_groupe:
                                                    self.main_bot.remove(t)
                                                self.a_ouvert_bot = True
                                                coup_trouve = True
                                                break
                                            else:
                                                for t in sous_groupe:
                                                    r = 13 - t['valeur']
                                                    self.grille[r][c] = None
                    if coup_trouve: break
                if coup_trouve: break

        if not coup_trouve and self.tuiles:
            self.main_bot.append(self.tuiles.pop())

        self.grille_debut_tour = copy.deepcopy(self.grille)

jeu = EtatJeu()

class RequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)

        if parsed.path == '/':
            chemin_html = os.path.expanduser('~/rummy-custom/index.html')
            with open(chemin_html, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content)
            
        elif parsed.path == '/reponse.mp3':
            chemin_mp3 = os.path.expanduser('~/rummy-custom/reponse.mp3')
            if os.path.exists(chemin_mp3):
                with open(chemin_mp3, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'audio/mpeg')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404)

        elif parsed.path == '/api/state':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            data = {'main': jeu.main_joueur, 'bot_count': len(jeu.main_bot), 'grille': jeu.grille, 'chat': jeu.chat_history}
            self.wfile.write(json.dumps(data).encode('utf-8'))

        elif parsed.path == '/api/place':
            jeu.poser_depuis_main(int(qs['idx'][0]), int(qs['r'][0]), int(qs['c'][0]))
            self.send_response(200); self.end_headers()

        elif parsed.path == '/api/move':
            jeu.deplacer_sur_grille(int(qs['r1'][0]), int(qs['c1'][0]), int(qs['r2'][0]), int(qs['c2'][0]))
            self.send_response(200); self.end_headers()

        elif parsed.path == '/api/move_column':
            jeu.deplacer_colonne_entiere(int(qs['c1'][0]), int(qs['c2'][0]))
            self.send_response(200); self.end_headers()

        elif parsed.path == '/api/return':
            jeu.ramener_dans_main(int(qs['r'][0]), int(qs['c'][0]))
            self.send_response(200); self.end_headers()

        elif parsed.path == '/api/swap_hand':
            jeu.echanger_dans_main(int(qs['idx1'][0]), int(qs['idx2'][0]))
            self.send_response(200); self.end_headers()

        elif parsed.path == '/api/draw':
            jeu.piger_joueur()
            self.send_response(200); self.end_headers()

        elif parsed.path == '/api/end_turn':
            jeu.valider_fin_tour_joueur()
            self.send_response(200); self.end_headers()

        elif parsed.path == '/api/chat_user':
            msg = qs['msg'][0]
            jeu.ajouter_message_user(msg)
            self.send_response(200); self.end_headers()

        else:
            self.send_error(404)

if __name__ == '__main__':
    port = 8080
    print(f"Serveur Casino IA Actif : http://localhost:{port}")
    server = HTTPServer(('0.0.0.0', port), RequestHandler)
    server.serve_forever()
