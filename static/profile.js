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
    if (typeof window.setTheme === 'function') {
      window.setTheme(p.theme);
    } else {
      document.documentElement.setAttribute('data-theme', p.theme);
      localStorage.setItem('selectedTheme', p.theme);
    }
    if (p.encryptionDefault && window.encryption && typeof window.encryption.setEncryptionEnabled==='function') {
      window.encryption.setEncryptionEnabled(true);
    }
    if (isServer) {
      const nameEl = document.getElementById('server-username-display');
      if (nameEl && p.displayName) nameEl.textContent = p.displayName;
      if (updateBackend && p.displayName) {
        try { fetch('/set_server_username', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({username: p.displayName})}); } catch {}
      }
      if (updateBackend && p.avatar) {
        try { fetch('/set_server_avatar', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({avatar: p.avatar})}); } catch {}
      }
    } else {
      const userInput = document.getElementById('username');
      if (userInput && p.displayName && !userInput.value) userInput.value = p.displayName;
      if (updateBackend && p.avatar && window.socket) {
        try { window.socket.emit('change_avatar', {avatar: p.avatar}); } catch {}
      }
    }
    
    saveProfile(p);
    const headerAvatar = document.querySelector('.server-avatar, .logo-wrapper');
    if (headerAvatar) {
      headerAvatar.setAttribute('data-avatar', p.avatar);
    }

    try { window.currentProfile = p; } catch {}
    try { window.dispatchEvent(new CustomEvent('profile-updated', { detail: p })); } catch {}
    
    updateProfileButtonDisplay(p.avatar);
  }

  function updateProfileButtonDisplay(avatar) {
    const btn = document.getElementById('profile-btn');
    if (!btn) return;
    if (avatar && (avatar.startsWith('http://') || avatar.startsWith('https://') || avatar.startsWith('data:image/'))) {
      btn.innerHTML = `<img src="${avatar}" alt="profile" style="width:100%;height:100%;object-fit:cover;border-radius:50%;"/>`;
    } else if (avatar && avatar.length <= 4 && /\p{Emoji}/u.test(avatar)) {
      btn.textContent = avatar;
    } else {
      btn.textContent = '👤';
    }
  }

  function createUI(){
    let btn = document.getElementById('profile-btn');
    const needsFloating = !btn;
    if (needsFloating) {
      btn = document.createElement('button');
      btn.className = 'profile-btn';
      btn.id = 'profile-btn';
      btn.title = 'Profil utilisateur';
      btn.textContent = '👤';
    }

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
        <label class="profile-label">Avatar (emoji, URL ou photo)</label>
        <div style="display:flex; gap:8px; align-items:center;">
          <input id="profile-avatar" class="profile-input" placeholder="🙂 ou https://..." style="flex:1;" />
          <input id="profile-avatar-file" type="file" accept="image/*" style="display:none;" />
          <button class="profile-btn-secondary" id="profile-avatar-upload" type="button">Importer</button>
        </div>
        <div class="profile-hint" style="font-size:12px; color:#666; margin-top:6px;">Taille conseillée ≤ 256 Ko. Les formats data URL et lien HTTP(S) sont supportés.</div>
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

    const state = { open:false };
    const open = ()=>{ modal.classList.add('open'); state.open=true; syncForm(); };
    const close = ()=>{ modal.classList.remove('open'); state.open=false; };
    btn.addEventListener('click', open);
    modal.addEventListener('click', (e)=>{ if(e.target===modal) close(); });
    content.querySelector('#profile-close').addEventListener('click', close);
    content.querySelector('#profile-cancel').addEventListener('click', close);

    function syncForm(){
      const p = loadProfile();
      content.querySelector('#profile-displayName').value = p.displayName || '';
      content.querySelector('#profile-status').value = p.status || 'Disponible';
      content.querySelector('#profile-avatar').value = p.avatar || '';
      content.querySelector('#profile-theme').value = p.theme || THEMES[0];
      content.querySelector('#profile-encryption').checked = !!p.encryptionDefault;
      const prev = content.querySelector('#profile-avatar-preview');
      if (p.avatar && (/^https?:\/\//.test(p.avatar) || p.avatar.startsWith('data:image/'))) {
        prev.innerHTML = `<img src="${p.avatar}" alt="avatar"/>`;
      } else {
        prev.textContent = p.avatar || '🙂';
      }
    }

    content.querySelector('#profile-avatar').addEventListener('input', (e)=>{
      const v = e.target.value.trim();
      const prev = content.querySelector('#profile-avatar-preview');
      if ((/^https?:\/\//.test(v)) || v.startsWith('data:image/')) { prev.innerHTML = `<img src="${v}" alt="avatar"/>`; }
      else { prev.textContent = v || '🙂'; }
    });

    const uploadBtn = content.querySelector('#profile-avatar-upload');
    const uploadInput = content.querySelector('#profile-avatar-file');
    uploadBtn.addEventListener('click', ()=> uploadInput.click());
    uploadInput.addEventListener('change', (e)=>{
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      if (!file.type.startsWith('image/')) { alert('Veuillez sélectionner une image.'); e.target.value=''; return; }
      if (file.size > 256 * 1024) { alert('Image trop volumineuse (max 256 Ko).'); e.target.value=''; return; }
      const reader = new FileReader();
      reader.onload = ()=>{
        const dataUrl = reader.result;
        content.querySelector('#profile-avatar').value = dataUrl;
        const prev = content.querySelector('#profile-avatar-preview');
        prev.innerHTML = `<img src="${dataUrl}" alt="avatar"/>`;
      };
      reader.readAsDataURL(file);
      e.target.value='';
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
      applyProfile(p, true);
      
      if (!isServer && oldName !== p.displayName && p.displayName && window.socket) {
        try { window.socket.emit('rename_user', {username: p.displayName}); } catch (e) { console.warn('Could not emit rename_user:', e); }
      }
      
      if (!isServer && oldStatus !== p.status && window.socket && p.status) {
        try { 
          console.log('Émission change_status:', p.status);
          window.socket.emit('change_status', {status: p.status || 'Disponible'}); 
        } catch (e) { 
          console.warn('Could not emit change_status:', e); 
        }
      }
      
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

  function init(){
    if (!document.querySelector('link[href*="/static/profile.css"]')){
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = '/static/profile.css';
      document.head.appendChild(link);
    }
    createUI();
    const profile = loadProfile();
    applyProfile(profile);
    updateProfileButtonDisplay(profile.avatar);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
