from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import socket
import threading
import os
import base64
from pathlib import Path
from database import Database
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'localnetmessage-secret-key-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

HOST = '0.0.0.0'
PORT = 12345

server_username = 'Serveur'
server_status = 'Disponible'

EXIT_KEYWORDS = [
    'quit', 'exit', 'au revoir', 'aurevoir', 'à plus', 'a plus',
    'bye', 'goodbye', 'ciao', 'salut', 'tchao', 'bye bye',
    'à bientôt', 'a bientot', 'adieu', 'fin'
]

clients = {}
client_counter = 0

BASE_DIR = Path(__file__).resolve().parent
SERVER_FILES_DIR = BASE_DIR / 'uploads' / 'server'
SERVER_RECEIVED_DIR = SERVER_FILES_DIR / 'received'
SERVER_SENT_DIR = SERVER_FILES_DIR / 'sent'
for d in [SERVER_RECEIVED_DIR, SERVER_SENT_DIR]:
    os.makedirs(d, exist_ok=True)

# Initialiser la base de données SQLite
db = Database(str(BASE_DIR / 'messages.db'))

def handle_client(client_socket, client_address, client_id):
    """Gère la communication avec un client TCP connecté"""
    global clients
    
    address_str = f"{client_address[0]}:{client_address[1]}"
    username = "Anonyme"
    
    try:
        username = client_socket.recv(1024).decode('utf-8').strip()
        if not username:
            username = f"Client_{client_id}"
    except:
        username = f"Client_{client_id}"
    
    clients[client_id]['username'] = username
    clients[client_id]['messages'] = []
    
    print(f"[NOUVELLE CONNEXION] {username} ({address_str}) - ID: {client_id}")
    
    # Mettre à jour l'historique du client dans SQLite
    db.update_client_history(client_id, username, address_str)

    try:
        client_socket.send(f"__SERVER_NAME__:{server_username}\n".encode('utf-8'))
        client_socket.send(f"__SERVER_STATUS__:{server_status}\n".encode('utf-8'))
    except Exception as e:
        print(f"[AVERTISSEMENT] Impossible d'envoyer les infos du serveur au client {client_id}: {e}")
    
    socketio.emit('client_connected', {
        'client_id': client_id,
        'address': address_str,
        'username': username
    })
    
    try:
        connected = True
        buffer = ""
        while connected:
            chunk = client_socket.recv(1024)
            if not chunk:
                break
            try:
                text = chunk.decode('utf-8')
            except UnicodeDecodeError:
                continue
            buffer += text
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                if not line:
                    continue
                if line.startswith("__CLIENT_NAME__:"):
                    new_name = line.split(":",1)[1].strip() or f"Client_{client_id}"
                    username = new_name
                    if client_id in clients:
                        clients[client_id]['username'] = new_name
                    db.update_client_history(client_id, new_name, address_str)
                    socketio.emit('client_renamed', {
                        'client_id': client_id,
                        'address': address_str,
                        'username': new_name
                    })
                    continue

                if line.startswith("__CLIENT_STATUS__:"):
                    new_status = line.split(":",1)[1].strip()
                    if client_id in clients:
                        clients[client_id]['status'] = new_status
                    socketio.emit('client_status_changed', {
                        'client_id': client_id,
                        'address': address_str,
                        'username': username,
                        'status': new_status
                    })
                    continue

                if line.startswith("__FILE__|"):
                    try:
                        _, filename, mimetype, size_str, b64 = line.split('|', 4)
                        data = base64.b64decode(b64.encode('utf-8'))
                        filename = os.path.basename(filename)
                        client_dir = SERVER_RECEIVED_DIR / str(client_id)
                        os.makedirs(client_dir, exist_ok=True)
                        save_path = client_dir / filename
                        with open(save_path, 'wb') as f:
                            f.write(data)
                        
                        timestamp = datetime.now().isoformat()
                        
                        if client_id in clients:
                            clients[client_id]['messages'].append({
                                'type': 'received',
                                'sender': username,
                                'message': f"[FICHIER] {filename} ({len(data)} o)",
                                'timestamp': timestamp,
                                'read': False
                            })
                        
                        # Sauvegarder dans SQLite
                        db.save_file(
                            client_id,
                            filename,
                            mimetype,
                            len(data),
                            'received',
                            username,
                            str(save_path),
                            timestamp
                        )
                        db.increment_file_count(client_id)
                        
                        socketio.emit('file_received', {
                            'client_id': client_id,
                            'address': address_str,
                            'username': username,
                            'filename': filename,
                            'mimetype': mimetype,
                            'size': len(data),
                            'url': f"/files/server/received/{client_id}/{filename}"
                        })
                    except Exception as e:
                        print(f"[ERREUR] Réception fichier client {client_id}: {e}")
                    continue

                if line.lower() in EXIT_KEYWORDS:
                    print(f"[DÉCONNEXION] {username} se déconnecte (mot-clé: '{line}').")
                    try:
                        client_socket.send("Au revoir !\n".encode('utf-8'))
                    except:
                        pass
                    connected = False
                    continue

                if client_id in clients:
                    timestamp = datetime.now().isoformat()
                    clients[client_id]['messages'].append({
                        'type': 'received',
                        'sender': username,
                        'message': line,
                        'timestamp': timestamp,
                        'read': False
                    })
                    # Sauvegarder dans SQLite
                    db.save_message(client_id, 'received', username, line, timestamp)
                    db.increment_message_count(client_id)
                
                socketio.emit('message_received', {
                    'client_id': client_id,
                    'address': address_str,
                    'username': username,
                    'message': line
                })
    
    except Exception as e:
        print(f"[ERREUR] {username}: {e}")
    
    finally:
        if client_id in clients:
            del clients[client_id]
        
        client_socket.close()
        print(f"[FERMETURE] {username} déconnecté.")
        
        socketio.emit('client_disconnected', {
            'client_id': client_id,
            'address': address_str,
            'username': username
        })

def start_tcp_server():
    """Démarre le serveur TCP dans un thread séparé"""
    global client_counter
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    
    print(f"[DÉMARRAGE] Serveur TCP en écoute sur {HOST}:{PORT}")
    
    try:
        while True:
            client_socket, client_address = server.accept()
            
            client_counter += 1
            client_id = client_counter
            
            clients[client_id] = {
                'socket': client_socket,
                'address': f"{client_address[0]}:{client_address[1]}",
                'username': f"Client_{client_id}",
                'messages': []
            }
            
            thread = threading.Thread(
                target=handle_client, 
                args=(client_socket, client_address, client_id)
            )
            thread.daemon = True
            thread.start()
            
            print(f"[CONNEXIONS ACTIVES] {len(clients)}")
    
    except Exception as e:
        print(f"[ERREUR SERVEUR] {e}")
    
    finally:
        server.close()

@app.route('/')
def index():
    """Page d'accueil - Interface du serveur"""
    return render_template('server.html')

@app.route('/client')
def client():
    """Page client - Interface du client"""
    return render_template('client.html')

@app.route('/set_server_username', methods=['POST'])
def set_server_username():
    """Définir le nom d'utilisateur du serveur"""
    global server_username
    
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if username and len(username) >= 2:
        server_username = username
        print(f'[SERVEUR] Nom d\'utilisateur défini: {server_username}')
        # Notifier tous les clients TCP
        for cid, cdata in list(clients.items()):
            sock = cdata.get('socket')
            try:
                if sock:
                    sock.send(f"__SERVER_NAME__:{server_username}\n".encode('utf-8'))
            except Exception as e:
                print(f"[AVERTISSEMENT] Impossible d'envoyer le nouveau nom au client {cid}: {e}")
        # Notifier l'UI web
        socketio.emit('server_username_updated', {'username': server_username})
        return jsonify({'success': True, 'username': server_username})
    else:
        return jsonify({'success': False, 'error': 'Nom d\'utilisateur invalide'}), 400

@app.route('/set_server_status', methods=['POST'])
def set_server_status():
    """Définir le statut du serveur"""
    global server_status
    
    data = request.get_json()
    status = data.get('status', '').strip()
    
    if status:
        server_status = status
        print(f'[SERVEUR] Statut défini: {server_status}')
        # Notifier tous les clients TCP
        for cid, cdata in list(clients.items()):
            sock = cdata.get('socket')
            try:
                if sock:
                    sock.send(f"__SERVER_STATUS__:{server_status}\n".encode('utf-8'))
            except Exception as e:
                print(f"[AVERTISSEMENT] Impossible d'envoyer le nouveau statut au client {cid}: {e}")
        # Notifier l'UI web
        socketio.emit('server_status_updated', {'status': server_status})
        return jsonify({'success': True, 'status': server_status})
    else:
        return jsonify({'success': False, 'error': 'Statut invalide'}), 400

@socketio.on('connect')
def handle_connect():
    """Client web connecté"""
    print('[WEB] Client web connecté')
    emit('clients_update', {
        'clients': [
            {'id': cid, 'address': cdata['address'], 'username': cdata.get('username', 'Anonyme')}
            for cid, cdata in clients.items()
        ]
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Client web déconnecté"""
    print('[WEB] Client web déconnecté')

@socketio.on('get_client_messages')
def handle_get_client_messages(data):
    """Récupérer l'historique des messages d'un client"""
    client_id = data.get('client_id')
    
    # Chercher d'abord en mémoire (client actif)
    if client_id in clients:
        messages = clients[client_id]['messages']
    else:
        # Chercher dans SQLite (client déconnecté)
        messages = db.get_messages(client_id)
    
    emit('client_messages', {
        'client_id': client_id,
        'messages': messages
    })

@socketio.on('mark_messages_read')
def handle_mark_messages_read(data):
    """Marquer les messages d'un client comme lus"""
    client_id = data.get('client_id')
    
    if client_id in clients:
        for msg in clients[client_id]['messages']:
            if msg['type'] == 'received' and not msg.get('read', False):
                msg['read'] = True
        
        emit('messages_marked_read', {'client_id': client_id}, broadcast=True)

@socketio.on('connect_to_server')
def handle_client_connect_to_server(data):
    """Gérer la connexion d'un client web via TCP"""
    username = data.get('username', 'Anonyme')
    server_ip = data.get('server_ip', '127.0.0.1')
    server_port = int(data.get('server_port', PORT))
    
    try:
        print(f"[CLIENT WEB] {username} tente de se connecter via l'interface web")
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, server_port))
        
        client_socket.send(username.encode('utf-8'))
        
        global client_counter
        client_counter += 1
        web_client_id = f"web_{client_counter}"
        
        emit('connected', {
            'server_ip': server_ip,
            'server_port': server_port,
            'username': username,
            'client_id': web_client_id
        })
        
        print(f"[CLIENT WEB] {username} connecté avec succès")
        
    except Exception as e:
        print(f"[ERREUR CLIENT WEB] {e}")
        emit('connection_error', {
            'message': f'Impossible de se connecter: {str(e)}'
        })

@socketio.on('send_message')
def handle_send_message(data):
    """Envoyer un message à un client spécifique"""
    client_id = data.get('client_id')
    message = data.get('message', '').strip()
    
    if not message:
        emit('error', {'message': 'Le message ne peut pas être vide'})
        return
    
    if len(message) > 5000:
        emit('error', {'message': 'Message trop long (maximum 5000 caractères)'})
        return
    
    if client_id not in clients:
        emit('error', {'message': 'Client non trouvé'})
        return
    
    client_socket = clients[client_id]['socket']
    
    try:
        client_socket.send((message + "\n").encode('utf-8'))
        
        timestamp = datetime.now().isoformat()
        clients[client_id]['messages'].append({
            'type': 'sent',
            'sender': 'Serveur',
            'message': message,
            'timestamp': timestamp,
            'read': False
        })
        
        # Sauvegarder dans SQLite
        db.save_message(client_id, 'sent', 'Serveur', message, timestamp)
        db.increment_message_count(client_id)
        
        emit('message_sent', {
            'client_id': client_id,
            'message': message
        })
        
        if message.lower().strip() in EXIT_KEYWORDS:
            print(f"[DÉCONNEXION] Terminaison de la conversation avec client {client_id}")
    
    except Exception as e:
        print(f"[ERREUR] Impossible d'envoyer au client {client_id}: {e}")
        emit('error', {'message': 'Erreur lors de l\'envoi du message'})


@app.route('/files/server/<path:subpath>')
def serve_server_files(subpath):
    root = str(SERVER_FILES_DIR)
    return send_from_directory(root, subpath, as_attachment=True)


@socketio.on('send_file')
def handle_send_file(data):
    """Envoi d'un fichier à un client spécifique depuis l'UI serveur."""
    client_id = data.get('client_id')
    filename = os.path.basename(data.get('filename', ''))
    mimetype = data.get('mimetype', 'application/octet-stream')
    b64 = data.get('data_base64', '')

    if client_id not in clients:
        emit('error', {'message': 'Client non trouvé'})
        return
    if not filename or not b64:
        emit('error', {'message': 'Fichier invalide.'})
        return

    try:
        print(f"[SERVEUR] Envoi de fichier vers client {client_id}: {filename} ({mimetype})")
        raw = base64.b64decode(b64.encode('utf-8'))
        if len(raw) > 2 * 1024 * 1024:
            emit('error', {'message': 'Fichier trop volumineux (max 2 Mo).'})
            return

        client_dir = SERVER_SENT_DIR / str(client_id)
        os.makedirs(client_dir, exist_ok=True)
        save_path = client_dir / filename
        with open(save_path, 'wb') as f:
            f.write(raw)

        line = f"__FILE__|{filename}|{mimetype}|{len(raw)}|{b64}\n"
        clients[client_id]['socket'].send(line.encode('utf-8'))

        timestamp = datetime.now().isoformat()
        clients[client_id]['messages'].append({
            'type': 'sent',
            'sender': 'Serveur',
            'message': f"[FICHIER] {filename} ({len(raw)} o)",
            'timestamp': timestamp,
            'read': False
        })
        
        # Sauvegarder dans SQLite
        db.save_file(
            client_id,
            filename,
            mimetype,
            len(raw),
            'sent',
            'Serveur',
            str(save_path),
            timestamp
        )
        db.increment_file_count(client_id)

        emit('file_sent', {
            'client_id': client_id,
            'filename': filename,
            'mimetype': mimetype,
            'size': len(raw)
        })
    except Exception as e:
        print(f"[ERREUR] Envoi fichier au client {client_id}: {e}")
        emit('error', {'message': 'Erreur lors de l\'envoi du fichier'})

if __name__ == '__main__':
    tcp_thread = threading.Thread(target=start_tcp_server)
    tcp_thread.daemon = True
    tcp_thread.start()
    
    print('[WEB] Serveur web démarré sur http://127.0.0.1:5000')
    print('[INFO] Ouvrez http://localhost:5000 dans votre navigateur')
    socketio.run(app, host='127.0.0.1', port=5000, debug=False, allow_unsafe_werkzeug=True)
