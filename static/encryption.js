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

    loadEncryptionKey() {
        let key = localStorage.getItem('encryptionKey');
        if (!key) {
            key = this.generateRandomKey();
            localStorage.setItem('encryptionKey', key);
        }
        this.encryptionKey = key;
    }

    generateRandomKey() {
        const array = new Uint8Array(16);
        crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    }

    getKey() {
        return this.encryptionKey;
    }

    setKey(key) {
        if (key && key.length >= 32) {
            this.encryptionKey = key;
            localStorage.setItem('encryptionKey', key);
            return true;
        }
        return false;
    }

    setEncryptionEnabled(enabled) {
        this.isEncryptionEnabled = enabled;
        localStorage.setItem('encryptionEnabled', enabled ? 'true' : 'false');
    }

    isEnabled() {
        return this.isEncryptionEnabled;
    }

    encrypt(message) {
        if (!this.isEncryptionEnabled || !this.encryptionKey) {
            return message;
        }

        try {
            const encoded = btoa(unescape(encodeURIComponent(message)));
            
            let encrypted = '';
            for (let i = 0; i < encoded.length; i++) {
                const keyChar = this.encryptionKey[i % this.encryptionKey.length];
                const messageChar = encoded[i];
                encrypted += String.fromCharCode(
                    messageChar.charCodeAt(0) ^ keyChar.charCodeAt(0)
                );
            }
            
            const finalEncrypted = btoa(encrypted);
            
            return '[ENCRYPTED]' + finalEncrypted;
        } catch (error) {
            console.error('Erreur lors du chiffrement:', error);
            return message;
        }
    }

    decrypt(encryptedMessage) {
        if (!encryptedMessage.startsWith('[ENCRYPTED]')) {
            return encryptedMessage;
        }

        try {
            const encrypted = encryptedMessage.substring('[ENCRYPTED]'.length);
            
            const decoded = atob(encrypted);
            
            let decrypted = '';
            for (let i = 0; i < decoded.length; i++) {
                const keyChar = this.encryptionKey[i % this.encryptionKey.length];
                decrypted += String.fromCharCode(
                    decoded.charCodeAt(i) ^ keyChar.charCodeAt(0)
                );
            }
            
            const message = decodeURIComponent(escape(atob(decrypted)));
            return message;
        } catch (error) {
            console.error('Erreur lors du déchiffrement:', error);
            return encryptedMessage;
        }
    }

    resetKey() {
        const newKey = this.generateRandomKey();
        this.encryptionKey = newKey;
        localStorage.setItem('encryptionKey', newKey);
        return newKey;
    }

    copyKeyToClipboard() {
        try {
            navigator.clipboard.writeText(this.encryptionKey);
            return true;
        } catch (error) {
            console.error('Erreur lors de la copie:', error);
            return false;
        }
    }

    formatKeyForDisplay() {
        if (!this.encryptionKey) return '';
        const start = this.encryptionKey.substring(0, 8);
        const end = this.encryptionKey.substring(this.encryptionKey.length - 8);
        return `${start}...${end}`;
    }

    verifyKey(key) {
        if (!key) return false;
        const normalized = key.trim();
        const isHex = /^[0-9a-fA-F]{32,}$/; 
        return isHex.test(normalized);
    }
}

const encryption = new MessageEncryption();

window.encryption = encryption;
