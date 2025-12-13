# Documentation du Code `server_web.py`

## Rôle Général
`server_web.py` implémente le serveur principal combinant:
- Un serveur TCP qui accepte des connexions clients classiques (sockets)
- Une interface Web (Flask + Socket.IO) pour superviser, envoyer des messages ciblés, consulter l'historique, définir le nom du serveur

Il sert de point central: chaque client TCP est géré dans un thread dédié, et l'état (liste des clients + historique par client) est synchronisé vers l'interface Web en temps réel.

## Stack Technique
- Flask: sert `server.html` (UI d'administration) + route optionnelle `/client`
- Flask-SocketIO: canal temps réel navigateur ↔ serveur
- socket (TCP): écoute des connexions entrantes sur `PORT = 12345`
- threading: un thread pour le serveur TCP + un thread par client
- **SQLite** (via `database.py`): persistance messages/fichiers/clients
- **Chiffrement léger côté navigateur**: XOR + double Base64 via `static/encryption.js`; clé partagée manuellement et stockée en localStorage

## Variables & Structures
- `HOST = '0.0.0.0'`: écoute sur toutes les interfaces
- `PORT = 12345`: port TCP standardisé du projet
- `server_username`: nom d'affichage du serveur (modifiable via route POST)
- `EXIT_KEYWORDS`: mots-clés indiquant fin de conversation
- `clients`: dictionnaire des clients actifs
  - Structure: `{ client_id: { 'socket': socket_obj, 'address': ip:port, 'username': str, 'messages': [ { ... } ] } }`
- `client_counter`: compteur auto-incrément pour attribuer des IDs uniques
- `db`: instance SQLite (classe `Database` du module `database.py`) pour persistance

## Cycle de Vie d'une Connexion TCP
1. Le serveur (`start_tcp_server`) écoute et accepte une connexion.
2. Incrémente `client_counter` → `client_id`.
3. Insère entrée initiale dans `clients` avec username provisoire.
4. Lance un thread `handle_client(client_socket, client_address, client_id)`.
5. Le thread lit le premier message (username réel) → met à jour l'entrée.
6. **Enregistre le client dans SQLite** via `db.update_client_history(client_id, username, address)`.
7. Envoie au client le nom du serveur: `__SERVER_NAME__:<server_username>`.
8. Notifie l'UI Web via Socket.IO (`client_connected`).
9. Boucle de réception: chaque message reçu est:
   - Vérifié contre `EXIT_KEYWORDS`.
   - Stocké dans `clients[client_id]['messages']` (type `received`).
   - **Sauvegardé dans SQLite** via `db.save_message()`.
   - Compteur incrément via `db.increment_message_count()`.
   - Émis à l'UI Web (`message_received`).
10. Si mot-clé exit détecté ou socket fermé: nettoyage + émission `client_disconnected`.

## Historique des Messages par Client
Format d'un message stocké:
```json
{
  "type": "received" | "sent",
  "sender": "<username>",
  "message": "<texte>",
  "timestamp": "ISO-8601",
  "read": false
}
```
- Les messages envoyés depuis l'interface serveur ont `type = 'sent'`.
- Le statut `read` est modifiable via l'événement `mark_messages_read`.

## Routes Flask
| Route | Méthode | Rôle |
|-------|---------|------|
| `/` | GET | Interface du serveur (`server.html`) |
| `/client` | GET | Interface client web (alternative) |
| `/set_server_username` | POST | Modifie `server_username` si valide |

## Chiffrement côté UI (panneau 🔒)
- Générer une clé (bouton «🔄 Nouvelle Clé») puis copier.
- Coller/importer la même clé côté client ou autre navigateur via «📥 Importer».
- Activer le toggle de chiffrement des deux côtés ; les messages `[ENCRYPTED]...` sont déchiffrés automatiquement si la clé est identique.
- La clé reste en localStorage ; si vidé/changement de navigateur, réimporter la clé. Les fichiers ne sont pas chiffrés.

## Événements Socket.IO (Entrants)
| Événement | Fonction | Description |
|-----------|----------|-------------|
| `connect` | `handle_connect` | Envoi snapshot liste clients à la connexion |
| `disconnect` | `handle_disconnect` | Log seul |
| `get_client_messages` | `handle_get_client_messages` | Retourne l'historique complet d'un client |
| `mark_messages_read` | `handle_mark_messages_read` | Marque messages `received` comme lus |
| `connect_to_server` | `handle_client_connect_to_server` | Simule connexion TCP via l'UI (client web) |
| `send_message` | `handle_send_message` | Envoie message ciblé à un client |

## Événements Socket.IO (Sortants)
| Événement | Déclencheur | Payload |
|-----------|-------------|---------|
| `clients_update` | Lors d'une connexion web (snapshot) | Liste des clients actifs |
| `client_connected` | Nouveau client TCP | ID, adresse, username |
| `client_disconnected` | Fin d'une connexion | ID, adresse, username |
| `message_received` | Message reçu d'un client | ID client, texte, username |
| `message_sent` | Message envoyé par le serveur | ID client, texte |
| `client_messages` | Requête d'historique | ID client + tableau messages |
| `messages_marked_read` | Marquage lecture | ID client |
| `error` | Erreur d'envoi ciblé | Texte erreur |
| `connection_error` | Échec simulation connexion web | Détail |

## Détails des Fonctions Clés
### `start_tcp_server()`
- Crée socket serveur (`SO_REUSEADDR` activé)
- Boucle accept() infinie
- Pour chaque nouveau client:
  - Incrémente `client_counter`
  - Initialise entrée dans `clients`
  - Lance thread `handle_client`

### `handle_client(...)`
- Récupère username initial (ou fallback)
- Envoie nom serveur format spécial
- Boucle de réception:
  - Si mot-clé exit: envoie "Au revoir !" + rupture
  - Sinon: stocke message + émet vers UI
- Nettoie structures et notifie UI à la fin

### `handle_send_message(data)`
- Validation (non vide, taille, client existant)
- Envoi au socket du client ciblé
- Ajout à l'historique en `type: sent`
- Émet `message_sent`
- Si mot-clé exit: laisse thread gérer fermeture

### `handle_mark_messages_read(data)`
- Parcourt l'historique du client et marque comme `read = True` tous les `received` non lus
- Broadcast un événement de confirmation

## Nom du Serveur Personnalisable
Route `/set_server_username`:
- Reçoit JSON `{ "username": "NouveauNom" }`
- Validation min length ≥ 2
- Met à jour variable globale + log
- Permet au prochain client connecté de récupérer ce nom via `__SERVER_NAME__:`

## Gestion des IDs Clients
- Numériques incrémentaux (`client_id = client_counter`)
- Clients simulés via UI web reçoivent un ID string `web_<n>` (note: pour la simulation rapide, le thread TCP prend le relais).

## Transfert de Fichiers

### Stockage Organisé par Client
Le code crée plusieurs répertoires organisés par client pour isoler les fichiers:
- `SERVER_RECEIVED_DIR = "uploads/server/received/"`: fichiers reçus des clients (sous-dossiers par `client_id`)
- `SERVER_SENT_DIR = "uploads/server/sent/"`: fichiers envoyés aux clients (sous-dossiers par `client_id`)

Structure: `uploads/server/received/<client_id>/<filename>` et `uploads/server/sent/<client_id>/<filename>`

Ces répertoires sont créés au démarrage (`Path(...).mkdir(parents=True, exist_ok=True)`).

### Réception de Fichiers depuis Clients (dans `handle_client`)
Le thread de réception intègre la détection des lignes commençant par `__FILE__|`:
1. Analyse la ligne: extraction de `filename`, `mimetype`, `size`, `base64_data`
2. Décodage base64 → données binaires
3. Validation du nom de fichier (prévention path traversal)
4. Sauvegarde en `SERVER_RECEIVED_DIR/<client_id>/<filename>`
5. Création d'entrée historique spéciale: `type: 'received'`, `message: '[FICHIER]'` avec métadonnées
6. Émission d'événement Socket.IO `file_received` vers l'UI admin

### Envoi de Fichiers aux Clients (`handle_send_file`)
Fonction décorée `@socketio.on('send_file')` qui:
1. Reçoit un événement du navigateur avec `target_client_id`, `filename`, `mimetype`, `base64_data`
2. Valide: client existe et actif, taille ≤ 2 Mo
3. Encode le fichier en format `__FILE__|<filename>|<mimetype>|<size>|<base64_data>`
4. Envoie sur le socket TCP du client ciblé
5. Sauvegarde une copie en `SERVER_SENT_DIR/<target_client_id>/<filename>`
6. Ajoute entrée historique: `type: 'sent'`, `message: '[FICHIER]'`
7. Émet `file_sent` vers l'UI admin avec lien de téléchargement

**Sérialisation TCP**: format `__FILE__|filename|mimetype|size|base64\n` (newline-delimited pour parsing buffurisé côté client).

### Routes Flask de Téléchargement
```python
@app.route('/files/server/<path:filepath>')
```
Sert les fichiers depuis `uploads/server/{received|sent}/<filepath>` avec le bon `Content-Type` (inline pour images/PDF, attachment pour autres).

Exemple URL générée: `/files/server/received/3/photo.jpg` → télécharge `uploads/server/received/3/photo.jpg`

### Historique Fichiers
Lors du stockage d'un fichier reçu/envoyé, une entrée est créée dans `clients[client_id]['messages']`:
```json
{
  "type": "received" | "sent",
  "sender": "<admin>" | "<client_username>",
  "message": "[FICHIER] <filename>",
  "filename": "<nom_du_fichier>",
  "mimetype": "image/jpeg",
  "size": 5120,
  "timestamp": "ISO-8601"
}
```
Permet de reconstituer la chronologie des transferts de fichiers par client.

## Événements Socket.IO pour Fichiers
| Événement (Entrant)   | Fonction                 | Rôle |
|-----------------------|--------------------------|------|
| `send_file`           | `handle_send_file`       | Reçoit fichier base64 du navigateur admin, envoie au client TCP |

| Événement (Sortant)   | Déclencheur              | Payload |
|-----------------------|--------------------------|---------|
| `file_sent`           | Après envoi TCP + sauvegarde | `{filename, link}` |
| `file_received`       | Thread reçoit `__FILE__` | `{filename, client_id, link}` |

### Flux Typique de Transfert
**Admin envoie fichier à client:**
1. Administrateur clique 📎 dans `server.html`, sélectionne un client et un fichier
2. JavaScript: `FileReader.readAsDataURL(file)` → base64
3. Émet `send_file` Socket.IO avec `target_client_id`
4. `handle_send_file`: encode, envoie sur TCP au client, sauvegarde localement
5. Interface affiche lien de téléchargement dans historique du client

**Admin reçoit fichier d'un client:**
1. Client TCP envoie: `__FILE__|document.pdf|application/pdf|45600|[base64]`
2. Thread `handle_client` détecte `__FILE__`, décode base64, sauvegarde dans `SERVER_RECEIVED_DIR/<client_id>/`
3. Ajoute entrée historique spéciale pour ce client
4. Émet `file_received` Socket.IO
5. Interface affiche le fichier téléchargeable dans l'historique du client

### Limitations et Notes de Sécurité
- **Taille max**: 2 Mo (overhead base64 ~33%)
- **Chiffrement**: fichiers transmis en clair sur TCP (pas de TLS par défaut)
- **Noms**: dénudés de chemins (`/`, `..` stripés) pour prévention path traversal
- **Stockage**: `uploads/server/` peut croître ; nettoyer régulièrement ou archiver ancien historique
- **Multi-client**: chaque client a ses propres dossiers `received/` et `sent/` pour isolation



## Points d'Amélioration Potentiels
- Abstraction: encapsuler la gestion client dans une classe `ClientManager`
- Sécurité: authentification / filtrage IP
- **Persistance**: actuellement SQLite (voir `DATABASE.md`), migration vers PostgreSQL pour haute charge
- Diffusion: gestion broadcast / groupes / rooms
- Surveillance: métriques (nb messages, latence) exposées via endpoint
- Gestion mémoire: purge historique au-delà d'un seuil
- Timeout inactifs: déconnexion automatique après inactivité

## Séquence Type
1. Lancement du script → thread TCP + serveur Flask-SocketIO
2. Connexion d'un client TCP (telnet, script client) → thread `handle_client`
3. UI serveur web se connecte (événement `connect`) → reçoit snapshot clients
4. L'administrateur sélectionne un client → lit historique (`get_client_messages`)
5. Envoie un message ciblé (`send_message`) → historique mis à jour
6. Client répond → arrivée `message_received`
7. Fin conversation mot-clé → thread nettoie + événement `client_disconnected`

## Lancement
Exécution directe:
```bash
python server_web.py
```
Démarrage:
- TCP: `0.0.0.0:12345`
- Web: `http://127.0.0.1:5000`

## Persistance SQLite

### Initialisation de la Base de Données
Au démarrage, un objet `db = Database('messages.db')` est créé, initialisant trois tables (si non présentes):
- `messages`: tous les messages texte échangés
- `files`: métadonnées de tous les fichiers transférés
- `client_history`: historique des connexions clients

### Sauvegarde Automatique
Chaque interaction client est enregistrée:

**Messages reçus:**
```python
db.save_message(
    client_id,
    'received',
    username,
    message_text,
    datetime.now().isoformat()
)
db.increment_message_count(client_id)
```

**Fichiers reçus:**
```python
db.save_file(
    client_id,
    filename,
    mimetype,
    file_size,
    'received',
    username,
    file_path,
    datetime.now().isoformat()
)
db.increment_file_count(client_id)
```

**Messages envoyés:**
```python
db.save_message(
    client_id,
    'sent',
    'Serveur',
    message_text,
    datetime.now().isoformat()
)
db.increment_message_count(client_id)
```

### Récupération de l'Historique
Quand un administrateur consulte l'historique d'un client (événement `get_client_messages`):
```python
if client_id in clients:
    messages = clients[client_id]['messages']  # En mémoire si connecté
else:
    messages = db.get_messages(client_id)  # Depuis SQLite si déconnecté
```

Cela permet de retrouver tout l'historique même après redémarrage du serveur ou déconnexion du client.

### Autres Opérations SQLite
- **Marquer lus**: `db.mark_messages_read(client_id)` met à jour tous les 'received' en `read = 1`
- **Historique client**: `db.get_client_history(client_id)` → infos première connexion, dernière activité, compteurs
- **Export JSON**: `db.export_to_json(client_id, 'client_1_export.json')` → export complet

## Résumé
`server_web.py` orchestre simultanément un serveur TCP multi-clients et une interface temps réel d'administration, avec persistance SQLite automatique de tous les échanges. Il centralise l'état des connexions, expose un historique granularisé par client et fournit les outils nécessaires pour interagir de manière ciblée et supervisée.
