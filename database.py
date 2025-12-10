"""
Database module for LocalNetMessage
Gère la persistance des messages et fichiers avec SQLite
"""

import sqlite3
import json
import threading
from pathlib import Path
from datetime import datetime

class Database:
    """Classe pour gérer les opérations SQLite"""
    
    def __init__(self, db_path='messages.db'):
        """
        Initialise la connexion à la base de données SQLite
        
        Args:
            db_path: chemin du fichier SQLite (défaut: messages.db)
        """
        self.db_path = Path(db_path)
        self.lock = threading.Lock()
        self._init_db()
    
    def _get_connection(self):
        """Retourne une connexion SQLite thread-safe"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Crée les tables si elles n'existent pas"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Table des messages
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('received', 'sent')),
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    read BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Index pour optimiser les requêtes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_client_id ON messages(client_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp)
            ''')
            
            # Table des fichiers
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    mimetype TEXT,
                    size INTEGER NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('received', 'sent')),
                    sender TEXT NOT NULL,
                    file_path TEXT,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_file_client_id ON files(client_id)
            ''')
            
            # Table d'historique des clients
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS client_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    address TEXT,
                    first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_seen TEXT,
                    message_count INTEGER DEFAULT 0,
                    file_count INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
            conn.close()
    
    def save_message(self, client_id, message_type, sender, message, timestamp):
        """
        Sauvegarde un message dans la base de données
        
        Args:
            client_id: ID du client
            message_type: 'received' ou 'sent'
            sender: nom de l'expéditeur
            message: contenu du message
            timestamp: timestamp ISO du message
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO messages 
                (client_id, type, sender, message, timestamp, read)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (client_id, message_type, sender, message, timestamp, 0))
            
            conn.commit()
            msg_id = cursor.lastrowid
            conn.close()
            
            return msg_id
    
    def get_messages(self, client_id):
        """
        Récupère tous les messages d'un client
        
        Args:
            client_id: ID du client
        
        Returns:
            Liste de dictionnaires (messages)
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, type, sender, message, timestamp, read
                FROM messages
                WHERE client_id = ?
                ORDER BY timestamp ASC
            ''', (client_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
    
    def mark_messages_read(self, client_id):
        """
        Marque tous les messages reçus d'un client comme lus
        
        Args:
            client_id: ID du client
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE messages
                SET read = 1
                WHERE client_id = ? AND type = 'received'
            ''', (client_id,))
            
            conn.commit()
            conn.close()
    
    def save_file(self, client_id, filename, mimetype, size, file_type, sender, file_path, timestamp):
        """
        Sauvegarde les métadonnées d'un fichier
        
        Args:
            client_id: ID du client
            filename: nom du fichier
            mimetype: type MIME
            size: taille en octets
            file_type: 'received' ou 'sent'
            sender: nom de l'expéditeur
            file_path: chemin du fichier stocké
            timestamp: timestamp ISO
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO files
                (client_id, filename, mimetype, size, type, sender, file_path, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (client_id, filename, mimetype, size, file_type, sender, file_path, timestamp))
            
            conn.commit()
            file_id = cursor.lastrowid
            conn.close()
            
            return file_id
    
    def get_files(self, client_id):
        """
        Récupère tous les fichiers d'un client
        
        Args:
            client_id: ID du client
        
        Returns:
            Liste de dictionnaires (fichiers)
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, filename, mimetype, size, type, sender, file_path, timestamp
                FROM files
                WHERE client_id = ?
                ORDER BY timestamp ASC
            ''', (client_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
    
    def update_client_history(self, client_id, username, address):
        """
        Crée ou met à jour l'historique d'un client
        
        Args:
            client_id: ID du client
            username: nom d'utilisateur
            address: adresse IP:port
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id FROM client_history WHERE client_id = ?
            ''', (client_id,))
            
            if cursor.fetchone():
                cursor.execute('''
                    UPDATE client_history
                    SET last_seen = CURRENT_TIMESTAMP, username = ?
                    WHERE client_id = ?
                ''', (username, client_id))
            else:
                cursor.execute('''
                    INSERT INTO client_history (client_id, username, address)
                    VALUES (?, ?, ?)
                ''', (client_id, username, address))
            
            conn.commit()
            conn.close()
    
    def get_client_history(self, client_id):
        """
        Récupère l'historique d'un client
        
        Args:
            client_id: ID du client
        
        Returns:
            Dictionnaire avec infos du client ou None
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM client_history WHERE client_id = ?
            ''', (client_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            return dict(row) if row else None
    
    def get_all_client_history(self):
        """
        Récupère l'historique de tous les clients
        
        Returns:
            Liste de dictionnaires (clients)
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM client_history ORDER BY last_seen DESC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
    
    def increment_message_count(self, client_id):
        """Incrémente le compteur de messages pour un client"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE client_history
                SET message_count = message_count + 1
                WHERE client_id = ?
            ''', (client_id,))
            
            conn.commit()
            conn.close()
    
    def increment_file_count(self, client_id):
        """Incrémente le compteur de fichiers pour un client"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE client_history
                SET file_count = file_count + 1
                WHERE client_id = ?
            ''', (client_id,))
            
            conn.commit()
            conn.close()
    
    def delete_old_messages(self, days=30):
        """
        Supprime les messages antérieurs à X jours (archivage)
        
        Args:
            days: nombre de jours avant suppression
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM messages
                WHERE created_at < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            return deleted
    
    def export_to_json(self, client_id, output_path):
        """
        Exporte les messages et fichiers d'un client en JSON
        
        Args:
            client_id: ID du client
            output_path: chemin du fichier JSON de sortie
        """
        with self.lock:
            messages = self.get_messages(client_id)
            files = self.get_files(client_id)
            client_history = self.get_client_history(client_id)
            
            export_data = {
                'client': client_history,
                'messages': messages,
                'files': files
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return output_path
    
    def close(self):
        """Ferme la connexion à la base de données"""
        pass  # Les connexions sont fermeées après chaque opération
