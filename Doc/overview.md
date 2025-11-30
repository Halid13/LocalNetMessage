# LocalNetMessage - Overview

LocalNetMessage est une application de messagerie temps réel pensée pour un usage sur réseau local, combinant :
- Un serveur TCP pour la couche transport des messages
- Une interface web serveur (Flask + Socket.IO) pour la supervision et la modération
- Une interface web client moderne pour l’envoi et la réception de messages

## Objectifs
- Simplifier les échanges sur un LAN (bureau, salle de formation, classe)
- Offrir une UI/UX moderne et responsive
- Permettre au serveur de visualiser tous les clients et leur activité
- Fournir un socle extensible (authentification, persistance, sécurité)

## Composants principaux
| Composant | Rôle | Fichier |
|----------|------|---------|
| Serveur TCP | Accepte les connexions des clients et relaie les messages | `server.py` / logique partagée avec `server_web.py` |
| Interface serveur web | Supervision, liste des clients, historique, thème | `server_web.py` + `templates/server.html` |
| Interface client web | Connexion, envoi/réception, formatage de texte | `client_web.py` + `templates/client.html` |
| Styles modernes | Design glassmorphism, dark mode, animations | `static/client-modern.css`, `static/server-modern.css` |
| Socket.IO | Canal temps réel (événements) | Intégré dans pages HTML |

## Features clés
- Gestion multi-clients (identifiants / pseudo)
- Avatars colorés dynamiques
- Bulles de discussion stylées (horodatage, statut lecture)
- Thème clair / sombre (persisté) 
- Formatage léger Markdown-like (**gras**, *italique*, ~~barré~~)
- Emojis rapides
- Mots-clés de déconnexion filtrés côté serveur

## Limites actuelles
- Pas de stockage persistant (mémoire uniquement)
- Pas d’authentification ni chiffrement TLS
- Pas de pagination d’historique

## Pistes d’extension
Voir `roadmap.md` pour les idées d’évolution.
