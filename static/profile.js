(function(){
  const THEMES = ['violet','rose','cyan','green','orange','turquoise','peach','indigo','coral'];
  const isServer = !!document.querySelector('body.server-view') || !!document.getElementById('server-container');
  const storageKey = isServer ? 'serverProfile' : 'clientProfile';
  const defaultProfile = {
    displayName: isServer ? 'Serveur' : '',
    status: '',
    avatar: '🙂',
    theme: localStorage.getItem('selectedTheme') || 'violet',
    encryptionDefault: false
  };

  function loadProfile(){
    try {
      const raw = localStorage.getItem(storageKey);
      return raw ? {...defaultProfile, ...JSON.parse(raw)} : {...defaultProfile};
    } catch { return {...defaultProfile}; }
  }
  function saveProfile(p){ localStorage.setItem(storageKey, JSON.stringify(p)); }

  function applyProfile(p, updateBackend = false){
    // Theme
    if (typeof window.setTheme === 'function') {
      window.setTheme(p.theme);
    } else {
      document.documentElement.setAttribute('data-theme', p.theme);
      localStorage.setItem('selectedTheme', p.theme);
    }
    // Encryption default
    if (p.encryptionDefault && window.encryption && typeof window.encryption.setEncryptionEnabled==='function') {
      window.encryption.setEncryptionEnabled(true);
    }
    // Apply name/avatar to UI
    if (isServer) {
      const nameEl = document.getElementById('server-username-display');
      if (nameEl && p.displayName) nameEl.textContent = p.displayName;
      // Update backend name only when explicitly saving
      if (updateBackend && p.displayName) {
        try { fetch('/set_server_username', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({username: p.displayName})}); } catch {}
      }
    } else {
      const userInput = document.getElementById('username');
      if (userInput && p.displayName && !userInput.value) userInput.value = p.displayName;
    }
    // Avatar in headers if present
    const headerAvatar = document.querySelector('.server-avatar, .logo-wrapper');
    if (headerAvatar) {
      headerAvatar.setAttribute('data-avatar', p.avatar);
    }
  }

  function createUI(){
    // Try to use header button if present; fallback to floating button
    let btn = document.getElementById('profile-btn');
    const needsFloating = !btn;
    if (needsFloating) {
      btn = document.createElement('button');
      btn.className = 'profile-btn';
      btn.id = 'profile-btn';
      btn.title = 'Profil utilisateur';
      btn.textContent = '👤';
    }

    // Modal
    const modal = document.createElement('div');
    modal.className = 'profile-modal';
    modal.id = 'profile-modal';

    const content = document.createElement('div');
    content.className = 'profile-modal-content';
    content.innerHTML = `
      <div class="profile-header">
        <div class="profile-title">Profil ${isServer ? 'Serveur' : 'Client'}</div>
        <button class="profile-close" id="profile-close">✕</button>
      </div>
      <div class="profile-row-inline">
        <div class="profile-avatar-preview" id="profile-avatar-preview">🙂</div>
        <div style="flex:1"></div>
      </div>
      <div class="profile-row">
        <label class="profile-label">Nom d'affichage</label>
        <input id="profile-displayName" class="profile-input" placeholder="Votre nom" />
      </div>
      <div class="profile-row">
        <label class="profile-label">Statut</label>
        <select id="profile-status" class="profile-select">
          <option value="Disponible">Disponible</option>
          <option value="Occupé">Occupé</option>
          <option value="En pause">En pause</option>
        </select>
      </div>
      <div class="profile-row">
        <label class="profile-label">Avatar (emoji ou URL d'image)</label>
        <input id="profile-avatar" class="profile-input" placeholder="🙂 ou https://..." />
      </div>
      <div class="profile-row">
        <label class="profile-label">Thème</label>
        <select id="profile-theme" class="profile-select">
          ${THEMES.map(t=>`<option value="${t}">${t}</option>`).join('')}
        </select>
      </div>
      <div class="profile-row">
        <label class="profile-label">
          <input type="checkbox" id="profile-encryption" /> Activer le chiffrement par défaut
        </label>
      </div>
      <div class="profile-actions">
        <button class="profile-btn-secondary" id="profile-cancel">Annuler</button>
        <button class="profile-btn-primary" id="profile-save">Enregistrer</button>
      </div>
    `;

    modal.appendChild(content);
    if (needsFloating) document.body.appendChild(btn);
    document.body.appendChild(modal);

    // Bind events
    const state = { open:false };
    const open = ()=>{ modal.classList.add('open'); state.open=true; syncForm(); };
    const close = ()=>{ modal.classList.remove('open'); state.open=false; };
    btn.addEventListener('click', open);
    modal.addEventListener('click', (e)=>{ if(e.target===modal) close(); });
    content.querySelector('#profile-close').addEventListener('click', close);
    content.querySelector('#profile-cancel').addEventListener('click', close);

    // Load profile into form
    function syncForm(){
      const p = loadProfile();
      content.querySelector('#profile-displayName').value = p.displayName || '';
      content.querySelector('#profile-status').value = p.status || 'Disponible';
      content.querySelector('#profile-avatar').value = p.avatar || '';
      content.querySelector('#profile-theme').value = p.theme || THEMES[0];
      content.querySelector('#profile-encryption').checked = !!p.encryptionDefault;
      const prev = content.querySelector('#profile-avatar-preview');
      if (p.avatar && /^https?:\/\//.test(p.avatar)) {
        prev.innerHTML = `<img src="${p.avatar}" alt="avatar"/>`;
      } else {
        prev.textContent = p.avatar || '🙂';
      }
    }

    content.querySelector('#profile-avatar').addEventListener('input', (e)=>{
      const v = e.target.value.trim();
      const prev = content.querySelector('#profile-avatar-preview');
      if (/^https?:\/\//.test(v)) { prev.innerHTML = `<img src="${v}" alt="avatar"/>`; }
      else { prev.textContent = v || '🙂'; }
    });

    content.querySelector('#profile-save').addEventListener('click', ()=>{
      const p = loadProfile();
      const oldName = p.displayName;
      const oldStatus = p.status;
      p.displayName = content.querySelector('#profile-displayName').value.trim();
      p.status = content.querySelector('#profile-status').value.trim();
      p.avatar = content.querySelector('#profile-avatar').value.trim() || '🙂';
      p.theme = content.querySelector('#profile-theme').value;
      p.encryptionDefault = content.querySelector('#profile-encryption').checked;
      saveProfile(p);
      applyProfile(p, true); // updateBackend = true when explicitly saving
      
      // If client-side, emit rename_user if name changed
      if (!isServer && oldName !== p.displayName && p.displayName && window.socket) {
        try { window.socket.emit('rename_user', {username: p.displayName}); } catch (e) { console.warn('Could not emit rename_user:', e); }
      }
      
      // Emit status change if status changed
      if (!isServer && oldStatus !== p.status && window.socket && p.status) {
        try { 
          console.log('Émission change_status:', p.status);
          window.socket.emit('change_status', {status: p.status || 'Disponible'}); 
        } catch (e) { 
          console.warn('Could not emit change_status:', e); 
        }
      }
      
      // Server status change
      if (isServer && oldStatus !== p.status && p.status) {
        try { 
          fetch('/set_server_status', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({status: p.status || 'Disponible'})}); 
        } catch (e) { 
          console.warn('Could not set server status:', e); 
        }
      }
      
      close();
    });
  }

  // Initialize
  function init(){
    // Inject CSS if not present
    if (!document.querySelector('link[href*="/static/profile.css"]')){
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = '/static/profile.css';
      document.head.appendChild(link);
    }
    createUI();
    applyProfile(loadProfile());
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
