/* ========================================
   GESTION DE L'INTERFACE DE CHIFFREMENT
   ======================================== */

class EncryptionUI {
    constructor() {
        this.modalOpen = false;
        this.encryption = window.encryption;
        
        if (!this.encryption) {
            console.error('❌ encryption.js n\'a pas été chargé correctement');
            return;
        }
        
        this.init();
    }

    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupUI());
        } else {
            this.setupUI();
        }
    }

    setupUI() {
        if (!document.getElementById('encryption-panel')) {
            this.createEncryptionPanel();
        }

        this.attachEventListeners();

        this.updateEncryptionStatus();
        this.updateKeyDisplay();
    }

    createEncryptionPanel() {
        const panel = document.createElement('div');
        panel.id = 'encryption-panel';
        panel.className = 'encryption-panel';
        panel.innerHTML = `
            <button id="encryption-btn" class="encryption-btn" title="Paramètres de chiffrement">
                🔒
                <span id="encryption-status" class="encryption-status"></span>
            </button>
            <div id="encryption-modal" class="encryption-modal">
                <div class="encryption-modal-content">
                    <button class="encryption-close-btn" id="encryption-close-btn">✕</button>
                    
                    <div class="encryption-title">Chiffrement des Messages</div>
                    
                    <div class="encryption-info">
                        <strong>🔐 Informations:</strong> Les messages seront chiffrés avec votre clé privée avant d'être envoyés. Seul celui qui possède la clé peut les déchiffrer.
                    </div>

                    <!-- Toggle de chiffrement -->
                    <div class="encryption-section">
                        <div class="encryption-section-title">Activer le chiffrement</div>
                        <div class="encryption-toggle">
                            <div class="toggle-switch" id="encryption-toggle"></div>
                            <span id="encryption-toggle-text">Désactivé</span>
                        </div>
                    </div>

                    <!-- Gestion de la clé -->
                    <div class="encryption-section">
                        <div class="encryption-section-title">Votre Clé Privée</div>
                        <div class="encryption-key-display" id="encryption-key-display">
                            Clé non générée
                        </div>
                        <div class="encryption-key-actions">
                            <button class="encryption-btn-small" id="encryption-new-key-btn">
                                🔄 Nouvelle Clé
                            </button>
                            <button class="encryption-btn-small" id="encryption-copy-key-btn">
                                📋 Copier
                            </button>
                            <button class="encryption-btn-small danger" id="encryption-reset-btn">
                                🗑️ Réinitialiser
                            </button>
                        </div>
                    </div>

                    <!-- Import de clé -->
                    <div class="encryption-section">
                        <div class="encryption-section-title">Importer une Clé</div>
                        <input 
                            type="text" 
                            id="encryption-import-input" 
                            class="encryption-input"
                            placeholder="Collez ici la clé à importer"
                        >
                        <div class="encryption-key-actions">
                            <button class="encryption-btn-small" id="encryption-import-btn">
                                📥 Importer
                            </button>
                        </div>
                    </div>

                    <!-- État du chiffrement -->
                    <div class="encryption-section">
                        <div class="encryption-status-indicator" id="encryption-status-text">
                            <span class="status-dot-small"></span>
                            Chiffrement activé
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(panel);
    }

    attachEventListeners() {
        const encryptionBtn = document.getElementById('encryption-btn');
        if (encryptionBtn) {
            encryptionBtn.addEventListener('click', () => this.toggleModal());
        }

        const closeBtn = document.getElementById('encryption-close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.toggleModal());
        }

        const modal = document.getElementById('encryption-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.toggleModal();
                }
            });
        }

        const encryptionToggleParent = document.querySelector('.encryption-toggle');
        if (encryptionToggleParent) {
            encryptionToggleParent.addEventListener('click', () => this.toggleEncryption());
        }
        
        const encryptionToggle = document.getElementById('encryption-toggle');
        if (encryptionToggle) {
            encryptionToggle.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }

        const newKeyBtn = document.getElementById('encryption-new-key-btn');
        if (newKeyBtn) {
            newKeyBtn.addEventListener('click', () => this.generateNewKey());
        }

        const copyKeyBtn = document.getElementById('encryption-copy-key-btn');
        if (copyKeyBtn) {
            copyKeyBtn.addEventListener('click', () => this.copyKeyToClipboard());
        }

        const resetBtn = document.getElementById('encryption-reset-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetEncryption());
        }

        const importBtn = document.getElementById('encryption-import-btn');
        if (importBtn) {
            importBtn.addEventListener('click', () => this.importKey());
        }

        this.updateEncryptionStatus();
    }

    toggleModal() {
        const modal = document.getElementById('encryption-modal');
        if (modal) {
            modal.classList.toggle('open');
            this.modalOpen = !this.modalOpen;
            this.updateKeyDisplay();
        }
    }

    toggleEncryption() {
        const currentState = this.encryption.isEnabled();
        this.encryption.setEncryptionEnabled(!currentState);
        this.updateEncryptionStatus();

        this.showNotification(
            !currentState ? '🔒 Chiffrement activé' : '🔓 Chiffrement désactivé',
            !currentState ? '#48bb78' : '#f56565'
        );
    }

    generateNewKey() {
        const oldKey = this.encryption.getKey();
        this.encryption.resetKey();
        this.updateKeyDisplay();

        this.showNotification(
            '🔄 Nouvelle clé générée avec succès',
            '#667eea'
        );

        console.log('Nouvelle clé de chiffrement générée');
    }

    copyKeyToClipboard() {
        const key = this.encryption.getKey();
        if (!key) {
            this.showNotification('❌ Aucune clé à copier', '#f56565');
            return;
        }

        navigator.clipboard.writeText(key).then(() => {
            this.showNotification('✅ Clé copiée dans le presse-papiers', '#48bb78');
        }).catch(err => {
            this.showNotification('❌ Erreur lors de la copie', '#f56565');
            console.error('Erreur de copie:', err);
        });
    }

    resetEncryption() {
        const confirmed = confirm(
            '⚠️ Êtes-vous sûr? Votre clé de chiffrement sera réinitialisée et vous ne pourrez plus déchiffrer les anciens messages.'
        );

        if (confirmed) {
            this.encryption.resetKey();
            this.encryption.setEncryptionEnabled(false);
            this.updateEncryptionStatus();
            this.updateKeyDisplay();

            this.showNotification(
                '🔄 Chiffrement réinitialisé',
                '#f56565'
            );
        }
    }

    importKey() {
        const input = document.getElementById('encryption-import-input');
        const importedKey = input.value.trim();

        if (!importedKey) {
            this.showNotification('❌ Veuillez entrer une clé', '#f56565');
            return;
        }

        const isValid = this.encryption.verifyKey(importedKey);
        if (!isValid) {
            this.showNotification('❌ Clé invalide (32+ caractères hexadécimaux attendus)', '#f56565');
            return;
        }

        this.encryption.setKey(importedKey.trim());
        this.encryption.setEncryptionEnabled(true);
        input.value = '';
        this.updateEncryptionStatus();
        this.updateKeyDisplay();

        this.updateEncryptionStatus();
        this.updateKeyDisplay();

        this.showNotification(
            '✅ Clé importée avec succès',
            '#48bb78'
        );
    }

    updateEncryptionStatus() {
        const isEnabled = this.encryption.isEnabled();

        const toggle = document.getElementById('encryption-toggle');
        if (toggle) {
            toggle.classList.toggle('active', isEnabled);
        }

        const toggleText = document.getElementById('encryption-toggle-text');
        if (toggleText) {
            toggleText.textContent = isEnabled ? 'Activé' : 'Désactivé';
        }

        const statusIndicator = document.getElementById('encryption-status');
        if (statusIndicator) {
            statusIndicator.classList.toggle('disabled', !isEnabled);
        }

        const statusText = document.getElementById('encryption-status-text');
        if (statusText) {
            const statusDot = statusText.querySelector('.status-dot-small');
            if (statusDot) {
                statusDot.classList.toggle('disabled', !isEnabled);
            }
            statusText.textContent = (isEnabled ? '🔒' : '🔓') + ' ' + 
                                     (isEnabled ? 'Chiffrement activé' : 'Chiffrement désactivé');
        }

        const encryptionBtn = document.getElementById('encryption-btn');
        if (encryptionBtn) {
            encryptionBtn.textContent = isEnabled ? '🔒' : '🔓';
        }
    }

    updateKeyDisplay() {
        const key = this.encryption.getKey();
        const keyDisplay = document.getElementById('encryption-key-display');

        if (keyDisplay) {
            if (key) {
                const formatted = this.encryption.formatKeyForDisplay();
                keyDisplay.textContent = formatted;
            } else {
                keyDisplay.textContent = 'Clé non générée';
            }
        }
    }

    showNotification(message, color = '#667eea') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            bottom: 100px;
            right: 20px;
            background: ${color};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            font-weight: 600;
            z-index: 999;
            animation: slideIn 0.3s ease;
            max-width: 300px;
        `;
        notification.textContent = message;

        document.body.appendChild(notification);

        const style = document.createElement('style');
        if (!document.getElementById('notification-styles')) {
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
                @keyframes slideOut {
                    from {
                        transform: translateX(0);
                        opacity: 1;
                    }
                    to {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
}

const encryptionUI = new EncryptionUI();

window.encryptionUI = encryptionUI;
