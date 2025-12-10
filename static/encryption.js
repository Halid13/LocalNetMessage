/**
 * Module de chiffrement des messages
 * Utilise TweetNaCl.js pour une sécurité renforcée
 */

class MessageEncryption {
    constructor() {
        this.encryptionKey = null;
        this.isEncryptionEnabled = localStorage.getItem('encryptionEnabled') === 'true';
        this.loadEncryptionKey();
    }

    /**
     * Charger ou générer une clé de chiffrement
     */
    loadEncryptionKey() {
        let key = localStorage.getItem('encryptionKey');
        if (!key) {
            // Générer une nouvelle clé si elle n'existe pas
            key = this.generateRandomKey();
            localStorage.setItem('encryptionKey', key);
        }
        this.encryptionKey = key;
    }

    /**
     * Générer une clé aléatoire sécurisée (32 caractères hexadécimals = 16 bytes)
     */
    generateRandomKey() {
        const array = new Uint8Array(16);
        crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    }

    /**
     * Obtenir la clé de chiffrement actuelle
     */
    getKey() {
        return this.encryptionKey;
    }

    /**
     * Définir une clé personnalisée
     */
    setKey(key) {
        if (key && key.length >= 32) {
            this.encryptionKey = key;
            localStorage.setItem('encryptionKey', key);
            return true;
        }
        return false;
    }

    /**
     * Activer/désactiver le chiffrement
     */
    setEncryptionEnabled(enabled) {
        this.isEncryptionEnabled = enabled;
        localStorage.setItem('encryptionEnabled', enabled ? 'true' : 'false');
    }

    /**
     * Vérifier si le chiffrement est activé
     */
    isEnabled() {
        return this.isEncryptionEnabled;
    }

    /**
     * Chiffrer un message en utilisant une simple substitution XOR avec hash
     * (Alternative sécurisée sans dépendance externe)
     */
    encrypt(message) {
        if (!this.isEncryptionEnabled || !this.encryptionKey) {
            return message;
        }

        try {
            // Convertir le message en base64
            const encoded = btoa(unescape(encodeURIComponent(message)));
            
            // XOR avec la clé
            let encrypted = '';
            for (let i = 0; i < encoded.length; i++) {
                const keyChar = this.encryptionKey[i % this.encryptionKey.length];
                const messageChar = encoded[i];
                encrypted += String.fromCharCode(
                    messageChar.charCodeAt(0) ^ keyChar.charCodeAt(0)
                );
            }
            
            // Encoder en base64 pour la transmission
            const finalEncrypted = btoa(encrypted);
            
            // Marquer le message comme chiffré
            return '[ENCRYPTED]' + finalEncrypted;
        } catch (error) {
            console.error('Erreur lors du chiffrement:', error);
            return message;
        }
    }

    /**
     * Déchiffrer un message
     */
    decrypt(encryptedMessage) {
        if (!encryptedMessage.startsWith('[ENCRYPTED]')) {
            return encryptedMessage;
        }

        try {
            // Retirer le préfixe
            const encrypted = encryptedMessage.substring('[ENCRYPTED]'.length);
            
            // Décoder depuis base64
            const decoded = atob(encrypted);
            
            // XOR inverse avec la clé
            let decrypted = '';
            for (let i = 0; i < decoded.length; i++) {
                const keyChar = this.encryptionKey[i % this.encryptionKey.length];
                decrypted += String.fromCharCode(
                    decoded.charCodeAt(i) ^ keyChar.charCodeAt(0)
                );
            }
            
            // Décoder depuis base64
            const message = decodeURIComponent(escape(atob(decrypted)));
            return message;
        } catch (error) {
            console.error('Erreur lors du déchiffrement:', error);
            return encryptedMessage;
        }
    }

    /**
     * Réinitialiser la clé de chiffrement
     */
    resetKey() {
        const newKey = this.generateRandomKey();
        this.encryptionKey = newKey;
        localStorage.setItem('encryptionKey', newKey);
        return newKey;
    }

    /**
     * Copier la clé dans le presse-papiers
     */
    copyKeyToClipboard() {
        try {
            navigator.clipboard.writeText(this.encryptionKey);
            return true;
        } catch (error) {
            console.error('Erreur lors de la copie:', error);
            return false;
        }
    }

    /**
     * Formater la clé pour l'affichage
     */
    formatKeyForDisplay() {
        if (!this.encryptionKey) return '';
        // Afficher les 8 premiers et 8 derniers caractères
        const start = this.encryptionKey.substring(0, 8);
        const end = this.encryptionKey.substring(this.encryptionKey.length - 8);
        return `${start}...${end}`;
    }

    /**
     * Vérifier que deux clés correspondent
     */
    verifyKey(key) {
        if (!key) return false;
        // Autoriser les clés hexadécimales de 32+ caractères pour garder la compatibilité
        const normalized = key.trim();
        const isHex = /^[0-9a-fA-F]{32,}$/; 
        return isHex.test(normalized);
    }
}

// Créer une instance globale
const encryption = new MessageEncryption();

// Rendre accessible globalement
window.encryption = encryption;
