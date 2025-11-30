# Architecture Technique

## Vue d’ensemble
Le système combine un serveur TCP historique et une couche temps réel WebSocket (Socket.IO) via Flask pour offrir une supervision et une interface moderne.

```
[ Client Web ] -- Socket.IO --> [ Flask + Socket.IO ] --(interop)--> [ Logique Serveur / TCP ]
       |                                                      |
       +---------------- Affichage / UI ----------------------+ 
```

## Principaux fichiers
| Fichier | Rôle |
|---------|------|
| `server_web.py` | Lance Flask + Socket.IO + serveur TCP, agrège connexions |
| `client_web.py` | Client web local, init Socket.IO, interface utilisateur |
| `server.py` | Version terminal du serveur (mode legacy) |
| `client.py` | Version terminal du client (mode legacy) |
| `templates/server.html` | Structure HTML + JS inline pour gestion clients/messages |
| `templates/client.html` | Structure HTML + JS inline pour interface de chat côté client |
| `static/server-modern.css` | Styles avancés serveur (glass, gradient, dark mode) |
| `static/client-modern.css` | Styles avancés client |

## Flux de connexion (web)
1. Le client ouvre `client_web.py` (serveur Flask client) et charge `client.html`.
2. Il soumet un pseudo + IP serveur.
3. Socket.IO établit un canal avec le serveur (`server_web.py`).
4. Le serveur enregistre le client dans une structure interne (ex: dict ou liste).
5. Le serveur broadcast la mise à jour de la liste des clients à tous.

## Flux d’un message
1. L’utilisateur saisit un texte dans l’interface client.
2. Le JS client émet un événement Socket.IO (`send_message`).
3. Le serveur réceptionne, valide et relaye :
   - Sauvegarde éventuelle dans une conversation en mémoire.
   - Émet un événement de diffusion (`broadcast_message`).
4. Les interfaces (serveur + autres clients ciblés) mettent à jour l’affichage.

## Événements Socket.IO (exemples)
| Événement | Émetteur | Description |
|-----------|----------|-------------|
| `connect` | Client | Ouverture d’un canal Socket.IO |
| `disconnect` | Client / serveur | Fermeture du canal, purge des structures |
| `send_message` | Client | Demande d’envoi d’un message au serveur |
| `broadcast_message` | Serveur | Distribution d’un message aux clients concernés |
| `clients_update` | Serveur | Diffusion liste des clients connectés |
| `system_message` | Serveur | Message interne (info, notification) |

## Données en mémoire
- Dictionnaire des clients connectés : `{client_id: {username, ip}}`
- Conversations : `{client_id: [ {sender, message, type, timestamp, read} ]}`

## Sélection des clients (interface serveur)
- Le clic sur un client déclenche une fonction JS `selectClient(id)` mettant à jour:
  - En-tête de la zone de discussion
  - Chargement de l’historique via `loadClientConversation(id)`

## Gestion du thème
- Attribut `data-theme` sur `<html>` / `<body>` pour basculer light/dark
- Persisté via `localStorage`

## Points d’attention techniques
- Les identifiants clients doivent rester uniques (génération côté serveur)
- La perte de connexion doit déclencher nettoyage + broadcast de mise à jour
- Le rafraîchissement navigateur ne doit pas casser la structure interne (rejoin) 

## Améliorations possibles
Voir `roadmap.md` pour la suite : persistance, sécurité, logs structurés, tests automatiques.
