from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import socket
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'localnetmessage-client-secret-key-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

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
message_counter = 0

def receive_messages():
    """Thread pour recevoir les messages du serveur"""
    global client_socket, connected
    
    try:
        while connected:
            if client_socket:
                try:
                    message = client_socket.recv(1024).decode('utf-8')
                    
                    if not message:
                        print("[DÉCONNEXION] Le serveur a fermé la connexion.")
                        socketio.emit('disconnected', {'reason': 'Serveur déconnecté'})
                        connected = False
                        break
                    
                    if message.startswith("__SERVER_NAME__:"):
                        global server_display_name
                        server_display_name = message.split(":", 1)[1].strip() or 'Serveur'
                        print(f"[INFO] Nom du serveur défini: {server_display_name}")
                    else:
                        socketio.emit('message_received', {
                            'message': message,
                            'server_username': server_display_name
                        })
                    
                    if message.lower().strip() in EXIT_KEYWORDS:
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
        
        client_socket.send(username.encode('utf-8'))
        
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
        
        client_socket.send(message.encode('utf-8'))
        
        emit('message_sent', {
            'message': message,
            'message_id': message_id
        })
        
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

if __name__ == '__main__':
    print('[WEB] Serveur client web démarré sur http://localhost:5001')
    print('[INFO] Ouvrez http://localhost:5001 dans votre navigateur pour utiliser le client')
    socketio.run(app, host='127.0.0.1', port=5001, debug=False, allow_unsafe_werkzeug=True)
