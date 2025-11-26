import socket

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5555

EXIT_KEYWORDS = [
    'quit', 'exit', 'au revoir', 'aurevoir', 'à plus', 'a plus',
    'bye', 'goodbye', 'ciao', 'tchao', 'bye bye',
    'à bientôt', 'a bientot', 'adieu', 'fin'
]

def start_client():
    """Démarre le client et se connecte au serveur"""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect((SERVER_HOST, SERVER_PORT))
        print(f"[CONNECTÉ] Connecté au serveur {SERVER_HOST}:{SERVER_PORT}")
        print("Tapez un mot de sortie (quit, au revoir, bye, etc.) pour quitter.\n")
        
        connected = True
        while connected:
            message = input("Vous: ")
            client.send(message.encode('utf-8'))
            
            if message.lower().strip() in EXIT_KEYWORDS:
                print("[DÉCONNEXION] Déconnexion du serveur...")
                try:
                    response = client.recv(1024).decode('utf-8')
                    if response:
                        print(f"Serveur: {response}")
                except:
                    pass
                connected = False
            else:
                response = client.recv(1024).decode('utf-8')
                
                if not response:
                    print("[DÉCONNEXION] Le serveur a fermé la connexion.")
                    connected = False
                elif response.lower().strip() in EXIT_KEYWORDS:
                    print(f"Serveur: {response}")
                    print("[DÉCONNEXION] Le serveur a terminé la conversation.")
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
