# Persistance des Données avec SQLite

## Vue d'Ensemble
À partir de cette version, LocalNetMessage utilise **SQLite** pour persister les messages et les fichiers même après la déconnexion des clients ou l'arrêt du serveur.

## Architecture de la Base de Données

### Schéma SQLite
La base de données comprend trois tables principales:

#### 1. Table `messages`
Stocke tous les messages texte échangés.

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | INTEGER (PK) | Identifiant unique du message |
| `client_id` | INTEGER | ID du client (référence) |
| `type` | TEXT | `'received'` ou `'sent'` |
| `sender` | TEXT | Nom de l'expéditeur |
| `message` | TEXT | Contenu du message |
| `timestamp` | TEXT (ISO-8601) | Horodatage du message |
| `read` | BOOLEAN | Statut lecture (0/1) |
| `created_at` | TEXT | Timestamp création en BD |

**Index**: `idx_client_id`, `idx_timestamp` pour optimisation requêtes.

#### 2. Table `files`
Stocke les métadonnées des fichiers transférés.

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | INTEGER (PK) | Identifiant unique du fichier |
| `client_id` | INTEGER | ID du client |
| `filename` | TEXT | Nom du fichier |
| `mimetype` | TEXT | Type MIME (ex: image/jpeg) |
| `size` | INTEGER | Taille en octets |
| `type` | TEXT | `'received'` ou `'sent'` |
| `sender` | TEXT | Qui a envoyé le fichier |
| `file_path` | TEXT | Chemin de stockage local |
| `timestamp` | TEXT (ISO-8601) | Horodatage du transfert |
| `created_at` | TEXT | Timestamp création en BD |

**Index**: `idx_file_client_id` pour requêtes par client.

#### 3. Table `client_history`
Conserve l'historique des connexions et métadonnées des clients.

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | INTEGER (PK) | Identifiant unique |
| `client_id` | INTEGER (UNIQUE) | ID du client |
| `username` | TEXT | Nom d'utilisateur |
| `address` | TEXT | Adresse IP:port |
| `first_seen` | TEXT | Première connexion |
| `last_seen` | TEXT | Dernière activité |
| `message_count` | INTEGER | Nb messages totaux |
| `file_count` | INTEGER | Nb fichiers totaux |

## Fichiers de Base de Données

### Serveur (`server_web.py`)
- **Fichier**: `messages.db`
- **Localisation**: Racine du projet
- **Contenu**: Messages et fichiers de tous les clients

### Client (`client_web.py`)
- **Fichier**: `client_messages.db`
- **Localisation**: Racine du projet
- **Contenu**: Messages et fichiers du client local (ID client = 1)

## Fonctionnalités de Persistance

### Sauvegarde Automatique
Chaque message/fichier reçu ou envoyé est automatiquement enregistré dans SQLite:

**Côté Serveur:**
- Message reçu d'un client → sauvegardé immédiatement
- Fichier reçu d'un client → métadonnées + chemin sauvegardés
- Message envoyé à un client → marqué comme 'sent'
- Fichier envoyé à un client → marqué comme 'sent'

**Côté Client:**
- Message reçu du serveur → sauvegardé immédiatement
- Fichier reçu du serveur → métadonnées sauvegardées
- Message envoyé au serveur → marqué comme 'sent'
- Fichier envoyé au serveur → métadonnées sauvegardées

### Récupération de l'Historique
Si un client se reconecte ou le serveur redémarre:
1. L'historique en mémoire est vide
2. L'interface serveur peut consulter `get_client_messages` → requête BD
3. Si le client est déconnecté, SQLite fournit l'historique complet

### Marquage "Lus"
Événement Socket.IO `mark_messages_read`:
- Marque tous les messages 'received' d'un client comme `read = 1`
- Utile pour tracker les notifs non lues

## Usage dans le Code

### Module `database.py`
Classe `Database` avec méthodes CRUD:

```python
from database import Database

# Initialisation
db = Database('messages.db')

# Sauvegarder un message
db.save_message(
    client_id=1,
    message_type='received',
    sender='Alice',
    message='Bonjour!',
    timestamp='2025-12-06T10:30:00'
)

# Récupérer l'historique
messages = db.get_messages(client_id=1)

# Sauvegarder fichier
db.save_file(
    client_id=1,
    filename='photo.jpg',
    mimetype='image/jpeg',
    size=5120,
    file_type='received',
    sender='Bob',
    file_path='/uploads/client/received/photo.jpg',
    timestamp='2025-12-06T10:31:00'
)

# Récupérer historique client
history = db.get_client_history(client_id=1)

# Exporter en JSON
db.export_to_json(client_id=1, output_path='client_1_export.json')
```

## Avantages

✓ **Persistance**: Historique conservé après redémarrage  
✓ **Récupération**: Récupère l'historique même après déconnexion  
✓ **Archivage**: Possibilité de supprimer vieux messages  
✓ **Audit**: Trace complète des échanges  
✓ **Export**: Extraction JSON de l'historique par client  
✓ **Concurrence**: Lock threading pour sécurité multi-thread  
✓ **Optimization**: Index sur client_id et timestamp  

## Limitations

- Base de données **SQLite**: appropriée petite/moyenne charge, non recommandé très haut débit
- **Taille DB**: croît avec nb messages (surveiller périodiquement)
- **Pas de chiffrement**: données en BD clair (amélioration: SQLCipher)
- **Format texte**: `__FILE__` protocol simplifié pour prototypage

## Évolutions Futures

1. **PostgreSQL/MySQL**: Migration vers BD production pour haute scalabilité
2. **Chiffrement**: SQLCipher pour données sensibles
3. **Archivage**: Rotation logs, suppression auto messages > X jours
4. **Recherche**: Index texte intégral (Full-text search)
5. **Analytics**: Dashboard avec stats nb messages/fichiers/bande passante
6. **Backup**: Export/import auto pour sauvegarde
