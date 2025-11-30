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

## Variables Globales Principales
- `client_socket`: socket TCP actif vers le serveur
- `connected`: booléen indiquant l'état de connexion TCP
- `receive_thread`: thread qui écoute en permanence les messages du serveur
- `username`: pseudo de l'utilisateur courant envoyé au serveur
- `server_display_name`: nom d'affichage du serveur (peut être mis à jour dynamiquement via message spécial)
- `message_counter`: compteur pour générer des IDs uniques localement
- `EXIT_KEYWORDS`: liste de chaînes déclenchant la fin de conversation

## Flux de Connexion
1. Le navigateur émet l'événement Socket.IO `connect_to_server` avec `username`, `server_ip`, `server_port`.
2. Le serveur Flask crée un socket TCP et se connecte.
3. Le pseudo (`username`) est envoyé immédiatement comme premier payload TCP.
4. Le thread `receive_messages` démarre pour écouter en continu.
5. Un événement Socket.IO `connected` est renvoyé au navigateur pour mise à jour UI.

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
5. Si mot-clé de sortie envoyé: planifie la fermeture (`threading.Timer`) pour permettre une éventuelle réponse serveur

## Gestion Déconnexion
- `disconnect_from_server`: ferme le socket, remet `client_socket` à `None`, marque `connected = False`
- Événements déclencheurs: mot-clé de sortie (client ou serveur), fermeture serveur, action utilisateur `disconnect_from_server`.

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

## Résumé
`client_web.py` encapsule un client TCP classique derrière une couche Web temps réel. Il orchestre la connexion, la translation des événements Socket.IO vers des opérations socket brutes et la remontée d'un flux de messages vers l'UI moderne.
