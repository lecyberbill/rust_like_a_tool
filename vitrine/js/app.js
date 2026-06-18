// [WFGY] Zone: SAFE | λ: 0.2 | Action: Handle WORKSPACE_CREATED in websocket onmessage loop



try {
    promptHistory = JSON.parse(localStorage.getItem('prompt_history')) || [];
} catch (e) {
    promptHistory = [];
}

let AUTH_TOKEN = localStorage.getItem('auth_token') || '';
let AUTH_MODE = 'login'; // 'login' | 'register'

function getJwtPayload() {
    if (!AUTH_TOKEN) return null;
    try {
        const body = AUTH_TOKEN.split('.')[1];
        return JSON.parse(atob(body.replace(/-/g, '+').replace(/_/g, '/')));
    } catch (e) { return null; }
}

function addLog(message, type = 'info') {
    const logsDiv = document.getElementById('logs');
    if (!logsDiv) return;
    const time = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `<span class="log-time">[${time}]</span><span class="log-${type}">${message}</span>`;
    logsDiv.appendChild(entry);
    logsDiv.scrollTop = logsDiv.scrollHeight;
}

function changeEnvPod(env) {
    activeEnv = env;
    document.querySelectorAll('.env-pod-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.env === env);
    });
    addLog(`Environnement basculé sur : ${env.toUpperCase()}`, 'info');
    detectAndRenderEnvVars();
}

async function promoteEnv() {
    const wsId = currentRecipe ? currentRecipe.plan_id : null;
    if (!wsId) { showToast('Aucun flux actif', 'warning'); return; }
    const envOrder = ['dev', 'test', 'prod'];
    const idx = envOrder.indexOf(activeEnv);
    if (idx < 0 || idx >= envOrder.length - 1) {
        showToast('Deja au niveau le plus eleve (' + activeEnv.toUpperCase() + ')', 'warning');
        return;
    }
    const target = envOrder[idx + 1];
    if (!confirm(`Promouvoir les variables de ${activeEnv.toUpperCase()} vers ${target.toUpperCase()} ?`)) return;
    try {
        const r = await fetch(`/api/workspace/${wsId}/promote`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source_env: activeEnv, target_env: target })
        });
        const data = await r.json();
        if (data.ok) showToast(`Variables ${data.vars_pushed} poussees de ${activeEnv.toUpperCase()} vers ${target.toUpperCase()}`, 'success');
        else showToast('Erreur: ' + (data.error || 'inconnue'), 'error');
    } catch (e) { showToast('Erreur: ' + e.message, 'error'); }
}

function toggleLogs() {
    const panel = document.getElementById('log-panel');
    if (panel) panel.classList.toggle('collapsed');
}

function toggleEnv() {
    const panel = document.getElementById('env-panel');
    if (panel) panel.classList.toggle('collapsed');
}

function changeActiveEnv() {
    const envSel = document.getElementById('env-selector');
    if (!envSel) return;
    activeEnv = envSel.value;
    const title = document.getElementById('env-panel-title');
    if (title) title.innerText = `Secrets (${activeEnv.toUpperCase()})`;
    addLog(`Environnement actif basculé sur : ${activeEnv.toUpperCase()}`, 'info');
    detectAndRenderEnvVars();
}

class WorkflowNode extends HTMLElement {
    connectedCallback() {
        const label = this.getAttribute('label');
        const primitive = this.getAttribute('primitive');
        const step = this.getAttribute('step');
        
        this.className = 'node pending';
        this.id = `node-step-${step}`;
        this.style.left = this.getAttribute('x') + 'px';
        this.style.top = this.getAttribute('y') + 'px';
        this.style.position = 'absolute';
        this.style.display = 'block';
        this.style.cursor = 'grab';
        
        this.innerHTML = `
            <div class="node-input-handle" data-step="${step}"></div>
            <div class="node-header">
                <span>${label}</span>
                <div style="display: flex; align-items: center; gap: 4px;">
                    <span class="node-edit-badge" title="Éditer" onclick="event.stopPropagation(); editNode(${step})">✏️</span>
                    <span class="status-badge"></span>
                </div>
            </div>
            <div class="node-primitive">${primitive}</div>
            <div class="node-output-handle" data-step="${step}"></div>
        `;

        const outputHandle = this.querySelector('.node-output-handle');
        if (outputHandle) {
            outputHandle.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                e.preventDefault();
                startDrawingConnection(Number(step), e);
            });
        }
        
        this.addEventListener('dblclick', () => {
            const prim = this.getAttribute('primitive');
            if (prim === 'core.sub_flow' || prim === 'core.loop') {
                drillDown(Number(step), label);
            }
        });

        this.addEventListener('click', () => {
            requestDataPreview(Number(step));
        });

        let isDragging = false;
        let startX, startY;
        let initialLeft, initialTop;

        this.addEventListener('mousedown', (e) => {
            if (isPanMode) return;
            if (e.target.closest('.node-edit-badge') || e.target.closest('button') || e.target.closest('input')) return;
            
            isDragging = true;
            this.style.cursor = 'grabbing';
            this.style.transition = 'none';
            this.style.zIndex = '1000';

            startX = e.clientX;
            startY = e.clientY;
            initialLeft = parseInt(this.style.left) || 0;
            initialTop = parseInt(this.style.top) || 0;

            e.preventDefault();
        });

        const onMouseMove = (e) => {
            if (!isDragging) return;
            
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            
            const newLeft = initialLeft + dx;
            const newTop = initialTop + dy;

            this.style.left = newLeft + 'px';
            this.style.top = newTop + 'px';
            
            if (currentRecipe && currentRecipe.steps) {
                const stepObj = currentRecipe.steps.find(s => s.step === Number(step));
                if (stepObj) {
                    if (!stepObj.ui) stepObj.ui = {};
                    stepObj.ui.position = { x: newLeft, y: newTop };
                }
            }

            drawConnections();
        };

        const onMouseUp = () => {
            if (!isDragging) return;
            isDragging = false;
            this.style.cursor = 'grab';
            this.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            this.style.zIndex = '2';
            
            saveActiveWorkspace();
        };

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);

        this._cleanupDrag = () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        };
    }

    disconnectedCallback() {
        if (this._cleanupDrag) {
            this._cleanupDrag();
        }
    }
}
customElements.define('workflow-node', WorkflowNode);

// ── Authentification ────────────────────────────────────────────
async function checkAuthStatus() {
    try {
        const r = await fetch('/api/setup-status');
        const data = await r.json();
        if (!data.has_users) {
            AUTH_MODE = 'register';
            document.getElementById('auth-title').textContent = '👑 Création du Compte Admin';
            document.getElementById('auth-subtitle').textContent = 'Aucun compte existant. Créez votre administrateur.';
            document.getElementById('auth-action-btn').textContent = 'Créer l\'administrateur';
            document.getElementById('auth-alt-action').style.display = 'none';
        } else {
            AUTH_MODE = 'login';
            document.getElementById('auth-title').textContent = '🔐 Connexion';
            document.getElementById('auth-subtitle').textContent = 'Connectez-vous pour accéder à l\'atelier';
            document.getElementById('auth-action-btn').textContent = 'Se connecter';
            document.getElementById('auth-alt-action').style.display = 'block';
            document.getElementById('auth-alt-link').textContent = 'Créer un nouveau compte';
        }
        document.getElementById('auth-error').style.display = 'none';
        document.getElementById('auth-modal').style.display = 'flex';
    } catch (e) {
        addLog('Impossible de vérifier le statut d\'auth sur le serveur.', 'error');
    }
}

function toggleAuthMode() {
    if (AUTH_MODE === 'login') {
        AUTH_MODE = 'register';
        document.getElementById('auth-title').textContent = '📝 Création de Compte';
        document.getElementById('auth-subtitle').textContent = 'Créez un nouveau compte utilisateur';
        document.getElementById('auth-action-btn').textContent = 'Créer le compte';
        document.getElementById('auth-alt-link').textContent = 'Déjà un compte ? Se connecter';
    } else {
        AUTH_MODE = 'login';
        document.getElementById('auth-title').textContent = '🔐 Connexion';
        document.getElementById('auth-subtitle').textContent = 'Connectez-vous pour accéder à l\'atelier';
        document.getElementById('auth-action-btn').textContent = 'Se connecter';
        document.getElementById('auth-alt-link').textContent = 'Créer un nouveau compte';
    }
    document.getElementById('auth-error').style.display = 'none';
}

async function authSubmit() {
    const username = document.getElementById('auth-username').value.trim();
    const password = document.getElementById('auth-password').value;
    const errDiv = document.getElementById('auth-error');
    errDiv.style.display = 'none';

    if (!username || !password) {
        errDiv.textContent = 'Veuillez remplir tous les champs.';
        errDiv.style.display = 'block';
        return;
    }

    try {
        const endpoint = AUTH_MODE === 'login' ? '/api/login' : '/api/register';
        const r = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await r.json();
        if (data.error) {
            errDiv.textContent = data.error;
            errDiv.style.display = 'block';
            return;
        }
        AUTH_TOKEN = data.token;
        localStorage.setItem('auth_token', AUTH_TOKEN);
        document.getElementById('auth-modal').style.display = 'none';
        document.getElementById('logout-btn').style.display = 'inline-flex';
        ['admin-btn', 'admin-btn-header'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'inline-flex';
        });
    }
    catch (e) {
        errDiv.textContent = 'Erreur de connexion au serveur.';
        errDiv.style.display = 'block';
    }
}

function logout() {
    AUTH_TOKEN = '';
    localStorage.removeItem('auth_token');
    document.getElementById('auth-username').value = '';
    document.getElementById('auth-password').value = '';
    document.getElementById('logout-btn').style.display = 'none';
    ['admin-btn', 'admin-btn-header'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
    AUTH_MODE = 'login';
    if (ws) { ws.close(); }
    checkAuthStatus();
}

// ── Admin Panel ──────────────────────────────────────────────
async function openAdminPanel() {
    const tbody = document.getElementById('admin-users-table-body');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 30px; color: var(--text-muted);">Chargement des utilisateurs...</td></tr>';
    document.getElementById('admin-modal').style.display = 'flex';

    try {
        const r = await fetch('/api/users', {
            headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` }
        });
        const users = await r.json();
        if (users.error) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 30px; color: var(--error);">${users.error}</td></tr>`;
            return;
        }
        tbody.innerHTML = '';
        if (!users || users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 30px; color: var(--text-muted);">Aucun utilisateur.</td></tr>';
            return;
        }
        users.forEach(u => {
            const tr = document.createElement('tr');
            tr.style.borderBottom = '1px solid var(--border)';
            const created = u.created_at ? new Date(u.created_at).toLocaleString() : '-';
            tr.innerHTML = `
                <td style="padding: 10px; font-family: monospace;">${u.id}</td>
                <td style="padding: 10px; font-weight: 600;">${u.username}</td>
                <td style="padding: 10px;">
                    <select class="editor-input" onchange="changeUserRole(${u.id}, this.value)" style="width:120px; padding:4px 6px; font-size:0.8rem;">
                        <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>Admin</option>
                        <option value="operator" ${u.role === 'operator' ? 'selected' : ''}>Opérateur</option>
                        <option value="viewer" ${u.role === 'viewer' ? 'selected' : ''}>Lecteur</option>
                    </select>
                </td>
                <td style="padding: 10px; font-family: monospace; font-size:0.8rem;">${u.tenant_id || '-'}</td>
                <td style="padding: 10px; font-size:0.85rem;">${created}</td>
                <td style="padding: 10px; text-align: right;">
                    <button class="toggle-logs-btn" onclick="deleteUser(${u.id})" style="background: rgba(239,68,68,0.05); color: var(--error); border-color: rgba(239,68,68,0.2); padding:4px 10px; font-size:0.8rem;">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 30px; color: var(--error);">Erreur de chargement : ${e.message}</td></tr>`;
    }
}

function closeAdminPanel() {
    document.getElementById('admin-modal').style.display = 'none';
    document.getElementById('admin-create-form').style.display = 'none';
}

function showCreateUserForm() {
    document.getElementById('admin-create-form').style.display = 'flex';
}

function hideCreateUserForm() {
    document.getElementById('admin-create-form').style.display = 'none';
    document.getElementById('admin-new-username').value = '';
    document.getElementById('admin-new-password').value = '';
}

async function createUserFromAdmin() {
    const username = document.getElementById('admin-new-username').value.trim();
    const password = document.getElementById('admin-new-password').value;
    if (!username || !password) { addLog('Veuillez remplir tous les champs.', 'error'); return; }
    try {
        const r = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await r.json();
        if (data.error) { addLog('Erreur création : ' + data.error, 'error'); return; }
        addLog(`Utilisateur '${username}' créé (rôle: operator).`, 'success');
        hideCreateUserForm();
        openAdminPanel();
    } catch (e) {
        addLog('Erreur réseau : ' + e.message, 'error');
    }
}

async function changeUserRole(userId, role) {
    try {
        const r = await fetch('/api/users/role', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${AUTH_TOKEN}` },
            body: JSON.stringify({ user_id: userId, role })
        });
        const data = await r.json();
        if (data.error) {
            addLog(`Erreur changement rôle : ${data.error}`, 'error');
        } else {
            addLog(`Rôle de l'utilisateur ${userId} mis à jour : ${role}`, 'success');
        }
    } catch (e) {
        addLog(`Erreur réseau : ${e.message}`, 'error');
    }
}

async function deleteUser(userId) {
    if (!confirm(`Supprimer l'utilisateur ${userId} ?`)) return;
    try {
        const r = await fetch(`/api/users/${userId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` }
        });
        const data = await r.json();
        if (data.error) {
            addLog(`Erreur suppression : ${data.error}`, 'error');
        } else {
            addLog(`Utilisateur ${userId} supprimé.`, 'success');
            openAdminPanel();
        }
    } catch (e) {
        addLog(`Erreur réseau : ${e.message}`, 'error');
    }
}

// ── Version History ─────────────────────────────────────────
async function openVersionsModal() {
    const container = document.getElementById('versions-list');
    if (!container) return;
    container.innerHTML = '<div style="color: var(--text-muted); font-style: italic; text-align: center; padding: 30px;">Chargement des versions...</div>';
    document.getElementById('versions-modal').style.display = 'flex';

    const workspaceId = currentRecipe ? currentRecipe.plan_id || Object.keys(localWorkspaces)[0] : null;
    if (!workspaceId) {
        container.innerHTML = '<div style="color: var(--text-muted); font-style: italic; text-align: center; padding: 30px;">Aucun workspace actif.</div>';
        return;
    }

    try {
        const r = await fetch(`/api/recipe/versions/${workspaceId}`, {
            headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` }
        });
        const versions = await r.json();
        if (versions.error) {
            container.innerHTML = `<div style="color: var(--error); text-align: center; padding: 30px;">${versions.error}</div>`;
            return;
        }
        container.innerHTML = '';
        if (!versions || versions.length === 0) {
            container.innerHTML = '<div style="color: var(--text-muted); font-style: italic; text-align: center; padding: 30px;">Aucune version disponible.</div>';
            return;
        }
        versions.forEach(v => {
            const card = document.createElement('div');
            card.style.cssText = 'display:flex; justify-content:space-between; align-items:center; padding:12px 16px; border:1px solid var(--border); border-radius:8px; background:rgba(255,255,255,0.02);';
            const ts = v.timestamp ? new Date(v.timestamp).toLocaleString() : '-';
            card.innerHTML = `
                <div>
                    <div style="font-weight:600; font-size:0.9rem; color:var(--accent);">Version ${v.version || '?'}</div>
                    <div style="font-size:0.78rem; color:var(--text-muted); font-family:monospace;">${ts}</div>
                </div>
                <button class="toggle-logs-btn" onclick="rollbackToVersion('${v.version}')" style="background:rgba(245,158,11,0.05); color:var(--running); border-color:rgba(245,158,11,0.2); padding:4px 12px; font-size:0.8rem;">⏪ Restaurer</button>
            `;
            container.appendChild(card);
        });
    } catch (e) {
        container.innerHTML = `<div style="color: var(--error); text-align: center; padding: 30px;">Erreur : ${e.message}</div>`;
    }
}

function closeVersionsModal() {
    document.getElementById('versions-modal').style.display = 'none';
}

async function rollbackToVersion(version) {
    const workspaceId = currentRecipe ? currentRecipe.plan_id || Object.keys(localWorkspaces)[0] : null;
    if (!workspaceId) {
        addLog('Aucun workspace actif pour le rollback.', 'error');
        return;
    }
    try {
        const r = await fetch(`/api/recipe/rollback/${version}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${AUTH_TOKEN}` },
            body: JSON.stringify({ workspace_id: workspaceId })
        });
        const data = await r.json();
        if (data.error) {
            addLog(`Erreur rollback : ${data.error}`, 'error');
        } else {
            addLog(`Recette restaurée vers la version ${version}.`, 'success');
            closeVersionsModal();
        }
    } catch (e) {
        addLog(`Erreur réseau : ${e.message}`, 'error');
    }
}

// ── Toast Notification ──────────────────────────────────────
function showToast(message, type = 'info') {
    const existing = document.querySelector('.toast-notification');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    const colors = { error: 'var(--error)', warning: 'var(--running)', success: 'var(--success)', info: 'var(--accent)' };
    const bg = colors[type] || colors.info;
    toast.style.cssText = `position:fixed;top:20px;right:20px;padding:14px 24px;background:${bg};color:#000;font-weight:700;border-radius:10px;z-index:999;box-shadow:0 8px 32px rgba(0,0,0,0.5);max-width:400px;font-size:0.9rem;`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity 0.5s'; setTimeout(() => toast.remove(), 500); }, 4000);
}

// ── Connection Manager ───────────────────────────────────────
async function openConnectionManager() {
    const container = document.getElementById('connection-aliases-list');
    if (!container) return;
    document.getElementById('connection-manager-modal').style.display = 'flex';
    container.innerHTML = '<div style="color:var(--text-muted);text-align:center;padding:20px;">Chargement...</div>';
    try {
        const r = await fetch('/api/vault/aliases');
        const aliases = await r.json();
        const entries = Object.entries(aliases);
        if (entries.length === 0) { container.innerHTML = '<div style="color:var(--text-muted);text-align:center;padding:20px;">Aucune connexion enregistree.</div>'; return; }
        container.innerHTML = entries.map(([k, v]) => `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;border:1px solid var(--border);border-radius:6px;">
            <span style="font-weight:600;font-family:monospace;">${k}</span>
            <span style="color:var(--text-muted);font-size:0.8rem;font-family:monospace;max-width:300px;overflow:hidden;text-overflow:ellipsis;">${v}</span>
        </div>`).join('');
    } catch (e) { container.innerHTML = '<div style="color:var(--error);text-align:center;padding:20px;">Erreur: ' + e.message + '</div>'; }
}
function closeConnectionManager() { document.getElementById('connection-manager-modal').style.display = 'none'; }
async function saveConnectionAlias() {
    const key = document.getElementById('conn-alias-key').value.trim();
    const val = document.getElementById('conn-alias-value').value.trim();
    if (!key || !val) { showToast('Remplissez alias et valeur', 'warning'); return; }
    try {
        const r = await fetch('/api/vault/aliases', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({[key]: val}) });
        const data = await r.json();
        if (data.ok) { showToast('Connexion "' + key + '" sauvegardee.', 'success'); document.getElementById('conn-alias-key').value = ''; document.getElementById('conn-alias-value').value = ''; openConnectionManager(); }
        else showToast('Erreur: ' + (data.error || ''), 'error');
    } catch (e) { showToast('Erreur: ' + e.message, 'error'); }
}

// ── File Browser ──────────────────────────────────────────────
async function openFileBrowser() {
    const container = document.getElementById('file-browser-list');
    if (!container) return;
    document.getElementById('file-browser-modal').style.display = 'flex';
    container.innerHTML = '<div style="color:var(--text-muted);text-align:center;padding:30px;">Chargement...</div>';
    try {
        const r = await fetch('/api/workspace/files');
        const files = await r.json();
        if (!files || files.length === 0) { container.innerHTML = '<div style="color:var(--text-muted);text-align:center;padding:30px;">Aucun fichier dans workspace/output/</div>'; return; }
        container.innerHTML = files.map(f => {
            const size = f.size > 1024 ? (f.size/1024).toFixed(1) + ' KB' : f.size + ' B';
            const date = new Date(f.modified * 1000).toLocaleString();
            return `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;border:1px solid var(--border);border-radius:6px;font-size:0.85rem;">
                <span style="font-family:monospace;font-size:0.8rem;">${f.name}</span>
                <span style="color:var(--text-muted);font-size:0.75rem;">${size} - ${date}</span>
            </div>`;
        }).join('');
    } catch (e) { container.innerHTML = '<div style="color:var(--error);text-align:center;padding:30px;">Erreur: ' + e.message + '</div>'; }
}
function closeFileBrowser() { document.getElementById('file-browser-modal').style.display = 'none'; }

// ── Template Gallery ──────────────────────────────────────────
async function openTemplateGallery() {
    const container = document.getElementById('template-list');
    if (!container) return;
    document.getElementById('template-modal').style.display = 'flex';
    container.innerHTML = '<div style="color:var(--text-muted);text-align:center;padding:30px;">Chargement...</div>';
    try {
        const r = await fetch('/api/templates');
        const templates = await r.json();
        if (!templates || templates.length === 0) {
            container.innerHTML = '<div style="color:var(--text-muted);text-align:center;padding:30px;">Aucun gabarit disponible.</div>';
            return;
        }
        container.innerHTML = templates.map(t => {
            const vars = (t.variables || []).map(v => `<div style="font-size:0.8rem;color:var(--text-muted);margin:2px 0;">${v.label}: <input type="text" id="tpl-var-${t.id}-${v.key}" value="${v.default}" placeholder="${v.key}" style="width:120px;padding:2px 6px;border-radius:4px;border:1px solid var(--border);background:rgba(0,0,0,0.3);color:var(--text);font-size:0.75rem;margin-left:6px;"></div>`).join('');
            return `<div style="border:1px solid var(--border);border-radius:8px;padding:14px;"><div style="font-weight:700;color:var(--success);font-size:0.95rem;">${t.name}</div><div style="font-size:0.8rem;color:var(--text-muted);margin:6px 0;">${t.description}</div>${vars}<button class="toggle-logs-btn" onclick="instantiateTemplate('${t.id}')" style="margin-top:8px;background:linear-gradient(135deg,var(--success) 0%,rgba(0,255,102,0.6) 100%);color:#000;border:none;font-weight:800;padding:6px 16px;">➕ Creer le flux</button></div>`;
        }).join('');
    } catch (e) {
        container.innerHTML = '<div style="color:var(--error);text-align:center;padding:30px;">Erreur: ' + e.message + '</div>';
    }
}
function closeTemplateGallery() { document.getElementById('template-modal').style.display = 'none'; }
async function instantiateTemplate(tplId) {
    const vars = {};
    document.querySelectorAll(`[id^="tpl-var-${tplId}-"]`).forEach(el => {
        vars[el.id.replace(`tpl-var-${tplId}-`, '')] = el.value;
    });
    try {
        const r = await fetch('/api/templates/instantiate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ template_id: tplId, variables: vars }) });
        const data = await r.json();
        if (data.recipe) { currentRecipe = data.recipe; renderNodes(getCurrentStepList()); addLog('Gabarit "' + tplId + '" instancie.', 'success'); closeTemplateGallery(); }
        else showToast('Erreur: ' + (data.error || 'inconnue'), 'error');
    } catch (e) { showToast('Erreur: ' + e.message, 'error'); }
}

// ── Notification Config ─────────────────────────────────────
function toggleNotifType() {
    const t = document.getElementById('notif-type').value;
    document.getElementById('notif-smtp-fields').style.display = t === 'smtp' ? '' : 'none';
    document.getElementById('notif-webhook-fields').style.display = t === 'webhook' ? '' : 'none';
}

function toggleWsNotifType() {
    const t = document.getElementById('ws-notif-type').value;
    document.getElementById('ws-notif-smtp-fields').style.display = t === 'smtp' ? '' : 'none';
    document.getElementById('ws-notif-webhook-fields').style.display = t === 'webhook' ? '' : 'none';
}

async function openNotifConfigModal() {
    const modal = document.getElementById('notif-config-modal');
    if (!modal) return;
    modal.style.display = 'flex';
    try {
        const r = await fetch('/api/notif/config');
        const c = await r.json();
        const set = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ''; };
        set('notif-smtp-host', c.smtp_host);
        set('notif-smtp-port', c.smtp_port);
        set('notif-smtp-user', c.smtp_user);
        set('notif-smtp-pass', c.smtp_pass);
        set('notif-smtp-from', c.smtp_from);
        set('notif-smtp-to', c.smtp_to);
        set('notif-webhook-url', c.webhook_url);
    } catch (e) {
        addLog('Impossible de charger la config notifications.', 'error');
    }
}

function closeNotifConfigModal() {
    document.getElementById('notif-config-modal').style.display = 'none';
}

async function saveNotifConfig() {
    const config = {
        smtp_host: document.getElementById('notif-smtp-host').value,
        smtp_port: document.getElementById('notif-smtp-port').value,
        smtp_user: document.getElementById('notif-smtp-user').value,
        smtp_pass: document.getElementById('notif-smtp-pass').value,
        smtp_from: document.getElementById('notif-smtp-from').value,
        smtp_to: document.getElementById('notif-smtp-to').value,
        webhook_url: document.getElementById('notif-webhook-url').value
    };
    try {
        const r = await fetch('/api/notif/config', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        const data = await r.json();
        if (data.ok) addLog('Configuration des notifications sauvegardée.', 'success');
        else addLog('Erreur sauvegarde: ' + (data.error || 'inconnue'), 'error');
    } catch (e) {
        addLog('Erreur de connexion au serveur.', 'error');
    }
    closeNotifConfigModal();
}

async function testNotifConfig() {
    addLog('Test de notification en cours...', 'info');
    const config = {
        smtp_host: document.getElementById('notif-smtp-host').value,
        smtp_port: document.getElementById('notif-smtp-port').value,
        smtp_user: document.getElementById('notif-smtp-user').value,
        smtp_pass: document.getElementById('notif-smtp-pass').value,
        smtp_from: document.getElementById('notif-smtp-from').value,
        smtp_to: document.getElementById('notif-smtp-to').value,
        webhook_url: document.getElementById('notif-webhook-url').value
    };
    try {
        const r = await fetch('/api/notif/test', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        if (!r.ok) {
            addLog('Erreur serveur test notification (HTTP ' + r.status + ')', 'error');
            return;
        }
        const data = await r.json();
        if (data.error) {
            addLog('Erreur test notification: ' + data.error, 'error');
            showToast('Erreur: ' + data.error, 'error');
            return;
        }
        const msg = 'Email: ' + (data.email || 'N/A') + ' | Webhook: ' + (data.webhook || 'N/A');
        addLog(msg, 'info');
        showToast(msg, data.email === 'OK' || data.webhook === 'OK' ? 'success' : 'warning');
    } catch (e) {
        addLog('Erreur test notification: ' + e.message, 'error');
        showToast('Erreur: ' + e.message, 'error');
    }
}

function initWebSocket() {
    const wsHost = window.location.hostname || '127.0.0.1';
    const wsUrl = AUTH_TOKEN ? `ws://${wsHost}:8765/?token=${AUTH_TOKEN}` : `ws://${wsHost}:8765`;
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        addLog('Connecté au serveur d\'orchestration Python.', 'success');
        const statusDiv = document.getElementById('connection-status');
        if (statusDiv) {
            statusDiv.innerHTML = '<span style="width:8px; height:8px; border-radius:50%; background:var(--success); display:inline-block; box-shadow: 0 0 8px var(--success-glow);"></span> Serveur Connecté';
            statusDiv.style.color = 'var(--success)';
        }
        ws.send(JSON.stringify({ type: 'LIST_WORKSPACES' }));
        ws.send(JSON.stringify({ type: 'GET_RUN_HISTORY' }));
    };

    ws.onclose = () => {
        addLog('Connexion perdue avec le serveur. Tentative de reconnexion...', 'error');
        const statusDiv = document.getElementById('connection-status');
        if (statusDiv) {
            statusDiv.innerHTML = '<span style="width:8px; height:8px; border-radius:50%; background:var(--error); display:inline-block;"></span> Serveur Déconnecté';
            statusDiv.style.color = 'var(--error)';
        }
        const conflictModal = document.getElementById('conflict-modal');
        if (conflictModal) conflictModal.classList.remove('active');
        setTimeout(initWebSocket, 2000);
    };

    ws.onerror = (err) => {
        console.error(err);
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'LOG') {
            addLog(data.message, 'info');
        }
        else if (data.type === 'SCHEMA_DETAILS') {
            if (mapperStepNum !== null) {
                const step = currentRecipe.steps.find(s => s.step === mapperStepNum);
                if (step) {
                    const isRight = step.args.right_source === data.filepath || document.getElementById('aimapper-join-right-source').value.trim() === data.filepath;
                    renderSourceColumns(data.headers, isRight);
                    renderMappingRows();
                }
            }
        }
        else if (data.type === 'VAULT_SECRETS') {
            addLog("Coffre-fort d'images Chromatix déverrouillé et chargé en mémoire.", 'success');
            if (!currentRecipe) {
                currentRecipe = { env: data.env };
            } else {
                currentRecipe.env = data.env;
            }
            detectAndRenderEnvVars();
        }
        else if (data.type === 'PLAN_RECEIVED') {
            addLog(`Nouveau plan reçu : ${data.intent_analysis}`, 'info');
            currentRecipe = {
                plan_id: data.plan_id,
                intent_analysis: data.intent_analysis,
                steps: data.steps,
                env: data.env || (currentRecipe ? currentRecipe.env : {}) || {}
            };
            currentNavPath = [];
            updateBreadcrumb();
            saveHistoryState();
            renderNodes(data.steps);
            detectAndRenderEnvVars();
        }
        else if (data.type === 'STUDY_QUESTIONS') {
            addLog("Questions de clarification reçues de l'IA (Mode Étude).", 'info');
            openStudyChat(data.original_intent, data.analysis, data.questions);
        }
        else if (data.type === 'STEP_STATUS') {
            addLog(`Step ${data.step}: [${data.status}] - ${data.log}`, data.status === 'success' ? 'success' : (data.status === 'error' ? 'error' : 'info'));
            updateNodeStatus(data.step, data.status);
        }
        else if (data.type === 'USER_CONFIRMATION_REQUIRED') {
            addLog(`[CONFLIT] Demande de choix reçue pour l'étape ${data.step}`, 'info');
            showConflictModal(data.step, data.message, data.options);
        }
        else if (data.type === 'PLAN_FINISHED') {
            addLog(data.success ? 'Exécution du plan terminée avec SUCCÈS.' : 'Exécution du plan échouée.', data.success ? 'success' : 'error');
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'GET_RUN_HISTORY' }));
            }
        }
        else if (data.type === 'WORKSPACES_LIST') {
            updateWorkspacesList(data.active_workspace, data.workspaces);
        }
        else if (data.type === 'WORKSPACE_CREATED') {
            addLog(`Flux '${data.name}' créé avec succès. Ouverture de l'atelier...`, 'success');
            openWorkspace(data.workspace_id);
        }
        else if (data.type === 'WORKSPACE_EXECUTION_STATE') {
            updateWorkspaceExecutionState(data.workspace_id, data.state);
        }
        else if (data.type === 'PRIMITIVE_DOC') {
            const container = document.getElementById('primitive-doc-container');
            if (container && data.description) {
                const doc = getPrimitiveDoc(data.primitive);
                let params = data.parameters || {};
                let html = `
                    <div class="doc-header">
                        <div class="doc-primitive-name">${data.primitive}</div>
                        <h2 class="doc-label">${doc ? doc.label : data.primitive}</h2>
                        <p class="doc-desc">${data.description}</p>
                    </div>
                `;
                const props = params.properties || {};
                const required = params.required || [];
                if (Object.keys(props).length > 0) {
                    html += `<div class="doc-section-title">Paramètres</div>`;
                    html += `<table class="doc-table"><thead><tr>
                        <th>Paramètre</th><th>Type</th><th class="doc-col-center">Requis</th><th>Défaut</th><th>Description</th>
                    </tr></thead><tbody>`;
                    for (const [pname, pinfo] of Object.entries(props)) {
                        const req = required.includes(pname) ? '<span class="doc-required">Oui</span>' : '<span class="doc-optional">Non</span>';
                        const defVal = pinfo.default !== undefined ? `<code class="doc-code">${JSON.stringify(pinfo.default)}</code>` : '<span class="doc-na">—</span>';
                        let desc = pinfo.description || '';
                        if (pinfo.enum && pinfo.enum.length > 0) {
                            desc += `<div class="doc-enum">Valeurs : ${pinfo.enum.join(', ')}</div>`;
                        }
                        html += `<tr>
                            <td class="doc-cell-name">${pname}</td>
                            <td><code class="doc-code">${pinfo.type}</code></td>
                            <td class="doc-col-center">${req}</td>
                            <td>${defVal}</td>
                            <td class="doc-cell-desc">${desc}</td>
                        </tr>`;
                    }
                    html += `</tbody></table>`;
                }
                container.innerHTML = html;
            }
        }
        else if (data.type === 'RUN_HISTORY_RESULT') {
            renderRunHistoryTimeline(data.history);
        }
        else if (data.type === 'RUN_HISTORY_UPDATE') {
            addLog(`Nouvel enregistrement de télémétrie reçu pour : ${data.workspace_id}`, 'info');
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'GET_RUN_HISTORY' }));
            }
        }
        else if (data.type === 'AUDIT_TRAIL_RESULT') {
            renderAuditTrailList(data.audit);
        }
        else if (data.type === 'AUDIT_TRAIL_UPDATE') {
            addLog(`Nouvel audit immuable enregistré pour le run : ${data.audit.run_id}`, 'info');
            const auditModal = document.getElementById('audit-modal');
            if (auditModal && auditModal.style.display === 'flex') {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: 'GET_AUDIT_TRAIL' }));
                }
            }
        }
        else if (data.type === 'DATA_LINEAGE_RESULT') {
            renderDataLineageOverlays(data.lineage);
        }
        else if (data.type === 'DATA_PREVIEW_RESULT') {
            const contentDiv = document.getElementById('data-preview-content');
            if (!contentDiv) return;
            if (data.error) {
                contentDiv.innerHTML = `
                    <div style="color: var(--error); font-style: italic; text-align: center; padding: 15px; font-size: 0.85rem;">
                        ⚠️ ${data.error}
                    </div>
                `;
            } else if (!data.headers || data.headers.length === 0) {
                contentDiv.innerHTML = `
                    <div style="color: var(--text-muted); font-style: italic; text-align: center; padding: 15px; font-size: 0.85rem;">
                        Fichier vide ou format non pris en charge pour l'aperçu.
                    </div>
                `;
            } else {
                let tableHtml = `<table class="preview-table"><thead><tr>`;
                data.headers.forEach(h => {
                    tableHtml += `<th>${h}</th>`;
                });
                tableHtml += `</tr></thead><tbody>`;
                
                if (!data.rows || data.rows.length === 0) {
                    tableHtml += `<tr><td colspan="${data.headers.length}" style="text-align: center; color: var(--text-muted); font-style: italic;">Aucune ligne de données.</td></tr>`;
                } else {
                    data.rows.forEach(row => {
                        tableHtml += `<tr>`;
                        data.headers.forEach(h => {
                            const val = row[h] !== undefined ? row[h] : '';
                            tableHtml += `<td title="${val}">${val}</td>`;
                        });
                        tableHtml += `</tr>`;
                    });
                }
                tableHtml += `</tbody></table>`;
                contentDiv.innerHTML = tableHtml;
            }
        }
    };
}

function renderRunHistoryTimeline(history) {
    currentRunHistory = history || [];
    const container = document.getElementById('run-history-timeline');
    if (!container) return;

    container.innerHTML = '';
    if (currentRunHistory.length === 0) {
        container.innerHTML = '<div style="color: var(--text-muted); font-style: italic; font-size: 0.9rem; text-align: center; padding-top: 40px;">Aucun run enregistré</div>';
        return;
    }

    currentRunHistory.forEach((run, idx) => {
        const card = document.createElement('div');
        const isSuccess = run.status === 'success';
        card.className = `run-timeline-card ${isSuccess ? 'success' : 'error'}`;
        if (run.run_id === selectedRunId || (selectedRunId === null && idx === 0)) {
            card.classList.add('active');
            if (selectedRunId === null) {
                selectedRunId = run.run_id;
            }
        }

        const date = new Date(run.timestamp);
        const dateStr = date.toLocaleDateString();
        const timeStr = date.toLocaleTimeString();

        card.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <span class="status-indicator"></span>
                <div style="display: flex; flex-direction: column; gap: 2px;">
                    <span style="font-size: 0.85rem; font-weight: 700; color: var(--text);">${run.workspace_id}</span>
                    <span style="font-size: 0.72rem; color: var(--text-muted);">${dateStr} ${timeStr}</span>
                </div>
            </div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.8rem; font-weight: bold; color: ${isSuccess ? 'var(--success)' : 'var(--error)'};">
                ${run.duration_ms} ms
            </div>
        `;

        card.onclick = () => {
            document.querySelectorAll('.run-timeline-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            selectedRunId = run.run_id;
            displayRunPerformance(run);
        };

        container.appendChild(card);
    });

    const activeRun = currentRunHistory.find(r => r.run_id === selectedRunId) || currentRunHistory[0];
    if (activeRun) {
        displayRunPerformance(activeRun);
    }
}

function displayRunPerformance(run) {
    const metaDiv = document.getElementById('selected-run-meta');
    const barsContainer = document.getElementById('run-performance-bars');
    if (!metaDiv || !barsContainer) return;

    metaDiv.innerText = `${run.workspace_id} | Total: ${run.duration_ms} ms`;
    barsContainer.innerHTML = '';

    const steps = run.steps || [];
    if (steps.length === 0) {
        barsContainer.innerHTML = '<div style="color: var(--text-muted); font-style: italic; font-size: 0.9rem; text-align: center; padding-top: 40px;">Aucune étape de performance enregistrée</div>';
        return;
    }

    const maxDuration = Math.max(...steps.map(s => s.duration_ms), 1);

    steps.forEach(step => {
        const row = document.createElement('div');
        row.className = 'performance-bar-row';

        const percent = Math.max((step.duration_ms / maxDuration) * 100, 1);
        const stepStatus = step.status || 'success';

        row.innerHTML = `
            <div class="performance-bar-label">
                <span>Étape ${step.step} : ${step.label} (${stepStatus.toUpperCase()})</span>
                <span style="font-weight: bold;">${step.duration_ms} ms</span>
            </div>
            <div class="performance-bar-container">
                <div class="performance-bar-fill ${stepStatus}" style="width: ${percent}%;"></div>
            </div>
        `;
        barsContainer.appendChild(row);
    });
}

function detectAndRenderEnvVars() {
    const container = document.getElementById('env-vars-container');
    if (!container) return;
    container.innerHTML = '';
    
    if (!currentRecipe || !currentRecipe.steps) {
        container.innerHTML = '<div class="no-vars-msg">Aucun placeholder de secret détecté dans le flux courant.</div>';
        return;
    }

    const placeholders = new Set();
    const regex = /\${([^}]+)}/g;

    currentRecipe.steps.forEach(step => {
        if (step.args) {
            Object.values(step.args).forEach(val => {
                if (typeof val === 'string') {
                    let match;
                    regex.lastIndex = 0;
                    while ((match = regex.exec(val)) !== null) {
                        placeholders.add(match[1]);
                    }
                }
            });
        }
    });

    if (placeholders.size === 0) {
        container.innerHTML = '<div class="no-vars-msg">Aucun placeholder de secret détecté dans le flux courant.</div>';
        return;
    }

    if (!currentRecipe.env) currentRecipe.env = {};
    if (!currentRecipe.env.dev) currentRecipe.env.dev = {};
    if (!currentRecipe.env.test) currentRecipe.env.test = {};
    if (!currentRecipe.env.prod) currentRecipe.env.prod = {};

    placeholders.forEach(varName => {
        const row = document.createElement('div');
        row.className = 'env-var-row';

        const label = document.createElement('label');
        label.innerText = varName;
        
        const input = document.createElement('input');
        input.className = 'env-var-input';
        
        const isSensitive = varName.toLowerCase().includes('secret') || 
                            varName.toLowerCase().includes('pass') || 
                            varName.toLowerCase().includes('key') || 
                            varName.toLowerCase().includes('token');
        
        input.type = isSensitive ? 'password' : 'text';
        input.placeholder = isSensitive ? `Saisir secret pour ${activeEnv.toUpperCase()}...` : `Saisir valeur pour ${activeEnv.toUpperCase()}...`;
        
        input.value = currentRecipe.env[activeEnv][varName] || '';
        
        input.oninput = (e) => {
            currentRecipe.env[activeEnv][varName] = e.target.value;
        };

        row.appendChild(label);
        row.appendChild(input);
        container.appendChild(row);
    });
}

function getCurrentStepList() {
    if (!currentRecipe || !currentRecipe.steps) return [];
    let steps = currentRecipe.steps;
    for (let i = 0; i < currentNavPath.length; i++) {
        const targetStepNum = currentNavPath[i].stepNum;
        const parentNode = steps.find(s => s.step === targetStepNum);
        if (parentNode && parentNode.args && parentNode.args.steps) {
            steps = parentNode.args.steps;
        } else {
            return [];
        }
    }
    return steps;
}

function drillDown(stepNum, label) {
    currentNavPath.push({ stepNum, label });
    updateBreadcrumb();
    const currentSteps = getCurrentStepList();
    renderNodes(currentSteps);
}

function drillUp() {
    if (currentNavPath.length > 0) {
        currentNavPath.pop();
        updateBreadcrumb();
        const currentSteps = getCurrentStepList();
        renderNodes(currentSteps);
    }
}

function updateBreadcrumb() {
    const container = document.getElementById('breadcrumb-items');
    const upBtn = document.getElementById('nested-drillup-btn');
    if (!container || !upBtn) return;

    container.innerHTML = '';
    if (currentNavPath.length === 0) {
        upBtn.style.display = 'none';
        return;
    }

    upBtn.style.display = 'inline-block';
    currentNavPath.forEach((nav, idx) => {
        const span = document.createElement('span');
        span.style.color = '#c084fc';
        span.innerText = ` ➔ ${nav.label}`;
        container.appendChild(span);
    });
}

function updateNodeStatus(step, status) {
    const node = document.getElementById(`node-step-${step}`);
    if (node) {
        node.className = `node ${status}`;
    }
}

function triggerUpload() {
    const fileInput = document.getElementById('recipe-upload');
    if (fileInput) fileInput.click();
}

function uploadRecipe(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const recipe = JSON.parse(e.target.result);
            currentRecipe = recipe;
            renderNodes(recipe.steps);
            detectAndRenderEnvVars();
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'LOAD_RECIPE',
                    recipe: recipe
                }));
            } else {
                addLog('Recette chargée localement mais déconnecté du serveur.', 'error');
            }
        } catch (err) {
            addLog('Erreur lors de la lecture du fichier JSON : ' + err.message, 'error');
        }
    };
    reader.readAsText(file);
}

function downloadRecipe() {
    if (!currentRecipe) {
        addLog('Aucune recette active à sauvegarder.', 'error');
        return;
    }
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentRecipe, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `${currentRecipe.plan_id || 'workflow'}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    addLog('Recette exportée avec succès.', 'success');
}

function appendChatBubble(sender, text) {
    const msgArea = document.getElementById('study-chat-messages');
    if (!msgArea) return;
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;
    bubble.innerHTML = text;
    msgArea.appendChild(bubble);
    msgArea.scrollTop = msgArea.scrollHeight;
}

function togglePromptDrawer() {
    const drawer = document.getElementById('prompt-drawer');
    if (!drawer) return;
    drawer.classList.toggle('active');
    if (drawer.classList.contains('active')) {
        const intentInput = document.getElementById('intent-input');
        if (intentInput) intentInput.focus();
        const settingsDrawer = document.getElementById('settings-drawer');
        if (settingsDrawer) settingsDrawer.classList.remove('active');
    }
}

function toggleSettingsDrawer() {
    const drawer = document.getElementById('settings-drawer');
    if (!drawer) return;
    drawer.classList.toggle('active');
    if (drawer.classList.contains('active')) {
        const promptDrawer = document.getElementById('prompt-drawer');
        if (promptDrawer) promptDrawer.classList.remove('active');
    }
}

const PROVIDER_MODELS = {
    "openai_compatible": [
        { value: "lfm2.5-1.2b-instruct", label: "LiquidAI LFM-1.2B (Instruct)" },
        { value: "lfm2.5-8b-a1b", label: "LiquidAI LFM-8B (Local)" },
        { value: "gemma", label: "Google Gemma (Local)" },
        { value: "custom", label: "Autre modèle local" }
    ],
    "gemini": [
        { value: "gemini-2.5-flash", label: "Gemini 2.5 Flash" },
        { value: "gemini-2.5-pro", label: "Gemini 2.5 Pro" }
    ]
};

function updateSettingsModelOptions() {
    const providerEl = document.getElementById('setting-provider');
    const modelSelect = document.getElementById('setting-model');
    if (!providerEl || !modelSelect) return;
    const provider = providerEl.value;
    const baseUrlGroup = document.getElementById('setting-base-url').parentNode;
    
    modelSelect.innerHTML = '';
    
    const models = PROVIDER_MODELS[provider] || [];
    models.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.value;
        opt.innerText = m.label;
        modelSelect.appendChild(opt);
    });

    if (provider === 'gemini') {
        baseUrlGroup.style.display = 'none';
    } else {
        baseUrlGroup.style.display = 'flex';
    }
}

function savePromptToHistory(prompt) {
    if (!prompt || prompt.trim() === '') return;
    promptHistory = promptHistory.filter(p => p !== prompt);
    promptHistory.unshift(prompt);
    if (promptHistory.length > 50) {
        promptHistory.pop();
    }
    localStorage.setItem('prompt_history', JSON.stringify(promptHistory));
    historyIndex = -1;
}

function togglePromptHistory() {
    const listDiv = document.getElementById('prompt-history-list');
    if (!listDiv) return;
    if (listDiv.style.display === 'none') {
        renderPromptHistory();
        listDiv.style.display = 'block';
    } else {
        listDiv.style.display = 'none';
    }
}

function renderPromptHistory() {
    const container = document.getElementById('prompt-history-list');
    if (!container) return;
    container.innerHTML = '';
    
    if (promptHistory.length === 0) {
        container.innerHTML = '<div style="color:var(--text-muted); font-style:italic; padding:6px; font-size:0.8rem;">Aucun historique de prompt.</div>';
        return;
    }

    promptHistory.forEach((p, idx) => {
        const item = document.createElement('div');
        item.style.cssText = 'padding:6px 10px; border-bottom:1px solid rgba(255,255,255,0.03); cursor:pointer; font-size:0.8rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; transition: background 0.2s;';
        item.innerText = p;
        
        item.addEventListener('mouseenter', () => {
            item.style.background = 'rgba(255,255,255,0.05)';
        });
        item.addEventListener('mouseleave', () => {
            item.style.background = 'transparent';
        });
        item.addEventListener('click', () => {
            const intentInput = document.getElementById('intent-input');
            if (intentInput) intentInput.value = p;
            container.style.display = 'none';
        });
        container.appendChild(item);
    });
}

const intentInput = document.getElementById('intent-input');
if (intentInput) {
    intentInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitIntent();
        }
    });

    intentInput.addEventListener('keydown', function(e) {
        const input = e.target;
        if (e.key === 'ArrowUp' && input.selectionStart === 0) {
            if (promptHistory.length > 0) {
                e.preventDefault();
                if (historyIndex < promptHistory.length - 1) {
                    historyIndex++;
                    input.value = promptHistory[historyIndex];
                    input.selectionStart = input.selectionEnd = input.value.length;
                }
            }
        } else if (e.key === 'ArrowDown' && input.selectionStart === input.value.length) {
            if (promptHistory.length > 0) {
                e.preventDefault();
                if (historyIndex > 0) {
                    historyIndex--;
                    input.value = promptHistory[historyIndex];
                } else if (historyIndex === 0) {
                    historyIndex = -1;
                    input.value = '';
                }
            }
        }
    });
}

const studyChatInput = document.getElementById('study-chat-input');
if (studyChatInput) {
    studyChatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            sendStudyChatReply();
        }
    });
}

function switchTab(tabName) {
    document.querySelectorAll('.nav-tab').forEach(btn => {
        btn.classList.toggle('active', btn.id === `tab-btn-${tabName}`);
    });
    document.querySelectorAll('.view-section').forEach(view => {
        if (view.id === `${tabName}-view`) {
            view.classList.add('active');
            view.style.display = 'flex';
        } else {
            view.classList.remove('active');
            view.style.display = 'none';
        }
    });
    const workshopActions = document.getElementById('workshop-actions');
    if (workshopActions) workshopActions.style.display = tabName === 'workshop' ? 'flex' : 'none';
    const dashboardActions = document.getElementById('dashboard-actions');
    if (dashboardActions) dashboardActions.style.display = tabName === 'dashboard' ? 'flex' : 'none';
    
    if (tabName === 'workshop') {
        setTimeout(() => {
            const currentSteps = getCurrentStepList();
            if (currentSteps && currentSteps.length > 0) {
                renderNodes(currentSteps);
            } else if (currentRecipe && currentRecipe.steps) {
                currentNavPath = [];
                updateBreadcrumb();
                renderNodes(currentRecipe.steps);
            }
        }, 100);
    }
}

let localWorkspaces = {};
function updateWorkspacesList(activeId, workspaces) {
    localWorkspaces = workspaces;
    const tbody = document.getElementById('workspaces-table-body');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    const keys = Object.keys(workspaces);
    if (keys.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 30px;">Aucun flux enregistré. Cliquez sur "+ Nouveau Flux" pour commencer.</td></tr>`;
        return;
    }
    
    keys.forEach(id => {
        const w = workspaces[id];
        const tr = document.createElement('tr');
        tr.id = `workspace-row-${id}`;
        if (id === activeId) {
            tr.style.background = 'rgba(0, 240, 255, 0.03)';
            tr.style.borderLeft = '3px solid var(--accent)';
        }
        
        const isTriggerEnabled = w.trigger && w.trigger.enabled;
        const statusDotClass = isTriggerEnabled ? 'active' : 'inactive';
        
        let lastRunStr = 'Jamais';
        if (w.last_run) {
            lastRunStr = new Date(w.last_run).toLocaleString();
        }
        
        let nextRunStr = 'N/A';
        if (w.next_run && w.next_run !== 'N/A') {
            nextRunStr = new Date(w.next_run).toLocaleString();
        }
        
        let triggerBadge = '<span class="trigger-badge none">Aucun</span>';
        if (isTriggerEnabled) {
            if (w.trigger.type === 'cron') {
                triggerBadge = `<span class="trigger-badge cron" title="${w.trigger.cron_expression}">⏰ Cron</span>`;
            } else if (w.trigger.type === 'event') {
                triggerBadge = `<span class="trigger-badge event" title="${w.trigger.watch_directory} (${w.trigger.pattern})">📁 File Watcher</span>`;
            } else if (w.trigger.type === 'webhook') {
                triggerBadge = `<span class="trigger-badge webhook">🌐 Webhook</span>`;
            }
        }
        
        tr.innerHTML = `
            <td style="padding-left: 25px;">
                <span class="status-dot ${statusDotClass}" id="workspace-dot-${id}"></span>
            </td>
            <td style="font-weight: 600; color: ${id === activeId ? 'var(--accent)' : 'var(--text)'};">
                ${w.name} ${id === activeId ? ' <span style="font-size:0.75rem; color:var(--text-muted); font-weight:normal;">(Actif)</span>' : ''}
            </td>
            <td>${triggerBadge}</td>
            <td id="workspace-last-run-${id}">${lastRunStr}</td>
            <td id="workspace-next-run-${id}">${nextRunStr}</td>
            <td style="text-align: right; gap: 6px; display: flex; justify-content: flex-end; align-items: center; border-bottom: none; padding-top: 8px; padding-bottom: 8px;">
                <button class="toggle-logs-btn" onclick="openWorkspace('${id}')" style="background: rgba(0,240,255,0.05); color: var(--accent); border-color: rgba(0,240,255,0.2);">🛠️ Ouvrir</button>
                <button class="toggle-logs-btn" onclick="configureTrigger('${id}')" style="background: rgba(245,158,11,0.05); color: var(--running); border-color: rgba(245,158,11,0.2);">⚙️ Déclencheur</button>
                <button class="toggle-logs-btn" onclick="openWorkspaceNotif('${id}')" style="background: rgba(192,132,252,0.05); color: #c084fc; border-color: rgba(192,132,252,0.2);">🔔</button>
                <button class="toggle-logs-btn" onclick="renameWorkspace('${id}', '${w.name}')" style="background: rgba(255,255,255,0.02);">✏️</button>
                <button class="toggle-logs-btn" onclick="deleteWorkspace('${id}')" style="background: rgba(239,68,68,0.05); color: var(--error); border-color: rgba(239,68,68,0.2);">🗑️</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function updateWorkspaceExecutionState(id, state) {
    const dot = document.getElementById(`workspace-dot-${id}`);
    if (dot) {
        dot.className = `status-dot ${state}`;
    }
}

const primitiveCatalogData = {
    "I/O (Fichiers)": [
        { name: "io.copy", label: "Copier des fichiers", desc: "Copie un fichier local d'un emplacement vers un autre.", args: { source: "", destination: "", mode: "binary", conflict: "overwrite" } },
        { name: "io.move", label: "Déplacer des fichiers", desc: "Déplace ou renomme un fichier local avec gestion des conflits.", args: { source: "", destination: "", conflict: "overwrite" } },
        { name: "io.delete", label: "Supprimer des fichiers", desc: "Supprime un fichier/dossier avec option de mise à la corbeille.", args: { path: "", secure: "trash", retention_days: "" } },
        { name: "io.metadata", label: "Obtenir les métadonnées", desc: "Lit les métadonnées d'un fichier ou dossier (taille, date, etc.).", args: { path: "" } },
        { name: "io.write_file", label: "Écrire un fichier", desc: "Crée ou écrase un fichier local avec le contenu textuel spécifié.", args: { path: "", content: "" } },
        { name: "io.read_file", label: "Lire un fichier", desc: "Lit un fichier CSV, JSON, XLSX ou Parquet et le met à disposition des étapes suivantes.", args: { source: "", destination: "", format: "auto" } },
        { name: "data.zip", label: "Compresser en ZIP", desc: "Compresse un dossier ou fichier dans une archive ZIP.", args: { source: "", destination: "" } },
        { name: "data.unzip", label: "Décompresser un ZIP", desc: "Décompresse une archive ZIP dans un dossier de destination.", args: { source: "", destination: "" } }
    ],
    "Réseau & Services": [
        { name: "net.download", label: "Télécharger par HTTP", desc: "Télécharge un fichier depuis une URL HTTP/HTTPS.", args: { url: "", destination: "" } },
        { name: "net.upload", label: "Téléverser par HTTP", desc: "Téléverse un fichier local vers un serveur HTTP.", args: { file_path: "", url: "", method: "POST", headers: "" } },
        { name: "net.ftp_download", label: "Télécharger FTP", desc: "Télécharge un fichier depuis un serveur FTP.", args: { host: "", port: "21", user: "", password: "", remote_path: "", local_path: "" } },
        { name: "net.ftp_download_filtered", label: "Télécharger FTP Filtré", desc: "Télécharge sélectivement depuis FTP selon âge/taille (UTC).", args: { host: "", port: "21", user: "", password: "", remote_dir: "", local_dir: "", max_age_hours: "", min_age_hours: "", min_size_mb: "", max_size_mb: "" } },
        { name: "net.ftp_upload", label: "Téléverser FTP", desc: "Téléverse un fichier local vers un serveur FTP.", args: { host: "", port: "21", user: "", password: "", remote_path: "", local_path: "" } },
        { name: "net.sftp_download", label: "Télécharger SFTP", desc: "Télécharge un fichier depuis un serveur SFTP sécurisé (SSH).", args: { host: "", port: "22", user: "", password: "", key_path: "", key_passphrase: "", remote_path: "", local_path: "" } },
        { name: "net.sftp_download_filtered", label: "Télécharger SFTP Filtré", desc: "Télécharge sélectivement depuis SFTP selon âge/taille (UTC).", args: { host: "", port: "22", user: "", password: "", key_path: "", key_passphrase: "", remote_dir: "", local_dir: "", max_age_hours: "", min_age_hours: "", min_size_mb: "", max_size_mb: "" } },
        { name: "net.sftp_upload", label: "Téléverser SFTP", desc: "Téléverse un fichier local vers un serveur SFTP sécurisé (SSH).", args: { host: "", port: "22", user: "", password: "", key_path: "", key_passphrase: "", remote_path: "", local_path: "" } },
        { name: "google.sheets_read", label: "Lire Google Sheets", desc: "Extrait des données depuis Google Sheets vers un fichier local.", args: { credentials: "", spreadsheet_id: "", worksheet_title: "", local_path: "" } },
        { name: "google.sheets_write", label: "Écrire Google Sheets", desc: "Écrit des données depuis un fichier local vers Google Sheets.", args: { credentials: "", spreadsheet_id: "", worksheet_title: "", local_path: "", clear_sheet: true } },
        { name: "net.http_request", label: "Requête HTTP avancée", desc: "Exécute une requête HTTP (GET/POST) avec headers, corps et extraction regex.", args: { url: "", method: "GET", destination: "", headers: "", body: "", extract_regex: "", extract_destination: "" } },
        { name: "net.notify", label: "Notification SMTP / Webhook", desc: "Envoie une alerte par email (SMTP) ou HTTP Webhook, avec pièce jointe optionnelle.", args: { type: "webhook", smtp_host: "localhost", smtp_port: "25", smtp_user: "", smtp_pass: "", to: "", subject: "ETL Alert", url: "", message: "", attachment: "" } },
        { name: "s3.upload", label: "Uploader vers S3", desc: "Téléverse un fichier local vers un bucket S3 (AWS/MinIO).", args: { bucket: "", file_path: "", object_key: "", aws_access_key_id: "", aws_secret_access_key: "", region: "us-east-1", endpoint: "" } },
        { name: "s3.download", label: "Télécharger depuis S3", desc: "Télécharge un objet depuis un bucket S3 vers le stockage local.", args: { bucket: "", object_key: "", destination: "", aws_access_key_id: "", aws_secret_access_key: "", region: "us-east-1", endpoint: "" } }
    ],
    "Transformations de données": [
        { name: "data.filter", label: "Filtrer des lignes", desc: "Filtre les lignes d'un CSV selon une règle logique sur une colonne.", args: { source: "", destination: "", column_name: "", operator: "equals", value: "", delimiter: ",", has_headers: true } },
        { name: "data.clean", label: "Nettoyer et mapper (AiMapper)", desc: "Nettoie, transforme et joint des données (tri, mapping, jointures).", args: { source: "", destination: "", mappings: {}, sort_by: "", sort_descending: false, deduplicate: false, deduplicate_on: "", select_columns: "", fill_na: "", drop_na: false, right_source: "", left_on: "", right_on: "", how_join: "left" } },
        { name: "data.validate", label: "Validation Qualité (DLQ)", desc: "Valide les lignes selon des règles et isole les rejets en quarantaine.", args: { source: "", destination: "", quarantine: "", rules: "[]" } },
        { name: "data.csv_to_json", label: "CSV vers JSON", desc: "Convertit un fichier CSV structuré en fichier JSON.", args: { source: "", destination: "", delimiter: ",", has_headers: true } },
        { name: "data.json_to_csv", label: "JSON vers CSV", desc: "Convertit un fichier JSON (tableau d'objets) en CSV.", args: { source: "", destination: "", delimiter: ",", has_headers: true } },
        { name: "data.xml_to_json", label: "XML vers JSON", desc: "Convertit un fichier XML hiérarchique en fichier JSON.", args: { source: "", destination: "" } },
        { name: "data.json_to_xml", label: "Exporter en XML", desc: "Exporte un tableau JSON/CSV vers un fichier XML structuré.", args: { source: "", destination: "", root_element: "root", row_element: "row" } },
        { name: "data.to_xlsx", label: "Exporter en Excel XLSX", desc: "Exporte un jeu de données (CSV/JSON) vers une feuille Excel .xlsx.", args: { source: "", destination: "", sheet_name: "Sheet1" } },
        { name: "data.delta", label: "Réconciliation Delta CDC", desc: "Compare deux datasets sur clés primaires pour calculer les différences (upserts/deletes).", args: { source: "", target: "", keys: "", destination_upsert: "", destination_delete: "", destination_sync: "" } },
        { name: "data.type_cast", label: "Typage strict de schéma", desc: "Convertit les colonnes vers des types stricts (int, float, bool, string, date).", args: { source: "", destination: "", casts: "{}" } },
        { name: "data.split_out", label: "Séparation Split Out (Explode)", desc: "Explose les colonnes contenant des listes/JSON en lignes distinctes.", args: { source: "", destination: "", column: "", delimiter: "" } },
        { name: "data.lookup", label: "Jointure dictionnaire", desc: "Enrichit le dataset principal par jointure gauche avec un référentiel.", args: { source: "", lookup_file: "", source_key: "", lookup_key: "", lookup_value: "", destination: "" } },
        { name: "data.deduplicate", label: "Supprimer les doublons", desc: "Supprime les lignes dupliquées basées sur des colonnes clés.", args: { source: "", destination: "", subset: "", keep: "first" } },
        { name: "data.anonymize", label: "Masquage / RGPD", desc: "Anonymise les colonnes sensibles (PII) par hash, masquage ou remplacement (format: col1:strategy1,col2:strategy2).", args: { source: "", destination: "", rules: "" } },
        { name: "data.schema_check", label: "Vérification de schéma", desc: "Compare le schéma d'un dataset à un schéma attendu et alerte en cas de dérive.", args: { source: "", expected_schema: "", destination: "" } },
        { name: "data.pivot", label: "Pivoter (format large)", desc: "Pivote une table du format long au format large (lignes en colonnes).", args: { source: "", destination: "", index: "", on: "", values: "", aggregate: "sum" } },
        { name: "data.unpivot", label: "Dépivoter (format long)", desc: "Dépivote une table du format large au format long (colonnes en lignes).", args: { source: "", destination: "", index: "", on: "", variable_name: "variable", value_name: "value" } },
        { name: "data.xml_transform", label: "Transformer XML (XSLT)", desc: "Applique une transformation XSLT sur un fichier XML source.", args: { source: "", stylesheet: "", destination: "" } },
        { name: "data.generate_fake", label: "Générateur de données factices", desc: "Génère des données aléatoires (PII, montants, patterns, dates). Les colonnes se configurent dans le modal dédié.", args: { columns: "", count: "100", format: "csv" } }
    ],
    "Bases de Données": [
        { name: "db.query", label: "Requête SQL SELECT", desc: "Exécute une requête SQL SELECT et écrit le résultat dans un fichier.", args: { connection_string: "", query: "", destination: "" } },
        { name: "db.insert", label: "Insertion SQL", desc: "Importe un fichier CSV/JSON dans une table SQL (SQLite, Postgres, MySQL).", args: { connection_string: "", table_name: "", source: "", mode: "insert", schema_drift: false } },
        { name: "db.upsert", label: "Upsert SQL Idempotent", desc: "Insère ou met à jour des lignes dans une table SQL sur clés primaires.", args: { connection_string: "", table_name: "", source: "", keys: "", schema_drift: false } },
        { name: "data.sync", label: "Sync BDD ↔ Fichier", desc: "Synchronisation bidirectionnelle (INSERT/UPDATE/DELETE) entre un CSV et une table SQL.", args: { source: "", connection_string: "", table_name: "", key_columns: "" } },
        { name: "data.to_db", label: "Exporter vers BDD", desc: "Écrit un dataset dans une table SQL avec création automatique du schéma.", args: { source: "", connection_string: "", table_name: "", mode: "replace" } },
        { name: "mongodb.find", label: "Recherche MongoDB", desc: "Extrait des documents MongoDB vers un fichier JSON.", args: { connection_string: "", database: "", collection: "", filter: "{}", projection: "", destination: "" } },
        { name: "mongodb.insert", label: "Insertion MongoDB", desc: "Importe un fichier CSV/JSON dans une collection MongoDB.", args: { connection_string: "", database: "", collection: "", source: "", mode: "insert" } }
    ],
    "Analytique & Statistiques": [
        { name: "data.groupby", label: "Agrégations Group By", desc: "Groupe les lignes et calcule des agrégations (somme, moyenne, min, max, count).", args: { source: "", destination: "", groupby_columns: "", aggregate_column: "", operation: "sum" } },
        { name: "data.metrics", label: "Statistiques descriptives", desc: "Calcule des métriques (sum, mean, min, max, count, null_count, n_unique).", args: { source: "", column_name: "", operation: "sum", destination_variable: "" } },
        { name: "data.join", label: "Jointure relationnelle", desc: "Réalise une jointure (inner/left/outer) entre deux fichiers de données.", args: { left_source: "", right_source: "", destination: "", left_on: "", right_on: "", how: "inner" } },
        { name: "data.split", label: "Division par colonne", desc: "Divise un dataset en plusieurs fichiers selon les valeurs d'une colonne.", args: { source: "", destination_prefix: "", by_column: "" } },
        { name: "data.merge", label: "Fusion verticale", desc: "Fusionne verticalement plusieurs fichiers de structure identique.", args: { sources: "", destination: "" } },
        { name: "data.chunk_cumulative", label: "Partition par cumul", desc: "Découpe un dataset en fichiers dès qu'un seuil cumulé est franchi.", args: { source: "", destination_prefix: "", accumulate_column: "", threshold: "" } },
        { name: "data.partition", label: "Partitionner par colonne", desc: "Partitionne un dataset en fichiers séparés selon les valeurs d'une colonne.", args: { source: "", destination_dir: "", by_columns: "" } },
        { name: "data.scd", label: "SCD Type 2 (dimension lente)", desc: "Gère les dimensions à évolution lente en comparant source et cible avec versionnement.", args: { source: "", target: "", keys: "", compare_columns: "", destination: "", valid_from_col: "valid_from", valid_to_col: "valid_to", is_current_col: "is_current", valid_from_value: "" } },
        { name: "data.read", label: "Lire tout format", desc: "Lit tout format supporté (CSV, JSON, Parquet, JSONL) et écrit en CSV.", args: { source: "", destination: "" } },
        { name: "data.write", label: "Écrire tout format", desc: "Lit CSV et écrit dans tout format supporté (extension auto-détectée).", args: { source: "", destination: "" } },
        { name: "data.convert", label: "Convertir formats", desc: "Convertit entre tous les formats supportés par auto-détection d'extension.", args: { source: "", destination: "" } }
    ],
    "Intelligence Artificielle": [
        { name: "ai.summarize", label: "Résumé de texte NLP", desc: "Génère des résumés concis via LLM d'une colonne textuelle.", args: { source: "", destination: "", column: "", target_column: "", prompt: "", model_provider: "", model_id: "", base_url: "" } },
        { name: "ai.extract", label: "Extraction d'entités NLP", desc: "Extrait des informations structurées (JSON) via LLM depuis du texte.", args: { source: "", destination: "", column: "", schema: "{}", prompt: "", model_provider: "", model_id: "", base_url: "" } }
    ],
    "Contrôle": [
        { name: "core.condition", label: "Condition logique", desc: "Évalue une expression conditionnelle et exécute des branches.", args: { expression: "", then_steps: [], else_steps: [] } },
        { name: "core.wait", label: "Attente (Retention Wait)", desc: "Pause l'exécution du workflow pendant une durée configurable.", args: { duration: "10" } },
        { name: "core.sub_flow", label: "Sous-flux de traitement", desc: "Exécute un ensemble d'étapes imbriquées comme sous-graphe.", args: { steps: [] } },
        { name: "core.loop", label: "Boucle d'itération", desc: "Itère sur des variables, fichiers ou lignes avec injection de contexte.", args: { loop_over: "variables", items_source: "", pattern: "*", max_age_hours: "", min_age_hours: "", min_size_mb: "", max_size_mb: "", steps: [] } },
        { name: "core.switch", label: "Aiguillage Switch", desc: "Route l'exécution vers différents sous-graphes selon une valeur.", args: { value: "", cases: {} } },
        { name: "flow.report", label: "Rapport d'exécution", desc: "Génère un rapport texte avec les métriques du flux (${STEPS.N.STATUS}, ${FLOW.TOTAL_DURATION_MS}, ...).", args: { template: "", destination: "" } }
    ]
};

// Mapping des arguments qui doivent être rendus en <select> avec leurs options
const primitiveEnums = {
    "io.copy": { mode: ["binary", "text"], conflict: ["overwrite", "skip", "newer"] },
    "io.move": { conflict: ["overwrite", "skip", "newer"] },
    "io.delete": { secure: ["trash", "permanent"] },
    "io.read_file": { format: ["auto", "csv", "json", "xlsx", "parquet"] },
    "net.upload": { method: ["POST", "PUT"] },
    "net.notify": { type: ["webhook", "smtp"] },
    "data.filter": { operator: ["equals", "not_equals", "greater_than", "less_than", "greater_or_equal", "less_or_equal", "contains", "starts_with", "ends_with", "regex", "is_null", "is_not_null"] },
    "data.join": { how: ["inner", "left", "outer", "semi", "anti"] },
    "data.clean": { how_join: ["left", "inner", "outer"] },
    "data.deduplicate": { keep: ["first", "last", "none"] },
    "data.groupby": { operation: ["sum", "mean", "min", "max", "count", "first", "last", "median", "std", "var"] },
    "data.metrics": { operation: ["sum", "mean", "min", "max", "count", "null_count", "n_unique", "std", "var", "median"] },
    "data.pivot": { aggregate: ["sum", "mean", "min", "max", "count", "first", "last"] },
    "ai.summarize": { model_provider: ["openai_compatible", "gemini"] },
    "ai.extract": { model_provider: ["openai_compatible", "gemini"] },
    "core.loop": { loop_over: ["variables", "files", "rows"] },
    "db.insert": { mode: ["insert", "replace", "ignore"] },
    "mongodb.insert": { mode: ["insert", "replace"] },
    "net.http_request": { method: ["GET", "POST", "PUT", "DELETE", "PATCH"] },
    "data.generate_fake": { format: ["csv", "json"] },
    "data.to_db": { mode: ["replace", "append"] }
};

function getPrimitiveDoc(primitiveName) {
    for (const items of Object.values(primitiveCatalogData)) {
        const found = items.find(i => i.name === primitiveName);
        if (found) return found;
    }
    return null;
}

function showPrimitiveDoc(primitiveName) {
    const doc = getPrimitiveDoc(primitiveName);
    if (!doc) {
        addLog(`Documentation introuvable pour '${primitiveName}'`, 'error');
        return;
    }
    const modal = document.getElementById('primitive-doc-modal');
    const container = document.getElementById('primitive-doc-container');
    if (!modal || !container) return;

    let html = `
        <div class="doc-header">
            <div class="doc-primitive-name">${primitiveName}</div>
            <h2 class="doc-label">${doc.label}</h2>
            <p class="doc-desc">${doc.desc || 'Aucune description disponible.'}</p>
        </div>
    `;

    if (doc.params && Object.keys(doc.params).length > 0) {
        html += `<div class="doc-section-title">Paramètres</div>`;
        html += `<table class="doc-table">
            <thead><tr>
                <th>Paramètre</th>
                <th>Type</th>
                <th class="doc-col-center">Requis</th>
                <th>Défaut</th>
                <th>Description</th>
            </tr></thead><tbody>`;

        for (const [pname, pinfo] of Object.entries(doc.params)) {
            const req = pinfo.required ? '<span class="doc-required">Oui</span>' : '<span class="doc-optional">Non</span>';
            const defVal = pinfo.default !== null && pinfo.default !== undefined ? `<code class="doc-code">${JSON.stringify(pinfo.default)}</code>` : '<span class="doc-na">—</span>';
            let desc = pinfo.desc || '';
            if (pinfo.enum && pinfo.enum.length > 0) {
                desc += `<div class="doc-enum">Valeurs autorisées : ${pinfo.enum.join(', ')}</div>`;
            }
            html += `<tr>
                <td class="doc-cell-name">${pname}</td>
                <td><code class="doc-code">${pinfo.type}</code></td>
                <td class="doc-col-center">${req}</td>
                <td>${defVal}</td>
                <td class="doc-cell-desc">${desc}</td>
            </tr>`;
        }
        html += `</tbody></table>`;
    } else {
        html += `<div class="doc-no-params">Chargement des paramètres depuis le registre...</div>`;
    }

    container.innerHTML = html;
    modal.style.display = 'flex';

    // Try to load param docs from backend WebSocket
    if (!doc.params && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'GET_PRIMITIVE_DOC', primitive: primitiveName }));
    }
}

function closePrimitiveDocModal() {
    const modal = document.getElementById('primitive-doc-modal');
    if (modal) modal.style.display = 'none';
}

function toggleCatalog() {
    const panel = document.getElementById('primitives-catalog');
    if (panel) {
        panel.classList.toggle('collapsed');
    }
}

function initPrimitivesCatalog() {
    const container = document.getElementById('primitives-list-container');
    if (!container) return;
    container.innerHTML = '';

    for (const [category, items] of Object.entries(primitiveCatalogData)) {
        const catDiv = document.createElement('div');
        catDiv.className = 'catalog-category';

        const titleDiv = document.createElement('div');
        titleDiv.className = 'catalog-category-title';
        titleDiv.innerHTML = `<span>${category}</span> <span class="cat-arrow">►</span>`;
        
        const itemsDiv = document.createElement('div');
        itemsDiv.className = 'catalog-category-items';
        itemsDiv.style.display = 'none';

        items.forEach(item => {
            const wrapper = document.createElement('div');
            wrapper.style.cssText = 'display:flex; align-items:center; gap:4px;';
            const btn = document.createElement('button');
            btn.className = 'catalog-item-btn';
            btn.style.flex = '1';
            btn.innerHTML = `<span>${item.label}</span> <span style="font-size:0.65rem; color:var(--accent); font-family:monospace; margin-left:8px;">${item.name}</span>`;
            btn.onclick = () => addPrimitiveNode(item.name, item.label, item.args);
            wrapper.appendChild(btn);
            const infoBtn = document.createElement('span');
            infoBtn.className = 'catalog-info-btn';
            infoBtn.title = "Voir la documentation";
            infoBtn.textContent = 'ℹ️';
            infoBtn.onclick = (e) => { e.stopPropagation(); showPrimitiveDoc(item.name); };
            wrapper.appendChild(infoBtn);
            itemsDiv.appendChild(wrapper);
        });

        titleDiv.onclick = () => {
            const collapsed = itemsDiv.style.display === 'none';
            itemsDiv.style.display = collapsed ? 'flex' : 'none';
            titleDiv.querySelector('.cat-arrow').innerText = collapsed ? '▼' : '►';
        };

        catDiv.appendChild(titleDiv);
        catDiv.appendChild(itemsDiv);
        container.appendChild(catDiv);
    }
}

function addPrimitiveNode(primitiveName, label, defaultArgs) {
    if (!currentRecipe) {
        currentRecipe = {
            recipe: "manual_flow",
            steps: [],
            env: { dev: {}, test: {}, prod: {} }
        };
    }
    if (!currentRecipe.steps) {
        currentRecipe.steps = [];
    }

    const steps = getCurrentStepList();
    
    let nextStepNum = 1;
    if (currentRecipe.steps.length > 0) {
        const getAllStepNums = (stepList) => {
            let nums = [];
            stepList.forEach(s => {
                nums.push(s.step);
                if (s.args && s.args.steps) {
                    nums = nums.concat(getAllStepNums(s.args.steps));
                }
            });
            return nums;
        };
        const allNums = getAllStepNums(currentRecipe.steps);
        nextStepNum = Math.max(...allNums) + 1;
    }

    const copiedArgs = JSON.parse(JSON.stringify(defaultArgs));

    const newStep = {
        step: nextStepNum,
        primitive: primitiveName,
        depends_on: [],
        args: copiedArgs,
        ui: {
            label: `${label} (${nextStepNum})`,
            position: {
                x: 150 + (steps.length % 3) * 100,
                y: 150 + Math.floor(steps.length / 3) * 100
            }
        }
    };

    steps.push(newStep);
    saveHistoryState();
    
    renderNodes(steps);
    addLog(`Nœud '${newStep.ui.label}' ajouté manuellement.`, 'success');
}

// ── Per-Workspace Notifications ──────────────────────────────
let _notifWsId = null;

async function openWorkspaceNotif(wsId) {
    _notifWsId = wsId;
    const modal = document.getElementById('ws-notif-modal');
    if (!modal) return;
    modal.style.display = 'flex';
    const workspaces = typeof localWorkspaces !== 'undefined' ? localWorkspaces : {};
    const name = workspaces[wsId]?.name || wsId;
    document.getElementById('ws-notif-workspace-name').textContent = 'Flux : ' + name;
    try {
        const r = await fetch(`/api/workspace/${wsId}/notif-config`);
        const c = await r.json();
        const set = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ''; };
        document.getElementById('ws-notif-enabled').checked = c.enabled === true || c.enabled === 'true';
        set('ws-notif-smtp-host', c.smtp_host);
        set('ws-notif-smtp-port', c.smtp_port);
        set('ws-notif-smtp-user', c.smtp_user);
        set('ws-notif-smtp-pass', c.smtp_pass);
        set('ws-notif-smtp-from', c.smtp_from);
        set('ws-notif-smtp-to', c.smtp_to);
        set('ws-notif-webhook-url', c.webhook_url);
    } catch (e) {
        addLog('Erreur chargement notification du flux.', 'error');
    }
}

function closeWorkspaceNotif() {
    document.getElementById('ws-notif-modal').style.display = 'none';
    _notifWsId = null;
}

async function saveWorkspaceNotif() {
    if (!_notifWsId) return;
    const config = {
        enabled: document.getElementById('ws-notif-enabled').checked,
        smtp_host: document.getElementById('ws-notif-smtp-host').value,
        smtp_port: document.getElementById('ws-notif-smtp-port').value,
        smtp_user: document.getElementById('ws-notif-smtp-user').value,
        smtp_pass: document.getElementById('ws-notif-smtp-pass').value,
        smtp_from: document.getElementById('ws-notif-smtp-from').value,
        smtp_to: document.getElementById('ws-notif-smtp-to').value,
        webhook_url: document.getElementById('ws-notif-webhook-url').value
    };
    try {
        const r = await fetch(`/api/workspace/${_notifWsId}/notif-config`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        const data = await r.json();
        if (data.ok) addLog('Notification du flux sauvegardée.', 'success');
        else addLog('Erreur: ' + (data.error || 'inconnue'), 'error');
    } catch (e) {
        addLog('Erreur réseau: ' + e.message, 'error');
    }
    closeWorkspaceNotif();
}

async function testWorkspaceNotif() {
    if (!_notifWsId) return;
    const config = {
        smtp_host: document.getElementById('ws-notif-smtp-host').value,
        smtp_port: document.getElementById('ws-notif-smtp-port').value,
        smtp_user: document.getElementById('ws-notif-smtp-user').value,
        smtp_pass: document.getElementById('ws-notif-smtp-pass').value,
        smtp_from: document.getElementById('ws-notif-smtp-from').value,
        smtp_to: document.getElementById('ws-notif-smtp-to').value,
        webhook_url: document.getElementById('ws-notif-webhook-url').value
    };
    try {
        const r = await fetch('/api/notif/test', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        if (!r.ok) { showToast('Erreur HTTP ' + r.status, 'error'); return; }
        const data = await r.json();
        const msg = 'Email: ' + (data.email || 'N/A') + ' | Webhook: ' + (data.webhook || 'N/A');
        addLog(msg, 'info');
        showToast(msg, data.email === 'OK' || data.webhook === 'OK' ? 'success' : 'warning');
    } catch (e) {
        showToast('Erreur: ' + e.message, 'error');
    }
}

// ── Fake Gen Editor ────────────────────────────────────────────
let _fakegenStepNum = null;
const FAKEGEN_TYPES = [
    { value: "id", label: "ID (auto-incrément)", fields: [{ key: "start", label: "Début", def: "1" }, { key: "step", label: "Pas", def: "1" }] },
    { value: "integer", label: "Entier", fields: [{ key: "min", label: "Min", def: "0" }, { key: "max", label: "Max", def: "99999" }] },
    { value: "float", label: "Décimal", fields: [{ key: "min", label: "Min", def: "0" }, { key: "max", label: "Max", def: "99999" }, { key: "decimals", label: "Décimales", def: "2" }] },
    { value: "boolean", label: "Booléen", fields: [] },
    { value: "date", label: "Date", fields: [{ key: "min", label: "Date min", def: "2020-01-01" }, { key: "max", label: "Date max", def: new Date().toISOString().split('T')[0] }, { key: "format", label: "Format", def: "%Y-%m-%d" }] },
    { value: "datetime", label: "Date+Heure", fields: [{ key: "min", label: "Min", def: "2020-01-01T00:00:00" }, { key: "max", label: "Max", def: new Date().toISOString().split('.')[0] }, { key: "format", label: "Format", def: "%Y-%m-%d %H:%M:%S" }] },
    { value: "time", label: "Heure", fields: [{ key: "minHour", label: "Heure min", def: "0" }, { key: "maxHour", label: "Heure max", def: "23" }, { key: "minMinute", label: "Minute min", def: "0" }, { key: "maxMinute", label: "Minute max", def: "59" }, { key: "format", label: "Format", def: "%H:%M:%S" }] },
    { value: "first_name", label: "Prénom", fields: [] },
    { value: "last_name", label: "Nom", fields: [] },
    { value: "full_name", label: "Nom complet", fields: [] },
    { value: "email", label: "Email", fields: [] },
    { value: "phone", label: "Téléphone", fields: [{ key: "prefix", label: "Préfixe", def: "" }] },
    { value: "country", label: "Pays", fields: [{ key: "format", label: "Format", def: "name" }] },
    { value: "city", label: "Ville", fields: [] },
    { value: "address", label: "Adresse", fields: [] },
    { value: "postal_code", label: "Code postal", fields: [{ key: "country", label: "Pays", def: "FR" }] },
    { value: "text", label: "Texte (lorem)", fields: [{ key: "minWords", label: "Mots min", def: "5" }, { key: "maxWords", label: "Mots max", def: "20" }] },
    { value: "pattern", label: "Pattern (#AaXx?)", fields: [{ key: "pattern", label: "Pattern", def: "###-AAA-###" }] },
];
FAKEGEN_TYPES.lookup = {}; FAKEGEN_TYPES.forEach(t => FAKEGEN_TYPES.lookup[t.value] = t);

function openFakeGenEditor(stepNum) {
    _fakegenStepNum = stepNum;
    const steps = getCurrentStepList();
    const step = steps.find(s => s.step === stepNum);
    if (!step) return;
    const args = step.args || {};
    document.getElementById('fakegen-count').value = args.count || '100';
    document.getElementById('fakegen-format').value = args.format || 'csv';
    renderFakeGenColumns(args.columns || '');
    document.getElementById('fakegen-modal').style.display = 'flex';
}

function closeFakeGenEditor() {
    document.getElementById('fakegen-modal').style.display = 'none';
    _fakegenStepNum = null;
}

function renderFakeGenColumns(columnsStr) {
    const container = document.getElementById('fakegen-columns-list');
    let cols = [];
    if (columnsStr) {
        try { cols = JSON.parse(columnsStr); } catch (e) {
            cols = columnsStr.split(',').filter(Boolean).map(p => {
                const parts = p.split(':');
                return { name: parts[0].trim(), type: (parts[1] || 'text').trim() };
            });
        }
    }
    if (cols.length === 0) {
        container.innerHTML = '<div style="color:var(--text-muted);font-style:italic;font-size:0.85rem;text-align:center;padding:20px;">Ajoutez des colonnes pour générer les données.</div>';
        return;
    }
    container.innerHTML = cols.map((col, idx) => renderFakeGenColumnRow(col, idx)).join('');
}

function renderFakeGenColumnRow(col, idx) {
    const typeDef = FAKEGEN_TYPES.lookup[col.type] || FAKEGEN_TYPES.lookup.text;
    const configFields = typeDef.fields.map(f => {
        const val = col[f.key] !== undefined ? col[f.key] : f.def;
        return `<div style="display:flex;align-items:center;gap:4px;">
            <label style="font-size:0.7rem;color:var(--text-muted);white-space:nowrap;">${f.label}</label>
            <input type="text" class="editor-input" id="fg-col-${idx}-${f.key}" value="${val}" oninput="onFakeGenColChange(${idx})" style="width:70px;padding:2px 4px;font-size:0.75rem;">
        </div>`;
    }).join('');

    return `<div class="aimapper-col-item" style="display:flex;align-items:center;gap:6px;padding:6px 8px;border:1px solid var(--border);border-radius:6px;flex-wrap:wrap;">
        <input type="text" class="editor-input" id="fg-col-${idx}-name" value="${col.name || ''}" placeholder="Nom" oninput="onFakeGenColChange(${idx})" style="width:100px;padding:2px 4px;font-size:0.8rem;">
        <select class="editor-input" id="fg-col-${idx}-type" onchange="onFakeGenColTypeChange(${idx})" style="width:140px;padding:2px 4px;font-size:0.75rem;">
            ${FAKEGEN_TYPES.map(t => `<option value="${t.value}"${t.value === col.type ? ' selected' : ''}>${t.label}</option>`).join('')}
        </select>
        ${configFields}
        <button class="toggle-logs-btn" onclick="removeFakeGenColumn(${idx})" style="padding:2px 6px;font-size:0.7rem;border-color:var(--error);color:var(--error);">✖</button>
    </div>`;
}

function onFakeGenColChange(idx) {
    // Re-render not needed, data is collected on apply
}

function onFakeGenColTypeChange(idx) {
    const colData = collectFakeGenCol(idx);
    const step = getCurrentStepList().find(s => s.step === _fakegenStepNum);
    if (!step) return;
    const args = step.args || {};
    const cols = parseFakeGenColumns(args.columns || '');
    while (cols.length <= idx) cols.push({ name: '', type: 'text' });
    cols[idx] = colData;
    args.columns = JSON.stringify(cols);
    saveNodeChanges();
    renderFakeGenColumns(args.columns);
}

function addFakeGenColumn() {
    const step = getCurrentStepList().find(s => s.step === _fakegenStepNum);
    if (!step) return;
    const args = step.args || {};
    const cols = parseFakeGenColumns(args.columns || '');
    cols.push({ name: 'colonne_' + (cols.length + 1), type: 'text' });
    args.columns = JSON.stringify(cols);
    saveNodeChanges();
    renderFakeGenColumns(args.columns);
}

function removeFakeGenColumn(idx) {
    const step = getCurrentStepList().find(s => s.step === _fakegenStepNum);
    if (!step) return;
    const args = step.args || {};
    const cols = parseFakeGenColumns(args.columns || '');
    cols.splice(idx, 1);
    args.columns = JSON.stringify(cols);
    saveNodeChanges();
    renderFakeGenColumns(args.columns);
}

function parseFakeGenColumns(str) {
    if (!str) return [];
    try { return JSON.parse(str); } catch (e) {
        return str.split(',').filter(Boolean).map(p => {
            const parts = p.split(':');
            return { name: parts[0].trim(), type: (parts[1] || 'text').trim() };
        });
    }
}

function collectFakeGenCol(idx) {
    const name = document.getElementById(`fg-col-${idx}-name`)?.value || '';
    const type = document.getElementById(`fg-col-${idx}-type`)?.value || 'text';
    const typeDef = FAKEGEN_TYPES.lookup[type] || FAKEGEN_TYPES.lookup.text;
    const col = { name, type };
    typeDef.fields.forEach(f => {
        const el = document.getElementById(`fg-col-${idx}-${f.key}`);
        if (el) col[f.key] = el.value;
    });
    return col;
}

function applyFakeGen() {
    const step = getCurrentStepList().find(s => s.step === _fakegenStepNum);
    if (!step) return;
    const container = document.getElementById('fakegen-columns-list');
    const rowEls = container.querySelectorAll('.aimapper-col-item');
    const cols = [];
    rowEls.forEach((_, idx) => cols.push(collectFakeGenCol(idx)));
    step.args = step.args || {};
    step.args.columns = JSON.stringify(cols);
    step.args.count = document.getElementById('fakegen-count').value || '100';
    step.args.format = document.getElementById('fakegen-format').value || 'csv';
    saveNodeChanges();
    addLog(`Générateur factice : ${cols.length} colonnes, ${step.args.count} lignes.`, 'success');
    closeFakeGenEditor();
}

window.addEventListener('DOMContentLoaded', () => {
    updateSettingsModelOptions();
    initPrimitivesCatalog();
    if (AUTH_TOKEN) {
        initWebSocket();
        ['admin-btn', 'admin-btn-header'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'inline-flex';
        });
    } else {
        checkAuthStatus();
    }
    
    // Canvas pan event listeners
    const wrapper = document.getElementById('canvas-wrapper');
    if (wrapper) {
        wrapper.addEventListener('mousedown', startCanvasPan);
        wrapper.addEventListener('mousemove', doCanvasPan);
        wrapper.addEventListener('mouseup', stopCanvasPan);
        wrapper.addEventListener('mouseleave', stopCanvasPan);
    }
    
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
    }
});