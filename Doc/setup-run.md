# Setup & Run

## 1. Prérequis
- Python 3.9+
- Accès à un terminal (PowerShell, CMD)
- Navigateur moderne (Chrome, Edge, Firefox)

## 2. Installation des dépendances
Dans le dossier racine :

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Démarrer les services
### Serveur Web + TCP
```powershell
python .\server_web.py
```
- Interface serveur : http://localhost:5000
- Port TCP : 12345

### Client Web
Dans un second terminal :
```powershell
python .\client_web.py
```
- Interface client : http://localhost:5001

## 4. Connexion d'un client
1. Ouvrir http://localhost:5001
2. Saisir l’IP du serveur (ex: 127.0.0.1 sur la même machine)
3. Entrer un pseudo
4. Cliquer sur "Se connecter"

## 5. Tester en réseau local
Sur une autre machine du LAN :
1. Récupérer l’IP du serveur : `ipconfig`
2. Dans le client, utiliser cette IP (ex: 192.168.1.42)
3. Vérifier pare-feu : autoriser ports 5000, 5001, 12345

## 6. Mode scripts terminal (optionnel)
```powershell
python .\server.py
python .\client.py
```

## 7. Déconnexion
Utiliser un mot-clé reconnu (ex: `quit`, `au revoir`, `bye`). Le client est retiré de la liste côté serveur.

## 8. Vérification rapide
- Message envoyé côté client apparaît côté serveur
- Sélection d’un client dans l’interface serveur met à jour l’en-tête
- Le thème peut être basculé (soleil / lune)

## 9. Résolution de problèmes
| Problème | Vérification | Action |
|----------|--------------|--------|
| Client ne se connecte pas | IP correcte ? Port ouvert ? | Tester ping, vérifier pare-feu |
| Pas de messages | Socket.IO chargé ? | Actualiser, vérifier console dev navigateur |
| Port déjà utilisé | Erreur OSError au lancement | Changer port dans scripts |
| Interface vide | Fichiers CSS non chargés | Forcer refresh (Ctrl+Shift+R) |

## 10. Nettoyage / Redémarrage
Arrêter chaque service avec `Ctrl + C` dans le terminal qui l’héberge puis relancer.
