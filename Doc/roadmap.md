# Roadmap & Améliorations Futures

## 1. Fiabilité & Persistance
- Sauvegarde des conversations (SQLite / PostgreSQL / fichiers JSON)
- Restauration de session après redémarrage
- Archivage / export (CSV, JSON)

## 2. Sécurité
- Passage à HTTPS (certificat local / reverse proxy Nginx)
- Authentification (JWT / session / mot de passe serveur)
- Filtrage de contenu / prévention injection HTML
- Limitation du spam (ratelimit par IP / pseudo)

## 3. Fonctionnalités UI/UX supplémentaires
- Recherche dans les messages
- Réactions emoji sur un message
- Edition / suppression de message (marquage modifié)
- Indicateur "utilisateur en train d’écrire"
- Upload de fichiers (images, PDF)

## 4. Outils serveur
- Tableau de bord statistiques : nombre messages, clients actifs
- Logs structurés (JSON) + niveau (INFO/WARN/ERROR)
- Commandes d’administration (kick, mute)

## 5. Qualité & Tests
- Tests unitaires (Pytest) sur la logique messages
- Tests d’intégration Socket.IO
- Script de charge (locust / artillery) pour 100+ clients simulés

## 6. Observabilité
- Intégration monitoring (Prometheus + Grafana)
- Métriques: latence message, connexions actives, taux erreurs

## 7. Internationalisation
- Fichiers de langue (FR / EN)
- Sélecteur de langue dans l’interface

## 8. Performance
- Passage éventuel à `eventlet` ou `gevent` pour meilleure scalabilité
- Compression des payloads Socket.IO
- Minification / bundling CSS & JS

## 9. API Externe (optionnel)
- Endpoints REST pour récupérer clients / messages
- Webhook sur nouvel utilisateur / message système

## 10. Mode mobile dédié
- Vue compacte / PWA (manifest + offline assets)
- Notifications push locales

---
Priorisation suggérée : Persistance → Authentification → File uploads → Observabilité.
