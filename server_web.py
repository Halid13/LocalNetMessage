from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import socket
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'localnetmessage-secret-key-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration du serveur TCP
HOST = '0.0.0.0'
PORT = 12345

# Dictionnaire des mots-clés pour terminer la conversation
EXIT_KEYWORDS = [
    'quit', 'exit', 'au revoir', 'aurevoir', 'à plus', 'a plus',
    'bye', 'goodbye', 'ciao', 'salut', 'tchao', 'bye bye',
    'à bientôt', 'a bientot', 'adieu', 'fin'
]

# Stockage des clients connectés
clients = {}  # {client_id: {'socket': socket_obj, 'address': address_string}}
client_counter = 0

def handle_client(client_socket, client_address, client_id):
    """Gère la communication avec un client TCP connecté"""
    global clients
    
    address_str = f"{client_address[0]}:{client_address[1]}"
    print(f"[NOUVELLE CONNEXION] Client {client_id} - {address_str}")
    
    # Notifier l'interface web
    socketio.emit('client_connected', {
        'client_id': client_id,
        'address': address_str
    })
    
    try:
        connected = True
        while connected:
            # Recevoir le message du client
            message = client_socket.recv(1024).decode('utf-8')
            
            if not message:
                break
            
            # Vérifier si le message contient un mot-clé de sortie
            if message.lower().strip() in EXIT_KEYWORDS:
                print(f"[DÉCONNEXION] Client {client_id} se déconnecte (mot-clé: '{message}').")
                client_socket.send("Au revoir !".encode('utf-8'))
                connected = False
            else:
                print(f"[Client {client_id}] {message}")
                
                # Envoyer le message à l'interface web
                socketio.emit('message_received', {
                    'client_id': client_id,
                    'address': address_str,
                    'message': message
                })
    
    except Exception as e:
        print(f"[ERREUR] Client {client_id}: {e}")
    
    finally:
        # Supprimer le client de la liste
        if client_id in clients:
            del clients[client_id]
        
        client_socket.close()
        print(f"[FERMETURE] Client {client_id} déconnecté.")
        
        # Notifier l'interface web
        socketio.emit('client_disconnected', {
            'client_id': client_id,
            'address': address_str
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
            # Accepter une nouvelle connexion
            client_socket, client_address = server.accept()
            
            # Générer un ID unique pour le client
            client_counter += 1
            client_id = client_counter
            
            # Stocker le client
            clients[client_id] = {
                'socket': client_socket,
                'address': f"{client_address[0]}:{client_address[1]}"
            }
            
            # Créer un thread pour gérer le client
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

# Routes Flask
@app.route('/')
def index():
    """Page d'accueil - Interface du serveur"""
    return render_template('server.html')

# Événements SocketIO
@socketio.on('connect')
def handle_connect():
    """Client web connecté"""
    print('[WEB] Client web connecté')
    # Envoyer la liste actuelle des clients
    emit('clients_update', {
        'clients': [
            {'id': cid, 'address': cdata['address']}
            for cid, cdata in clients.items()
        ]
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Client web déconnecté"""
    print('[WEB] Client web déconnecté')

@socketio.on('send_message')
def handle_send_message(data):
    """Envoyer un message à un client spécifique"""
    client_id = data.get('client_id')
    message = data.get('message', '').strip()
    
    if not message or client_id not in clients:
        return
    
    client_socket = clients[client_id]['socket']
    
    try:
        # Envoyer le message au client TCP
        client_socket.send(message.encode('utf-8'))
        
        # Confirmer l'envoi à l'interface web
        emit('message_sent', {
            'client_id': client_id,
            'message': message
        })
        
        print(f"[ENVOYÉ] Message envoyé au client {client_id}: {message}")
        
        # Vérifier si c'est un mot-clé de sortie
        if message.lower().strip() in EXIT_KEYWORDS:
            print(f"[DÉCONNEXION] Terminaison de la conversation avec client {client_id}")
            # La déconnexion sera gérée par le thread du client
    
    except Exception as e:
        print(f"[ERREUR] Impossible d'envoyer au client {client_id}: {e}")
        emit('error', {'message': 'Erreur lors de l\'envoi du message'})

if __name__ == '__main__':
    # Démarrer le serveur TCP dans un thread séparé
    tcp_thread = threading.Thread(target=start_tcp_server)
    tcp_thread.daemon = True
    tcp_thread.start()
    
    # Démarrer le serveur web Flask
    print('[WEB] Serveur web démarré sur http://127.0.0.1:5000')
    print('[INFO] Ouvrez http://localhost:5000 dans votre navigateur')
    socketio.run(app, host='127.0.0.1', port=5000, debug=False, allow_unsafe_werkzeug=True)
