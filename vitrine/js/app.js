// [WFGY] Zone: SAFE | λ: 0.2 | Action: Handle WORKSPACE_CREATED in websocket onmessage loop



try {
    promptHistory = JSON.parse(localStorage.getItem('prompt_history')) || [];
} catch (e) {
    promptHistory = [];
}

let AUTH_TOKEN = localStorage.getItem('auth_token') || '';
let AUTH_MODE = 'login'; // 'login' | 'register'

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
        initWebSocket();
    } catch (e) {
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
    AUTH_MODE = 'login';
    if (ws) { ws.close(); }
    checkAuthStatus();
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
        { name: "net.notify", label: "Notification SMTP / Webhook", desc: "Envoie une alerte par email (SMTP) ou HTTP Webhook.", args: { type: "webhook", smtp_host: "localhost", smtp_port: "25", smtp_user: "", smtp_pass: "", to: "", subject: "ETL Alert", url: "", message: "" } },
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
        { name: "data.pivot", label: "Pivoter (format large)", desc: "Pivote une table du format long au format large (lignes en colonnes).", args: { source: "", destination: "", index: "", on: "", values: "", aggregate: "sum" } },
        { name: "data.unpivot", label: "Dépivoter (format long)", desc: "Dépivote une table du format large au format long (colonnes en lignes).", args: { source: "", destination: "", index: "", on: "", variable_name: "variable", value_name: "value" } },
        { name: "data.xml_transform", label: "Transformer XML (XSLT)", desc: "Applique une transformation XSLT sur un fichier XML source.", args: { source: "", stylesheet: "", destination: "" } }
    ],
    "Bases de Données": [
        { name: "db.query", label: "Requête SQL SELECT", desc: "Exécute une requête SQL SELECT et écrit le résultat dans un fichier.", args: { connection_string: "", query: "", destination: "" } },
        { name: "db.insert", label: "Insertion SQL", desc: "Importe un fichier CSV/JSON dans une table SQL (SQLite, Postgres, MySQL).", args: { connection_string: "", table_name: "", source: "", mode: "insert", schema_drift: false } },
        { name: "db.upsert", label: "Upsert SQL Idempotent", desc: "Insère ou met à jour des lignes dans une table SQL sur clés primaires.", args: { connection_string: "", table_name: "", source: "", keys: "", schema_drift: false } },
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
        { name: "core.switch", label: "Aiguillage Switch", desc: "Route l'exécution vers différents sous-graphes selon une valeur.", args: { value: "", cases: {} } }
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
    "net.http_request": { method: ["GET", "POST", "PUT", "DELETE", "PATCH"] }
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

window.addEventListener('DOMContentLoaded', () => {
    updateSettingsModelOptions();
    initPrimitivesCatalog();
    if (AUTH_TOKEN) {
        initWebSocket();
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