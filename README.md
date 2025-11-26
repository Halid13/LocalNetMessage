# LocalNetMessage - Système de Communication Réseau Local

Un système de communication serveur-client moderne avec interface graphique web pour les réseaux locaux.

## 🚀 Fonctionnalités

- **Communication bidirectionnelle** entre serveur et clients
- **Interface graphique moderne** avec design UI/UX avancé
- **Support multi-clients** avec gestion de plusieurs connexions simultanées
- **Messages en temps réel** via WebSocket et TCP
- **Déconnexion intelligente** avec mots-clés personnalisés
- **Design responsive** pour tous les appareils

## 📋 Prérequis

- Python 3.7 ou supérieur
- pip (gestionnaire de paquets Python)

## 📦 Installation

1. Clonez le dépôt ou téléchargez les fichiers

2. Installez les dépendances :
```bash
pip install flask flask-socketio
```

## 🎯 Utilisation

### Mode Interface Graphique (Recommandé)

#### Lancer le serveur :
```bash
python server_web.py
```
- Ouvrez votre navigateur sur `http://localhost:8080`
- Le serveur TCP écoute sur le port 5555

#### Lancer le client :
```bash
python client_web.py
```
- Ouvrez votre navigateur sur `http://localhost:8081`
- Entrez l'adresse IP du serveur (par défaut: 127.0.0.1)
- Cliquez sur "Se connecter"

### Mode Terminal (Scripts originaux)

#### Lancer le serveur :
```bash
python server.py
```

#### Lancer le client :
```bash
python client.py
```

## 🌐 Connexion sur le réseau local

Pour connecter des clients depuis d'autres ordinateurs :

1. **Trouvez l'adresse IP de votre serveur** :
   - Windows : `ipconfig`
   - Linux/Mac : `ifconfig` ou `ip addr`

2. **Sur le client**, entrez l'adresse IP locale du serveur (ex: `192.168.1.10`)

3. **Assurez-vous que le pare-feu** autorise les connexions sur les ports :
   - Port 5555 (serveur TCP)
   - Port 8080 (interface web serveur)
   - Port 8081 (interface web client)

## 💬 Mots-clés de déconnexion

Les mots suivants terminent la conversation :
- `quit`, `exit`
- `au revoir`, `aurevoir`
- `à plus`, `a plus`
- `bye`, `goodbye`
- `ciao`, `salut`, `tchao`, `bye bye`
- `à bientôt`, `a bientot`
- `adieu`, `fin`

## 📁 Structure du projet

```
LocalNetMessage/
├── server.py              # Serveur TCP en mode terminal
├── client.py              # Client TCP en mode terminal
├── server_web.py          # Serveur avec interface web
├── client_web.py          # Client avec interface web
├── templates/
│   ├── server.html        # Interface graphique du serveur
│   └── client.html        # Interface graphique du client
└── static/
    └── style.css          # Styles CSS modernes
```

## 🎨 Caractéristiques de l'interface

- **Design moderne** avec dégradés et animations
- **Messages en temps réel** avec horodatage
- **Liste des clients connectés** (côté serveur)
- **Indicateurs de statut** visuels
- **Auto-scroll** des messages
- **Responsive design** adapté à tous les écrans

## 🔧 Configuration

### Modifier les ports

Dans `server_web.py` :
```python
PORT = 5555        # Port TCP
port=8080         # Port web
```

Dans `client_web.py` :
```python
port=8081         # Port web client
```

## 🐛 Résolution de problèmes

### Le client ne peut pas se connecter
- Vérifiez que le serveur est bien démarré
- Vérifiez l'adresse IP et le port
- Vérifiez les paramètres du pare-feu

### L'interface web ne s'affiche pas
- Assurez-vous que Flask et Flask-SocketIO sont installés
- Vérifiez que les ports ne sont pas déjà utilisés
- Consultez la console pour les erreurs

### Les messages ne s'affichent pas
- Vérifiez la connexion réseau
- Actualisez la page web
- Vérifiez la console du navigateur (F12)

## 📝 Auteur

Projet créé pour la communication sur réseau local avec Python.

## 📄 Licence

Ce projet est libre d'utilisation pour des fins éducatives et personnelles.
