import socket
import threading

# Configuration du serveur
HOST = '0.0.0.0'  # Écoute sur toutes les interfaces réseau
PORT = 5555       # Port d'écoute

# Dictionnaire des mots-clés pour terminer la conversation
EXIT_KEYWORDS = [
    'quit', 'exit', 'au revoir', 'aurevoir', 'à plus', 'a plus',
    'bye', 'goodbye', 'ciao', 'tchao', 'bye bye',
    'à bientôt', 'a bientot', 'adieu', 'fin'
]

def handle_client(client_socket, client_address):
    """Gère la communication avec un client connecté"""
    print(f"[NOUVELLE CONNEXION] {client_address} connecté.")
    
    try:
        connected = True
        while connected:
            # Recevoir le message du client
            message = client_socket.recv(1024).decode('utf-8')
            
            if not message:
                break
            
            # Vérifier si le message contient un mot-clé de sortie
            if message.lower().strip() in EXIT_KEYWORDS:
                print(f"[DÉCONNEXION] {client_address} se déconnecte (mot-clé: '{message}').")
                client_socket.send("Au revoir !".encode('utf-8'))
                connected = False
            else:
                print(f"[{client_address}] {message}")
                
                # Envoyer une réponse au client
                response = input(f"Réponse pour {client_address}: ")
                client_socket.send(response.encode('utf-8'))
                
                # Vérifier si la réponse contient un mot-clé de sortie
                if response.lower().strip() in EXIT_KEYWORDS:
                    print(f"[DÉCONNEXION] Vous avez terminé la conversation avec {client_address}.")
                    connected = False
    
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    finally:
        client_socket.close()
        print(f"[FERMETURE] Connexion avec {client_address} fermée.")

def start_server():
    """Démarre le serveur et accepte les connexions"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    
    print(f"[DÉMARRAGE] Serveur en écoute sur {HOST}:{PORT}")
    print("[EN ATTENTE] En attente de connexions...")
    
    try:
        while True:
            # Accepter une nouvelle connexion
            client_socket, client_address = server.accept()
            
            # Créer un thread pour gérer le client
            thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            thread.start()
            
            print(f"[CONNEXIONS ACTIVES] {threading.active_count() - 1}")
    
    except KeyboardInterrupt:
        print("\n[ARRÊT] Arrêt du serveur...")
    
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
