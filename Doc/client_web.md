# Documentation du Code `client_web.py`

## Rôle Général
`client_web.py` implémente l'interface Web côté *client* permettant à un utilisateur de:
- Se connecter au serveur TCP (adresse + port + pseudo)
- Envoyer des messages au serveur
- Recevoir des messages émis par le serveur
- Gérer la déconnexion manuelle ou automatique (mots-clés de sortie)

Il agit comme un pont entre le navigateur (Socket.IO) et le serveur TCP bas niveau (socket Python).

## Stack Technique
- Flask: sert la page HTML (`client.html`)
- Flask-SocketIO: canal temps réel entre navigateur et application Python
- socket (TCP): connexion bas niveau au serveur (port par défaut 5555 dans ce fichier, mais le projet normalise sur 12345 côté serveur principal)
- threading: thread séparé pour la réception non bloquante
- **SQLite** (via `database.py`): persistance messages et fichiers locaux
- **Chiffrement léger côté navigateur**: XOR + double Base64 via `static/encryption.js`; clé partagée manuellement et stockée en localStorage

## Variables Globales Principales
- `client_socket`: socket TCP actif vers le serveur
- `connected`: booléen indiquant l'état de connexion TCP
- `receive_thread`: thread qui écoute en permanence les messages du serveur
- `username`: pseudo de l'utilisateur courant envoyé au serveur
- `server_display_name`: nom d'affichage du serveur (peut être mis à jour dynamiquement via message spécial)
- `message_counter`: compteur pour générer des IDs uniques localement
- `EXIT_KEYWORDS`: liste de chaînes déclenchant la fin de conversation
- `db`: instance SQLite (classe `Database` du module `database.py`) pour persistance locale

## Flux de Connexion
1. Le navigateur émet l'événement Socket.IO `connect_to_server` avec `username`, `server_ip`, `server_port`.
2. Le serveur Flask crée un socket TCP et se connecte.
3. Le pseudo (`username`) est envoyé immédiatement comme premier payload TCP.
4. Le thread `receive_messages` démarre pour écouter en continu.
5. Un événement Socket.IO `connected` est renvoyé au navigateur pour mise à jour UI.

### Chiffrement côté UI (panneau 🔒 dans `client.html`)
- Générer une clé sur un navigateur (bouton «🔄 Nouvelle Clé») puis copier.
- Sur l'autre pair, coller la clé dans «Importer une Clé» et cliquer «📥 Importer».
- Activer le toggle de chiffrement des deux côtés ; les messages `[ENCRYPTED]...` seront déchiffrés si la clé est identique.
- La clé est conservée dans localStorage ; réimporter si le stockage est vidé ou si vous changez de navigateur. Les fichiers ne sont pas chiffrés.

## Réception des Messages (`receive_messages`)
Boucle tant que `connected` est vrai:
- Lit jusqu'à 1024 octets, décode en UTF-8
- Si vide: déclenche une déconnexion (serveur coupé)
- Si le message commence par `__SERVER_NAME__:` -> met à jour `server_display_name`
- Sinon: émet `message_received` au navigateur avec le contenu + nom serveur
- Si un mot-clé de sortie est détecté: stoppe la boucle et émet `disconnected`
Gestion des exceptions: envoie un événement `error` côté web si problème de réception.

## Envoi de Messages (`handle_send_message`)
Étapes:
1. Validation: non vide, taille ≤ 5000, état connecté
2. Génération d'un ID unique: `client_<compteur>_<timestamp_ms>`
3. Envoi sur le socket TCP (`client_socket.send`) en UTF-8
4. Émission de `message_sent` vers le navigateur avec l'ID pour confirmation UI
5. **Sauvegarde dans SQLite** via `db.save_message(1, 'sent', username, message, timestamp)`
6. Si mot-clé de sortie envoyé: planifie la fermeture (`threading.Timer`) pour permettre une éventuelle réponse serveur

## Gestion Déconnexion
- `disconnect_from_server`: ferme le socket, remet `client_socket` à `None`, marque `connected = False`
- Événements déclencheurs: mot-clé de sortie (client ou serveur), fermeture serveur, action utilisateur `disconnect_from_server`.

## Transfert de Fichiers

### Stockage Local
Le code crée et utilise plusieurs répertoires pour stocker les fichiers:
- `CLIENT_RECEIVED_DIR = "uploads/client/received/"`: fichiers reçus du serveur
- `CLIENT_SENT_DIR = "uploads/client/sent/"`: copies des fichiers envoyés au serveur

Ces répertoires sont créés au démarrage si non présents (`Path(...).mkdir(parents=True, exist_ok=True)`).

### Envoi de Fichiers (`handle_send_file`)
Fonction décorée `@socketio.on('send_file')` qui:
1. Reçoit un événement du navigateur avec `filename`, `mimetype`, `base64_data`
2. Valide: vérification de taille (max 2 Mo), validation du nom de fichier
3. Encode le fichier en format `__FILE__|<filename>|<mimetype>|<size>|<base64_data>`
4. Envoie sur le socket TCP via `client_socket.send()` en UTF-8
5. Sauvegarde une copie locale dans `CLIENT_SENT_DIR/<filename>`
6. Émet un événement Socket.IO `file_sent` au navigateur avec un lien de téléchargement local

**Sérialisation TCP**: le format est `__FILE__|filename|mimetype|size|base64\n` (newline-delimited pour permettre un parsing buffurisé).

### Réception de Fichiers (intégrée dans `receive_messages`)
Le thread de réception détecte les lignes commençant par `__FILE__|`:
1. Analyse la ligne: extraction de `filename`, `mimetype`, `size`, `base64_data`
2. Décodage base64 → données binaires
3. Sauvegarde en `CLIENT_RECEIVED_DIR/<filename>`
4. Émet un événement Socket.IO `file_received` avec lien de téléchargement

### Routes Flask de Téléchargement
```python
@app.route('/files/client/<path:filepath>')
```
Sert les fichiers depuis `uploads/client/{received|sent}/<filepath>` avec le bon `Content-Type` pour les navigateurs (inline pour images/PDFs, attachment pour autres).

## Événements Socket.IO pour Fichiers
| Événement (Entrant)   | Fonction                 | Rôle |
|-----------------------|--------------------------|------|
| `send_file`           | `handle_send_file`       | Reçoit fichier base64 du navigateur, envoie sur TCP |

| Événement (Sortant)   | Déclencheur              | Payload |
|-----------------------|--------------------------|---------|
| `file_sent`           | Après envoi TCP + sauvegarde | `{filename, link}` |
| `file_received`       | Thread reçoit `__FILE__` | `{filename, link}` |

### Flux Typique de Transfert
**Client envoie fichier au serveur:**
1. Utilisateur clique 📎 dans `client.html`, sélectionne un fichier
2. JavaScript: `FileReader.readAsDataURL(file)` → base64
3. Émet `send_file` Socket.IO
4. `handle_send_file`: encode, envoie sur TCP, sauvegarde localement
5. Interface montre lien dans l'historique

**Client reçoit fichier du serveur:**
1. Serveur TCP envoie: `__FILE__|photo.jpg|image/jpeg|5120|[base64]`
2. Thread reçeption détecte `__FILE__`, décode base64, sauvegarde
3. Émet `file_received` Socket.IO
4. Interface affiche le fichier téléchargeable

## Limitations et Notes de Sécurité
- **Taille max**: 2 Mo (overhead base64 ~33% ; éviter gros fichiers)
- **Chiffrement**: fichiers transmis en clair sur TCP (pas de TLS par défaut)
- **Noms**: dénudés de chemins (`/`, `..` stripés) pour éviter path traversal
- **Stockage**: `uploads/` peut croître; nettoyer régulièrement si nombreux transferts



## Événements Socket.IO Exposés
| Événement (Entrant)        | Fonction                      | Rôle |
|---------------------------|-------------------------------|------|
| `connect`                 | `handle_connect`              | Log simple connexion web |
| `disconnect`              | `handle_disconnect`           | Ferme TCP si ouvert |
| `connect_to_server`       | `handle_connect_to_server`    | Lance la connexion TCP |
| `send_message`            | `handle_send_message`         | Validation + envoi message |
| `disconnect_from_server`  | `handle_disconnect_request`   | Déconnexion manuelle |

| Événement (Sortant)     | Déclencheur / Source              | Payload |
|-------------------------|------------------------------------|---------|
| `connected`             | Après connexion TCP               | IP, port, username |
| `message_received`      | Thread réception (message normal) | Texte, `server_username` |
| `message_sent`          | Après envoi                       | Texte, ID de message |
| `error`                 | Exceptions diverses               | Message d'erreur |
| `disconnected`          | Fin de session                    | Raison |
| `connection_error`      | Échec connexion initiale          | Détail |

## Nom du Serveur Dynamique
Le serveur TCP peut envoyer une ligne spéciale `__SERVER_NAME__:<nom>` interceptée pour mettre à jour `server_display_name`. Cela permet une personnalisation côté serveur sans recharger l'UI client.

## Points d'Amélioration Potentiels
- Externaliser la logique dans une classe (éviter variables globales)
- Ajout d'un mécanisme de reconnexion automatique (retry exponentiel)
- Chiffrement TLS côté TCP (actuellement clair)
- Normaliser le port par configuration (`.env` ou fichier YAML)
- Ajout de journalisation structurée (niveau + timestamp) au lieu de `print`
- Gestion binaire / fichiers (actuellement texte brut uniquement)

## Séquence Type
1. L'utilisateur charge `/` -> `client.html`
2. Remplit le formulaire et déclenche `connect_to_server`
3. Commence à envoyer des messages (`send_message`)
4. Reçoit messages push (`message_received`)
5. Utilise mot-clé "quit" ou bouton déconnexion -> arrêt contrôlé

## Lancement
Le fichier lance Flask-SocketIO sur `http://localhost:5001` (paramétrable). Exécution directe:
```bash
python client_web.py
```

## Persistance SQLite

### Initialisation de la Base de Données Client
Au démarrage, un objet `db = Database('client_messages.db')` est créé (BD distincte du serveur) avec trois tables:
- `messages`: tous les messages reçus/envoyés au serveur
- `files`: métadonnées des fichiers reçus/envoyés
- `client_history`: (non utilisée côté client, mais initialisée)

### Sauvegarde Automatique
Chaque interaction client est enregistrée (client_id = 1, constant pour le client local):

**Messages reçus du serveur:**
```python
timestamp = datetime.now().isoformat()
db.save_message(1, 'received', server_display_name, line, timestamp)
```

**Messages envoyés au serveur:**
```python
timestamp = datetime.now().isoformat()
db.save_message(1, 'sent', username, message, timestamp)
```

**Fichiers reçus du serveur:**
```python
db.save_file(
    1,
    filename,
    mimetype,
    file_size,
    'received',
    server_display_name,
    file_path,
    timestamp
)
```

**Fichiers envoyés au serveur:**
```python
db.save_file(
    1,
    filename,
    mimetype,
    file_size,
    'sent',
    username,
    file_path,
    timestamp
)
```

### Avantages
- **Historique persistant**: retrouvez tous vos messages/fichiers même après redémarrage
- **Export**: possibilité d'exporter l'historique en JSON via `db.export_to_json(1, 'export.json')`
- **Archivage**: nettoyage auto possible via `db.delete_old_messages(days=30)`
- **Audit**: trace complète de votre activité

## Résumé
`client_web.py` encapsule un client TCP classique derrière une couche Web temps réel avec persistance SQLite automatique. Il orchestre la connexion, la translation des événements Socket.IO vers des opérations socket brutes, la sauvegarde durable de tous les échanges, et la remontée d'un flux de messages vers l'UI moderne.
