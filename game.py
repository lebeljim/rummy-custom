import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.parse
import urllib.request
import copy
import os
import subprocess
import threading

from moteur_rummy import MoteurRummy
from bot_ia import BotStrategique

def generer_reponse_ia(prompt_systeme, historique):
    url = "http://localhost:11434/api/generate"
    contexte = "\n".join([f"{'IA' if m['role']=='bot' else 'Joueur'}: {m['texte']}" for m in historique[-4:]])
    prompt_complet = f"{prompt_systeme}\n\nContexte:\n{contexte}\nRéponds très brièvement, agressivement ou selon ta personnalité (maximum 15 mots) :"
    
    payload = {
        "model": "llama3.2:3b",
        "prompt": prompt_complet,
        "stream": False,
        "options": {"temperature": 0.8, "num_predict": 25}
    }
    try:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}, method='POST'
        )
        with urllib.request.urlopen(req, timeout=3.0) as res:
            data = json.loads(res.read().decode('utf-8'))
            rep = data.get('response', '').strip().replace('"', '')
            if rep: return rep
    except Exception as e:
        print("Erreur IA:", e)
    return "À toi de jouer."

def generer_audio_async(texte):
    # Exécution en arrière-plan pour ne pas bloquer le serveur web et accélération de la voix
    def tache():
        dossier_actuel = os.path.dirname(os.path.abspath(__file__))
        chemin_mp3 = os.path.join(dossier_actuel, 'reponse.mp3')
        try:
            subprocess.run([
                'python', '-m', 'edge_tts', 
                '--voice', 'fr-CA-AntoineNeural', 
                '--text', texte, 
                '--rate', '+15%', 
                '--write-media', chemin_mp3
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print("Erreur Audio:", e)
    threading.Thread(target=tache, daemon=True).start()

class EtatJeuGlobal(MoteurRummy):
    def __init__(self):
        super().__init__()
        self.bot_strategie = BotStrategique()
        self.personnalites = {
            "amical": "Tu es un ami québécois chaleureux.",
            "agressif": "Tu es un joueur agacé et provocateur.",
            "sarcastique": "Tu es un partenaire cynique.",
            "introverti": "Tu es un joueur très silencieux.",
            "irritable": "Tu es impatient et tu t'énerves vite.",
            "perplexe": "Tu es sans cesse confus."
        }
        self.mode_actuel = "amical"
        self.system_prompt = self.personnalites[self.mode_actuel]
        self.chat_history = []
        self.ajouter_message_bot("Salut! La partie commence, essaie de vider ton jeu.", avec_voix=True)

    def changer_personnalite(self, mode):
        if mode in self.personnalites:
            self.mode_actuel = mode
            self.system_prompt = self.personnalites[mode]
            self.ajouter_message_bot(f"*[Changement d'humeur : mode {mode}]*", avec_voix=False)

    def ajouter_message_bot(self, texte, avec_voix=True):
        if texte and texte.strip():
            self.chat_history.append({'role': 'bot', 'texte': texte.strip()})
            if len(self.chat_history) > 30: self.chat_history.pop(0)
            if avec_voix and not texte.startswith("*"): generer_audio_async(texte.strip())

    def ajouter_message_user(self, texte):
        if self.partie_terminee: return
        if texte and texte.strip():
            self.chat_history.append({'role': 'user', 'texte': texte.strip()})
            rep_ia = generer_reponse_ia(self.system_prompt, self.chat_history)
            self.ajouter_message_bot(rep_ia, avec_voix=True)

    def piger_joueur(self):
        if self.partie_terminee: return
        self.restaurer_main_et_grille()
        if self.tuiles:
            self.main_joueur.append(self.tuiles.pop())
            if random.random() < 0.3:
                self.ajouter_message_bot("Encore une pioche?", avec_voix=True)
        self.enregistrer_debut_tour()
        self.tour_du_bot()

    def restaurer_main_et_grille(self):
        # Récupère toutes les tuiles placées sur la grille ce tour-ci et les remet dans la main du joueur
        for r in range(self.lignes):
            for c in range(self.colonnes):
                if self.grille[r][c] is not None and self.grille_debut_tour[r][c] is None:
                    self.main_joueur.append(self.grille[r][c])
        self.grille = copy.deepcopy(self.grille_debut_tour)

    def enregistrer_debut_tour(self):
        self.grille_debut_tour = copy.deepcopy(self.grille)
        self.main_debut_tour = list(self.main_joueur)

    def poser_depuis_main(self, idx_main, r, c):
        if self.partie_terminee: return False
        if 0 <= idx_main < len(self.main_joueur) and self.grille[r][c] is None:
            self.grille[r][c] = self.main_joueur.pop(idx_main)
            return True
        return False

    def deplacer_sur_grille(self, r1, c1, r2, c2):
        if self.partie_terminee: return False
        if self.grille[r1][c1] is not None and self.grille[r2][c2] is None:
            self.grille[r2][c2] = self.grille[r1][c1]
            self.grille[r1][c1] = None
            return True
        return False

    def deplacer_colonne_entiere(self, c1, c2):
        if self.partie_terminee: return False
        if 0 <= c1 < self.colonnes and 0 <= c2 < self.colonnes:
            for r in range(self.lignes):
                self.grille[r][c1], self.grille[r][c2] = self.grille[r][c2], self.grille[r][c1]
            return True
        return False

    def ramener_dans_main(self, r, c):
        if self.partie_terminee: return False
        if self.grille[r][c] is not None:
            t = self.grille[r][c]
            if not t.get('joker'):
                self.main_joueur.append(t)
                self.grille[r][c] = None
                return True
        return False

    def echanger_dans_main(self, idx1, idx2):
        if self.partie_terminee: return False
        if 0 <= idx1 < len(self.main_joueur) and 0 <= idx2 < len(self.main_joueur):
            self.main_joueur[idx1], self.main_joueur[idx2] = self.main_joueur[idx2], self.main_joueur[idx1]
            return True
        return False

    def valider_fin_tour_joueur(self):
        if self.partie_terminee: return False
        
        points_debut = sum(t['valeur'] for t in self.main_debut_tour)
        points_fin = sum(t['valeur'] for t in self.main_joueur)
        points_poses = points_debut - points_fin
        
        if len(self.main_joueur) == len(self.main_debut_tour):
            return False

        if not self.a_ouvert_joueur:
            if points_poses < 24:
                self.ajouter_message_bot("Il te faut 24 points pour ouvrir.", avec_voix=True)
                self.restaurer_main_et_grille()
                return False
            self.a_ouvert_joueur = True

        if not self.valider_table():
            self.ajouter_message_bot("Ta table n'est pas valide, tes tuiles reviennent en main.", avec_voix=True)
            self.restaurer_main_et_grille()
            return False

        # Vérification si le joueur a gagné (main vide)
        if len(self.main_joueur) == 0:
            self.partie_terminee = True
            self.message_fin = "Félicitations ! Tu as gagné la partie en vidant toutes tes tuiles !"
            self.ajouter_message_bot("Incroyable, tu as gagné...", avec_voix=True)
            return True

        self.enregistrer_debut_tour()
        self.tour_du_bot()
        return True

    def tour_du_bot(self):
        if self.partie_terminee: return
        self.bot_strategie.executer_tour(self)
        self.enregistrer_debut_tour()

jeu = EtatJeuGlobal()

class RequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)

        if parsed.path == '/':
            chemin_html = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
            with open(chemin_html, 'rb') as f: content = f.read()
            self.send_response(200); self.send_header('Content-type', 'text/html; charset=utf-8'); self.end_headers()
            self.wfile.write(content)
            
        elif parsed.path == '/reponse.mp3':
            chemin_mp3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reponse.mp3')
            if os.path.exists(chemin_mp3):
                with open(chemin_mp3, 'rb') as f: content = f.read()
                self.send_response(200); self.send_header('Content-type', 'audio/mpeg')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.end_headers(); self.wfile.write(content)
            else: self.send_error(404)

        elif parsed.path == '/api/state':
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            data = {
                'main': jeu.main_joueur, 
                'bot_count': len(jeu.main_bot), 
                'grille': jeu.grille, 
                'chat': jeu.chat_history, 
                'mode': jeu.mode_actuel,
                'partie_terminee': jeu.partie_terminee,
                'message_fin': jeu.message_fin
            }
            self.wfile.write(json.dumps(data).encode('utf-8'))

        elif parsed.path == '/api/set_personality':
            jeu.changer_personnalite(qs['mode'][0])
            self.send_response(200); self.end_headers()

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
            jeu.ajouter_message_user(qs['msg'][0])
            self.send_response(200); self.end_headers()

        elif parsed.path == '/api/restart':
            jeu.reinitialiser()
            self.send_response(200); self.end_headers()

        else: self.send_error(404)

if __name__ == '__main__':
    port = 8080
    print(f"Serveur Rummy Modulaire Actif : http://localhost:{port}")
    server = HTTPServer(('localhost', port), RequestHandler)
    server.serve_forever()