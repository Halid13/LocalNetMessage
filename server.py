import socket
import threading

# Configuration du serveur
HOST = '0.0.0.0'  # Écoute sur toutes les interfaces réseau
PORT = 5555       # Port d'écoute

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
            
            if message.lower() == 'quit':
                print(f"[DÉCONNEXION] {client_address} se déconnecte.")
                connected = False
            else:
                print(f"[{client_address}] {message}")
                
                # Envoyer une réponse au client
                response = input(f"Réponse pour {client_address}: ")
                client_socket.send(response.encode('utf-8'))
                
                if response.lower() == 'quit':
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
