# LocalNetMessage

Application de messagerie locale serveur ↔ client avec interfaces web modernes (UI/UX), temps réel via Socket.IO et un serveur TCP.

## 🚀 Fonctionnalités

- **Communication bidirectionnelle** entre serveur et clients
- **Interface graphique moderne** avec design UI/UX avancé
- **Support multi-clients** avec gestion de plusieurs connexions simultanées
- **Messages en temps réel** via WebSocket et TCP
- **Chiffrement symétrique léger** (XOR + Base64) côté navigateur avec partage de clé
- **Déconnexion intelligente** avec mots-clés personnalisés
- **Design responsive** pour tous les appareils

## 📋 Prérequis

- Python 3.9 ou supérieur
- pip (gestionnaire de paquets Python)
- Navigateur moderne (Chrome, Edge, Firefox)

## 📦 Installation

1. Clonez le dépôt ou téléchargez les fichiers
2. Installez les dépendances depuis `requirements.txt` :

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 🎯 Utilisation

### Mode Interface Web (recommandé)

#### Démarrer le serveur (Flask + Socket.IO):

```powershell
python .\server_web.py
```

- Interface web serveur: `http://localhost:5000`
- Serveur TCP: `0.0.0.0:12345`

#### Démarrer le client web:

```powershell
python .\client_web.py
```

- Interface web client: `http://localhost:5001`
- Dans le formulaire du client, entrez l'IP du serveur (ex: `127.0.0.1`) puis cliquez sur Se connecter

### Chiffrement des messages (UI Web)
1. Ouvrir le panneau 🔒 dans l'interface.
2. Émetteur : «🔄 Nouvelle Clé» puis «📋 Copier».
3. Destinataire : coller la clé dans «Importer une Clé» puis «📥 Importer».
4. Activer le toggle de chiffrement **des deux côtés**. Les messages `[ENCRYPTED]...` se déchiffrent automatiquement si la clé est identique. La clé est stockée en localStorage ; réimportez-la si le navigateur est réinitialisé.

### Mode Terminal (Scripts originaux)

#### Lancer le serveur :
```powershell
python .\server.py
```

#### Lancer le client :
```powershell
python .\client.py
```

## 🌐 Connexion sur le réseau local

Pour connecter des clients depuis d'autres ordinateurs :

1. **Trouvez l'adresse IP de votre serveur** :
   - Windows : `ipconfig`
   - Linux/Mac : `ifconfig` ou `ip addr`

2. **Sur le client**, entrez l'adresse IP locale du serveur (ex: `192.168.1.10`)

3. **Assurez-vous que le pare-feu** autorise les connexions sur les ports :
   - Port 12345 (serveur TCP)
   - Port 5000 (interface web serveur)
   - Port 5001 (interface web client)

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

## 🧪 Tester rapidement (scénario recommandé)

1. Lancez le serveur web:

```powershell
python .\server_web.py
```

2. Ouvrez `http://localhost:5000` et vérifiez la liste des clients (vide au début).

3. Lancez le client web dans un autre terminal:

```powershell
python .\client_web.py
```

4. Ouvrez `http://localhost:5001`, entrez `127.0.0.1` comme IP serveur, puis connectez.

5. Envoyez des messages depuis le client et vérifiez qu'ils apparaissent côté serveur en temps réel.

## 📝 Auteur

Projet réalisé par **Halid13**
