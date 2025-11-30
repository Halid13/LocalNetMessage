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

## Variables & Structures
- `HOST = '0.0.0.0'`: écoute sur toutes les interfaces
- `PORT = 12345`: port TCP standardisé du projet
- `server_username`: nom d'affichage du serveur (modifiable via route POST)
- `EXIT_KEYWORDS`: mots-clés indiquant fin de conversation
- `clients`: dictionnaire des clients actifs
  - Structure: `{ client_id: { 'socket': socket_obj, 'address': ip:port, 'username': str, 'messages': [ { ... } ] } }`
- `client_counter`: compteur auto-incrément pour attribuer des IDs uniques

## Cycle de Vie d'une Connexion TCP
1. Le serveur (`start_tcp_server`) écoute et accepte une connexion.
2. Incrémente `client_counter` → `client_id`.
3. Insère entrée initiale dans `clients` avec username provisoire.
4. Lance un thread `handle_client(client_socket, client_address, client_id)`.
5. Le thread lit le premier message (username réel) → met à jour l'entrée.
6. Envoie au client le nom du serveur: `__SERVER_NAME__:<server_username>`.
7. Notifie l'UI Web via Socket.IO (`client_connected`).
8. Boucle de réception: chaque message reçu est:
   - Vérifié contre `EXIT_KEYWORDS`.
   - Stocké dans `clients[client_id]['messages']` (type `received`).
   - Émis à l'UI Web (`message_received`).
9. Si mot-clé exit détecté ou socket fermé: nettoyage + émission `client_disconnected`.

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

## Points d'Amélioration Potentiels
- Abstraction: encapsuler la gestion client dans une classe `ClientManager`
- Sécurité: authentification / filtrage IP
- Persistance: stocker l'historique (SQLite, Postgres)
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

## Résumé
`server_web.py` orchestre simultanément un serveur TCP multi-clients et une interface temps réel d'administration. Il centralise l'état des connexions, expose un historique granularisé par client et fournit les outils nécessaires pour interagir de manière ciblée et supervisée.
