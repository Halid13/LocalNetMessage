import socket

# Configuration du client
SERVER_HOST = '127.0.0.1'  # Adresse IP du serveur (localhost par défaut)
SERVER_PORT = 5555         # Port du serveur

def start_client():
    """Démarre le client et se connecte au serveur"""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Connexion au serveur
        client.connect((SERVER_HOST, SERVER_PORT))
        print(f"[CONNECTÉ] Connecté au serveur {SERVER_HOST}:{SERVER_PORT}")
        print("Tapez 'quit' pour quitter.\n")
        
        connected = True
        while connected:
            # Envoyer un message au serveur
            message = input("Vous: ")
            client.send(message.encode('utf-8'))
            
            if message.lower() == 'quit':
                print("[DÉCONNEXION] Déconnexion du serveur...")
                connected = False
            else:
                # Recevoir la réponse du serveur
                response = client.recv(1024).decode('utf-8')
                
                if not response or response.lower() == 'quit':
                    print("[DÉCONNEXION] Le serveur a fermé la connexion.")
                    connected = False
                else:
                    print(f"Serveur: {response}\n")
    
    except ConnectionRefusedError:
        print(f"[ERREUR] Impossible de se connecter au serveur {SERVER_HOST}:{SERVER_PORT}")
        print("Vérifiez que le serveur est bien démarré.")
    
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    finally:
        client.close()
        print("[FERMETURE] Connexion fermée.")

if __name__ == "__main__":
    start_client()
