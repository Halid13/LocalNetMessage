from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit
import socket
import threading
import time
import os
import base64
from pathlib import Path
from database import Database
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'localnetmessage-client-secret-key-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

BASE_DIR = Path(__file__).resolve().parent
CLIENT_FILES_DIR = BASE_DIR / 'uploads' / 'client'
CLIENT_RECEIVED_DIR = CLIENT_FILES_DIR / 'received'
CLIENT_SENT_DIR = CLIENT_FILES_DIR / 'sent'
for d in [CLIENT_RECEIVED_DIR, CLIENT_SENT_DIR]:
    os.makedirs(d, exist_ok=True)

# Initialiser la base de données SQLite (client)
# Utilise un fichier DB séparé pour le client
db = Database(str(BASE_DIR / 'client_messages.db'))

EXIT_KEYWORDS = [
    'quit', 'exit', 'au revoir', 'aurevoir', 'à plus', 'a plus',
    'bye', 'goodbye', 'ciao', 'salut', 'tchao', 'bye bye',
    'à bientôt', 'a bientot', 'adieu', 'fin'
]

client_socket = None
connected = False
receive_thread = None
username = None
server_display_name = 'Serveur'
server_status = 'Disponible'
server_avatar = '🙂'
client_status = 'Disponible'
client_avatar = '🙂'
message_counter = 0

def receive_messages():
    """Thread pour recevoir les messages du serveur"""
    global client_socket, connected, server_display_name, server_status, server_avatar
    buffer = ""
    try:
        with app.app_context():
            while connected:
                if client_socket:
                    try:
                        chunk = client_socket.recv(1024)
                        if not chunk:
                            print("[DÉCONNEXION] Le serveur a fermé la connexion.")
                            socketio.emit('disconnected', {'reason': 'Serveur déconnecté'})
                            connected = False
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
                            if line.startswith("__SERVER_NAME__:"):
                                server_display_name = line.split(":", 1)[1].strip() or 'Serveur'
                                print(f"[INFO] Nom du serveur défini: {server_display_name}")
                                socketio.emit('server_username_updated', {'username': server_display_name})
                                continue
                            if line.startswith("__SERVER_STATUS__:"):
                                server_status = line.split(":", 1)[1].strip() or 'Disponible'
                                print(f"[INFO] Statut du serveur défini: {server_status}")
                                socketio.emit('server_status_updated', {'status': server_status})
                                continue
                            if line.startswith("__SERVER_AVATAR__:"):
                                server_avatar = line.split(":", 1)[1].strip() or '🙂'
                                print(f"[INFO] Avatar du serveur défini")
                                socketio.emit('server_avatar_updated', {'avatar': server_avatar})
                                continue
                            if line.startswith("__FILE__|"):
                                try:
                                    _, filename, mimetype, size_str, b64 = line.split('|', 4)
                                    data = base64.b64decode(b64.encode('utf-8'))
                                    filename = os.path.basename(filename)
                                    save_path = CLIENT_RECEIVED_DIR / filename
                                    with open(save_path, 'wb') as f:
                                        f.write(data)
                                    
                                    timestamp = datetime.now().isoformat()
                                    
                                    # Sauvegarder dans SQLite
                                    db.save_file(
                                        1,  # Client ID (constant: 1 pour le client local)
                                        filename,
                                        mimetype,
                                        len(data),
                                        'received',
                                        server_display_name,
                                        str(save_path),
                                        timestamp
                                    )
                                    
                                    socketio.emit('file_received', {
                                        'filename': filename,
                                        'mimetype': mimetype,
                                        'size': len(data),
                                        'url': f"/files/client/received/{filename}",
                                        'server_username': server_display_name
                                    })
                                except Exception as e:
                                    print(f"[ERREUR] Réception de fichier: {e}")
                                continue
                            socketio.emit('message_received', {
                                'message': line,
                                'server_username': server_display_name
                            })
                            
                            # Sauvegarder dans SQLite
                            timestamp = datetime.now().isoformat()
                            db.save_message(1, 'received', server_display_name, line, timestamp)
                            
                            if line.lower() in EXIT_KEYWORDS:
                                print("[DÉCONNEXION] Le serveur a terminé la conversation.")
                                socketio.emit('disconnected', {'reason': 'Serveur a terminé la conversation'})
                                connected = False
                                break
                    
                    except Exception as e:
                        if connected:
                            print(f"[ERREUR] Erreur de réception: {e}")
                            socketio.emit('error', {'message': f'Erreur de réception: {str(e)}'})
                        break
    
    except Exception as e:
        print(f"[ERREUR] Thread de réception: {e}")
    
    finally:
        if client_socket:
            try:
                client_socket.close()
            except:
                pass

@app.route('/')
def index():
    """Page d'accueil - Interface du client"""
    return render_template('client.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Servir les fichiers du dossier assets"""
    return send_from_directory('assets', filename)

@socketio.on('connect')
def handle_connect():
    """Client web connecté"""
    print('[WEB] Client web connecté')

@socketio.on('disconnect')
def handle_disconnect():
    """Client web déconnecté"""
    print('[WEB] Client web déconnecté')
    disconnect_from_server()

@socketio.on('connect_to_server')
def handle_connect_to_server(data):
    """Connexion au serveur TCP"""
    global client_socket, connected, receive_thread, username
    
    username = data.get('username', 'Anonyme')
    server_ip = data.get('server_ip', '127.0.0.1')
    server_port = int(data.get('server_port', 5555))
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, server_port))
        client_socket.send((username + "\n").encode('utf-8'))
        
        connected = True
        print(f"[CONNECTÉ] {username} connecté au serveur {server_ip}:{server_port}")
        
        global server_display_name
        server_display_name = 'Serveur'

        receive_thread = threading.Thread(target=receive_messages)
        receive_thread.daemon = True
        receive_thread.start()
        
        emit('connected', {
            'server_ip': server_ip,
            'server_port': server_port,
            'username': username
        })
    
    except ConnectionRefusedError:
        print(f"[ERREUR] Impossible de se connecter au serveur {server_ip}:{server_port}")
        emit('connection_error', {
            'message': f'Impossible de se connecter au serveur {server_ip}:{server_port}. Vérifiez que le serveur est bien démarré.'
        })
    
    except Exception as e:
        print(f"[ERREUR] Erreur de connexion: {e}")
        emit('connection_error', {
            'message': f'Erreur de connexion: {str(e)}'
        })

@socketio.on('rename_user')
def handle_rename_user(data):
    """Changer le nom d'utilisateur côté client et notifier le serveur TCP"""
    global client_socket, connected, username
    new_name = data.get('username', '').strip()
    if not new_name:
        emit('error', {'message': 'Nom utilisateur vide.'})
        return
    username = new_name
    if connected and client_socket:
        try:
            client_socket.send(f"__CLIENT_NAME__:{new_name}\n".encode('utf-8'))
        except Exception as e:
            emit('error', {'message': f'Impossible de changer le nom: {e}'})
    emit('user_renamed', {'username': new_name})

@socketio.on('change_status')
def handle_change_status(data):
    """Changer le statut côté client et notifier le serveur TCP"""
    global client_socket, connected, client_status
    new_status = data.get('status', '').strip()
    print(f"[DEBUG] change_status reçu: {new_status}, connected: {connected}")
    if not new_status:
        emit('error', {'message': 'Statut vide.'})
        return
    client_status = new_status
    if connected and client_socket:
        try:
            message = f"__CLIENT_STATUS__:{new_status}\n"
            print(f"[DEBUG] Envoi au serveur TCP: {message.strip()}")
            client_socket.send(message.encode('utf-8'))
            print(f"[INFO] Statut client changé et envoyé au serveur: {new_status}")
        except Exception as e:
            print(f"[ERREUR] Impossible de changer le statut: {e}")
            emit('error', {'message': f'Impossible de changer le statut: {e}'})
    else:
        print(f"[AVERTISSEMENT] Non connecté, impossible d'envoyer le statut")
    emit('status_changed', {'status': new_status})

@socketio.on('change_avatar')
def handle_change_avatar(data):
    """Changer l'avatar côté client et notifier le serveur TCP"""
    global client_socket, connected, client_avatar
    new_avatar = data.get('avatar', '').strip()
    print(f"[DEBUG] change_avatar reçu, connected: {connected}")
    if not new_avatar:
        emit('error', {'message': 'Avatar vide.'})
        return
    client_avatar = new_avatar
    if connected and client_socket:
        try:
            message = f"__CLIENT_AVATAR__:{new_avatar}\n"
            print(f"[DEBUG] Envoi avatar au serveur TCP")
            client_socket.send(message.encode('utf-8'))
            print(f"[INFO] Avatar client changé et envoyé au serveur")
        except Exception as e:
            print(f"[ERREUR] Impossible de changer l'avatar: {e}")
            emit('error', {'message': f'Impossible de changer l\'avatar: {e}'})
    else:
        print(f"[AVERTISSEMENT] Non connecté, impossible d'envoyer l'avatar")
    emit('avatar_changed', {'avatar': new_avatar})

@socketio.on('send_message')
def handle_send_message(data):
    """Envoyer un message au serveur"""
    global client_socket, connected, message_counter
    
    message = data.get('message', '').strip()
    
    if not message:
        emit('error', {'message': 'Le message ne peut pas être vide.'})
        return
    
    if len(message) > 5000:
        emit('error', {'message': 'Le message ne peut pas dépasser 5000 caractères.'})
        return
    
    if not connected or not client_socket:
        emit('error', {'message': 'Non connecté au serveur.'})
        return
    
    try:
        message_counter += 1
        message_id = f"client_{message_counter}_{int(time.time() * 1000)}"
        
        client_socket.send((message + "\n").encode('utf-8'))
        
        emit('message_sent', {
            'message': message,
            'message_id': message_id
        })
        
        # Sauvegarder dans SQLite
        timestamp = datetime.now().isoformat()
        db.save_message(1, 'sent', username, message, timestamp)
        
        if message.lower().strip() in EXIT_KEYWORDS:
            print("[DÉCONNEXION] Déconnexion du serveur...")
            connected = False
            threading.Timer(1.0, disconnect_from_server).start()
    
    except Exception as e:
        print(f"[ERREUR] Impossible d'envoyer le message: {e}")
        emit('error', {'message': f'Erreur lors de l\'envoi: {str(e)}'})

@socketio.on('disconnect_from_server')
def handle_disconnect_request():
    """Déconnexion manuelle du serveur"""
    disconnect_from_server()
    emit('disconnected', {'reason': 'Déconnexion manuelle'})

def disconnect_from_server():
    """Fermer la connexion au serveur"""
    global client_socket, connected
    
    connected = False
    
    if client_socket:
        try:
            client_socket.close()
        except:
            pass
        client_socket = None
    
    print("[FERMETURE] Connexion fermée.")


@app.route('/files/client/<path:subpath>')
def serve_client_files(subpath):
    root = str(CLIENT_FILES_DIR)
    return send_from_directory(root, subpath, as_attachment=True)


@socketio.on('send_file')
def handle_send_file(data):
    """Réception d'un fichier depuis l'UI client et envoi au serveur TCP."""
    global client_socket, connected
    if not connected or not client_socket:
        emit('error', {'message': 'Non connecté au serveur.'})
        return

    filename = os.path.basename(data.get('filename', ''))
    mimetype = data.get('mimetype', 'application/octet-stream')
    b64 = data.get('data_base64', '')

    if not filename or not b64:
        emit('error', {'message': 'Fichier invalide.'})
        return

    try:
        print(f"[CLIENT] Envoi de fichier demandé: {filename} ({mimetype})")
        raw = base64.b64decode(b64.encode('utf-8'))
        if len(raw) > 2 * 1024 * 1024:
            emit('error', {'message': 'Fichier trop volumineux (max 2 Mo).'})
            return
        save_path = CLIENT_SENT_DIR / filename
        with open(save_path, 'wb') as f:
            f.write(raw)
        
        line = f"__FILE__|{filename}|{mimetype}|{len(raw)}|{b64}\n"
        client_socket.send(line.encode('utf-8'))
        
        # Sauvegarder dans SQLite
        timestamp = datetime.now().isoformat()
        db.save_file(
            1,  # Client ID (constant: 1)
            filename,
            mimetype,
            len(raw),
            'sent',
            username,
            str(save_path),
            timestamp
        )
        
        emit('file_sent', {'filename': filename, 'mimetype': mimetype, 'size': len(raw)})
    except Exception as e:
        print(f"[ERREUR] Envoi fichier: {e}")
        emit('error', {'message': f"Erreur envoi fichier: {str(e)}"})

if __name__ == '__main__':
    print('[WEB] Serveur client web démarré sur http://localhost:5001')
    print('[INFO] Ouvrez http://localhost:5001 dans votre navigateur pour utiliser le client')
    socketio.run(app, host='127.0.0.1', port=5001, debug=False, allow_unsafe_werkzeug=True)