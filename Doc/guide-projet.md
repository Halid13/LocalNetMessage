# Guide Approfondi du Projet LocalNetMessage

## 1. Objectif et Vue d’Ensemble
LocalNetMessage est une messagerie locale simple permettant à un serveur d’administrer et de dialoguer avec des clients sur un réseau local.
- Cœur technique: sockets TCP pour le transport, Flask + Socket.IO pour l’interface temps réel.
- Deux interfaces Web:
  - `server_web.py` (administration): supervision des clients, envoi de messages ciblés, historique.
  - `client_web.py` (client): connexion à un serveur TCP et chat via navigateur.

## 2. Composants et Ports
- Serveur TCP intégré dans `server_web.py`:
  - Hôte: `0.0.0.0`
  - Port: `12345`
- Serveur Web d’administration (`server_web.py`): `http://127.0.0.1:5000`
- Client Web (`client_web.py`): `http://127.0.0.1:5001`
- Remarque côté client: le code prévoit un port par défaut `5555` si non fourni. Pour se connecter au serveur web ci-dessus, saisissez/paramétrez `12345` comme port TCP.

## 3. Architecture Fonctionnelle
- Transport: TCP pur entre le serveur et chaque client.
- Temps réel UI: Flask-SocketIO pousse les événements navigateur ↔ Python.
- Threads:
  - 1 thread d’acceptation TCP dans `server_web.py`.
  - 1 thread par client TCP pour gérer réception/fermeture.
  - 1 thread de réception côté `client_web.py` pour ne pas bloquer l’UI web.
- Stockage en mémoire:
  - `server_web.py` maintient un dictionnaire `clients` avec historique par client.

### 3.1 Flux Général
1. Lancement `server_web.py` → démarre l’écoute TCP (12345) + serveur Flask-SocketIO (5000).
2. Un client se connecte (ex: via `client_web.py`) au port TCP 12345 et envoie son username en premier message.
3. Le serveur crée un `client_id`, stocke les infos, envoie au client `__SERVER_NAME__:<NomServeur>`.
4. À chaque message reçu du client: stockage dans l’historique et diffusion à l’interface web d’admin.
5. Depuis l’interface d’admin: sélection d’un client, consultation de l’historique, envoi de messages ciblés.
6. Fin de conversation par mots-clés (ex: "quit") ou fermeture de socket → nettoyage + notification UI.

## 4. Événements Socket.IO (UI ↔ Python)
- Côté serveur (`server_web.py`):
  - Entrants: `get_client_messages`, `mark_messages_read`, `send_message`, `connect_to_server` (simulation depuis UI), `connect`/`disconnect`.
  - Sortants: `clients_update`, `client_connected`, `client_disconnected`, `message_received`, `message_sent`, `client_messages`, `messages_marked_read`, `connection_error`, `error`.
- Côté client (`client_web.py`):
  - Entrants: `connect_to_server`, `send_message`, `disconnect_from_server`, `connect`/`disconnect`.
  - Sortants: `connected`, `message_received`, `message_sent`, `disconnected`, `connection_error`, `error`.

## 5. Format des Données et Historique
- Messages stockés côté serveur dans `clients[client_id]['messages']`:
```json
{
  "type": "received" | "sent",
  "sender": "<username|Serveur>",
  "message": "<texte>",
  "timestamp": "ISO-8601",
  "read": false
}
```
- `mark_messages_read` met à jour `read = true` pour les messages `received`.
- Le client web ne conserve pas d’historique local durable; l’UI affiche les flux en temps réel.

## 6. Fonctionnalités Clés
- Supervision des clients (liste en temps réel, connexion/déconnexion).
- Historique par client côté serveur, avec statut de lecture.
- Envoi ciblé serveur → client.
- Réception en temps réel client → serveur (affiché côté admin).
- Nom du serveur personnalisable via `/set_server_username`.
- Mots-clés d’arrêt (ex: `quit`, `exit`, `au revoir`) pour mettre fin proprement à une session.

## 7. Lancement et Utilisation
### 7.1 Prérequis
- Python 3.9+
- Dépendances: `pip install -r requirements.txt`

### 7.2 Démarrage (PowerShell)
```powershell
python server_web.py
```
- Admin UI: ouvrir `http://127.0.0.1:5000`

```powershell
python client_web.py
```
- Client UI: ouvrir `http://127.0.0.1:5001`
- Saisir IP/port du serveur TCP: utiliser `127.0.0.1:12345` en local.

### 7.3 Test local rapide
- Dans l’UI client: renseigner un pseudo et se connecter sur `127.0.0.1:12345`.
- Dans l’UI serveur: sélectionner le client, envoyer/recevoir des messages.
- Utiliser un mot-clé de sortie pour fermer proprement.

## 8. Gestion des Erreurs et Déconnexions
- Côté client: erreurs surfacent via événements `error`/`connection_error` (ex: serveur non démarré, message vide, > 5000 chars).
- Côté serveur: validation message, erreurs d’envoi, suppression propre du client en `finally`.
- Déconnexions: détectées par lecture `recv()` vide côté client/serveur.

## 9. Sécurité et Limites Actuelles
- Transport TCP non chiffré (LAN seulement recommandé).
- Aucune authentification intégrée.
- Historique en mémoire (perdu au redémarrage).
- Pas de quotas/rate limiting.

## 10. Configuration et Personnalisation
- Nom du serveur: `POST /set_server_username` avec `{ "username": "MonServeur" }`.
- Ports: modifier `PORT` dans `server_web.py`; côté client, renseigner le même port dans l’UI.
- Messages de sortie: adapter `EXIT_KEYWORDS` dans les deux fichiers.

## 11. Structure des Fichiers
- `server_web.py`: serveur TCP + UI admin Flask-SocketIO (port 5000).
- `client_web.py`: UI client Flask-SocketIO (port 5001) + pont vers TCP.
- `templates/`: `server.html`, `client.html` pour les interfaces.
- `static/`: CSS modernes et assets.
- `README.md`: guide rapide.
- `Doc/`: documents explicatifs (ce guide, etc.).
- `documentation/`: autres docs techniques (si présent dans le repo).

## 12. Pistes d’Amélioration (Résumé)
- Persistance SQLite/PostgreSQL des messages.
- Authentification et autorisations.
- HTTPS/TLS (ou proxy Nginx en frontal).
- Observabilité (métriques, logs structurés).
- Gestion fichiers (upload) et recherche.
- Reconnexion automatique côté client.

---
Ce guide couvre l’architecture, les flux, la configuration et l’usage courant de LocalNetMessage. Pour des détails par fichier, voir `Doc/server_web.md` et `Doc/client_web.md` (ou leurs équivalents dans `documentation/`).