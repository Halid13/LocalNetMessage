from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import socket
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'localnetmessage-secret-key-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

HOST = '0.0.0.0'
PORT = 12345

server_username = 'Serveur'

EXIT_KEYWORDS = [
    'quit', 'exit', 'au revoir', 'aurevoir', 'à plus', 'a plus',
    'bye', 'goodbye', 'ciao', 'salut', 'tchao', 'bye bye',
    'à bientôt', 'a bientot', 'adieu', 'fin'
]

clients = {}
client_counter = 0

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

    try:
        client_socket.send(f"__SERVER_NAME__:{server_username}".encode('utf-8'))
    except Exception as e:
        print(f"[AVERTISSEMENT] Impossible d'envoyer le nom du serveur au client {client_id}: {e}")
    
    socketio.emit('client_connected', {
        'client_id': client_id,
        'address': address_str,
        'username': username
    })
    
    try:
        connected = True
        while connected:
            message = client_socket.recv(1024).decode('utf-8')
            
            if not message:
                break
            
            if message.lower().strip() in EXIT_KEYWORDS:
                print(f"[DÉCONNEXION] {username} se déconnecte (mot-clé: '{message}').")
                client_socket.send("Au revoir !".encode('utf-8'))
                connected = False
            else:
                if client_id in clients:
                    clients[client_id]['messages'].append({
                        'type': 'received',
                        'sender': username,
                        'message': message,
                        'timestamp': __import__('datetime').datetime.now().isoformat(),
                        'read': False
                    })
                
                socketio.emit('message_received', {
                    'client_id': client_id,
                    'address': address_str,
                    'username': username,
                    'message': message
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
        return jsonify({'success': True, 'username': server_username})
    else:
        return jsonify({'success': False, 'error': 'Nom d\'utilisateur invalide'}), 400

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
    
    if client_id in clients:
        emit('client_messages', {
            'client_id': client_id,
            'messages': clients[client_id]['messages']
        })
    else:
        emit('client_messages', {
            'client_id': client_id,
            'messages': []
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
        client_socket.send(message.encode('utf-8'))
        
        clients[client_id]['messages'].append({
            'type': 'sent',
            'sender': 'Serveur',
            'message': message,
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'read': False
        })
        
        emit('message_sent', {
            'client_id': client_id,
            'message': message
        })
        
        if message.lower().strip() in EXIT_KEYWORDS:
            print(f"[DÉCONNEXION] Terminaison de la conversation avec client {client_id}")
    
    except Exception as e:
        print(f"[ERREUR] Impossible d'envoyer au client {client_id}: {e}")
        emit('error', {'message': 'Erreur lors de l\'envoi du message'})

if __name__ == '__main__':
    tcp_thread = threading.Thread(target=start_tcp_server)
    tcp_thread.daemon = True
    tcp_thread.start()
    
    print('[WEB] Serveur web démarré sur http://127.0.0.1:5000')
    print('[INFO] Ouvrez http://localhost:5000 dans votre navigateur')
    socketio.run(app, host='127.0.0.1', port=5000, debug=False, allow_unsafe_werkzeug=True)
