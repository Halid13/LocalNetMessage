# 💬 LocalNetMessage

Une application de messagerie locale simple et intuitive pour communiquer entre un serveur et plusieurs clients sur le réseau local. Avec une interface web moderne et des fonctionnalités avancées comme le chiffrement des messages.

---

## ✨ Fonctionnalités

- 🔗 **Communication bidirectionnelle** - Serveur et clients peuvent s'échanger des messages en temps réel
- 🌐 **Interface web moderne** - Interface graphique élégante et responsive pour serveur et clients
- 👥 **Support multi-clients** - Le serveur gère plusieurs clients connectés simultanément
- ⚡ **Messages en temps réel** - Échange instantané via WebSocket et TCP
- 🔒 **Chiffrement optionnel** - Chiffrement léger des messages côté navigateur avec partage de clé
- 💾 **Historique des messages** - Base de données SQLite pour conserver les conversations
- 🎨 **Design personnalisable** - Avatars et statuts pour serveur et clients
- 👤 **Profil utilisateur** - Nom d'affichage, statut (Disponible/Occupé/En pause), avatar (emoji/URL ou image importée ≤ 256 Ko) avec aperçu, sélection du thème et activation du chiffrement par défaut; profil mémorisé (localStorage) et synchronisé avec le serveur (HTTP) et le client (Socket.IO).
- 🚪 **Déconnexion intelligente** - Mots-clés de déconnexion reconnus automatiquement

---

## 📋 Pré-requis

- **Python 3.9+**
- **pip** (inclus avec Python)
- **Navigateur web moderne** (Chrome, Edge, Firefox)

---

## 🚀 Installation

1. Téléchargez ou clonez le projet
2. Installez les dépendances :

```powershell
pip install -r requirements.txt
```

Les dépendances sont :
- `flask` - Serveur web
- `flask-socketio` - Communication WebSocket en temps réel
- `python-socketio` - Gestion des connexions WebSocket

---

## 🎯 Comment utiliser

### Option 1 : Interface Web (Recommandée)

#### Étape 1 : Démarrer le serveur

Ouvrez un terminal dans le dossier du projet et lancez :

```powershell
python server_web.py
```

L'interface du serveur sera accessible à `http://localhost:5000`

#### Étape 2 : Démarrer le client

Ouvrez un **second terminal** et lancez :

```powershell
python client_web.py
```

L'interface du client sera accessible à `http://localhost:5001`

#### Étape 3 : Connecter le client au serveur

1. Allez dans l'interface client (`http://localhost:5001`)
2. Entrez l'adresse IP du serveur : `127.0.0.1` (ou votre IP réseau)
3. Cliquez sur **Connecter**
4. Échangez vos messages !

---

### Option 2 : Mode Terminal

Si vous préférez une interface simple en ligne de commande :

#### Serveur :
```powershell
python server.py
```

#### Client :
```powershell
python client.py
```

---

## 🔐 Chiffrer les messages

1. Ouvrez le **panneau de chiffrement** 🔒 (en haut de l'interface web)
2. **Côté serveur** : Cliquez sur **Nouvelle Clé** puis **Copier**
3. **Côté client** : Collez la clé dans **Importer une Clé** et cliquez sur **Importer**
4. **Activez le chiffrement** des deux côtés via le toggle
5. Les messages s'afficheront chiffrés et se déchifferont automatiquement

💡 **Note** : Les clés sont stockées localement. Si vous videz le cache, vous devrez réimporter la clé.

---

## 🌍 Connecter des clients sur le réseau local

### Trouver votre adresse IP serveur

**Windows** :
```powershell
ipconfig
```
Cherchez `Adresse IPv4` (généralement `192.168.x.x` ou `10.x.x.x`)

**Linux/Mac** :
```bash
ifconfig
# ou
ip addr
```

### Configurer la connexion

1. Sur le client, entrez l'IP trouvée (exemple : `192.168.1.100`)
2. Vérifiez que le **pare-feu autorise** les connexions sur :
   - Port **12345** (communication TCP)
   - Port **5000** (interface serveur)
   - Port **5001** (interface client)

---

## 🚪 Mots-clés de déconnexion

Tapez l'un de ces mots pour terminer la conversation :

| Français | English |
|----------|---------|
| quit, exit | bye, goodbye |
| au revoir, aurevoir | ciao |
| à plus, a plus | tchao |
| salut | bye bye |
| à bientôt, a bientot | |
| adieu, fin | |

---

## 📁 Structure du projet

```
LocalNetMessage/
├── 📄 server.py           # Serveur TCP (mode terminal)
├── 📄 client.py           # Client TCP (mode terminal)
├── 📄 server_web.py       # Serveur web (Flask + WebSocket)
├── 📄 client_web.py       # Client web (Flask + WebSocket)
├── 📄 database.py         # Gestion de la base de données SQLite
├── 📄 requirements.txt     # Dépendances Python
│
├── 📁 templates/
│   ├── 🌐 server.html     # Interface web du serveur
│   └── 🌐 client.html     # Interface web du client
│
├── 📁 static/
│   ├── 🎨 style.css
│   ├── 🎨 theme-selector.css
│   ├── 🎨 encryption-ui.css
│   └── ⚙️ encryption.js, profile.js, ...
│
├── 📁 uploads/            # Fichiers partagés
│   ├── server/
│   └── client/
│
└── 📁 Doc/
    ├── 📖 guide-projet.md
    ├── 📖 DATABASE.md
    └── 📖 encryption_guide.md
```

---

## 📝 Auteur

Développé par **Halid13**
