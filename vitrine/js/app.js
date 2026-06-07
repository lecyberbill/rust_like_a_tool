// [WFGY] Zone: SAFE | λ: 0.1 | Action: Extracted javascript application logic

let ws;
        let activeNodes = {};
        let currentRecipe = null;
        let activeEnv = 'dev';

        function addLog(message, type = 'info') {
            const logsDiv = document.getElementById('logs');
            const time = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerHTML = `<span class="log-time">[${time}]</span><span class="log-${type}">${message}</span>`;
            logsDiv.appendChild(entry);
            logsDiv.scrollTop = logsDiv.scrollHeight;
        }

        function toggleLogs() {
            const panel = document.getElementById('log-panel');
            panel.classList.toggle('collapsed');
        }

        function toggleEnv() {
            const panel = document.getElementById('env-panel');
            panel.classList.toggle('collapsed');
        }

        function changeActiveEnv() {
            activeEnv = document.getElementById('env-selector').value;
            document.getElementById('env-panel-title').innerText = `Secrets (${activeEnv.toUpperCase()})`;
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
                
                const mapBadge = primitive === 'data.clean' ? `<span class="node-edit-badge" title="AiMapper" style="background:rgba(0, 255, 102, 0.2); color:var(--success); border:1px solid rgba(0, 255, 102, 0.4);" onclick="event.stopPropagation(); openAiMapper(${step})">🗺️</span>` : '';
                this.innerHTML = `
                    <div class="node-input-handle" data-step="${step}"></div>
                    <div class="node-header">
                        <span>${label}</span>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            ${mapBadge}
                            <span class="node-edit-badge" title="Dupliquer" onclick="event.stopPropagation(); duplicateNode(${step})">📋</span>
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
                
                // Double click to enter nested workflow
                this.addEventListener('dblclick', () => {
                    const prim = this.getAttribute('primitive');
                    if (prim === 'core.sub_flow' || prim === 'core.loop') {
                        drillDown(Number(step), label);
                    }
                });

                // Clicking the node card itself only requests data preview (without opening the editor sidebar)
                this.addEventListener('click', () => {
                    requestDataPreview(Number(step));
                });

                // Drag & Drop logic
                let isDragging = false;
                let startX, startY;
                let initialLeft, initialTop;

                this.addEventListener('mousedown', (e) => {
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
                    
                    if (currentRecipe && ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            type: 'SAVE_WORKSPACE',
                            recipe: currentRecipe
                        }));
                    }
                };

                document.addEventListener('mousemove', onMouseMove);
                document.addEventListener('mouseup', onMouseUp);

                // Cleanup event listeners if element is removed from DOM
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

        function initWebSocket() {
            const wsHost = window.location.hostname || '127.0.0.1';
            ws = new WebSocket(`ws://${wsHost}:8765`);
            
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
                document.getElementById('conflict-modal').classList.remove('active');
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
                    saveHistoryState(); // Initial state capture
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
                    // Request fresh run history upon completion of execution
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({ type: 'GET_RUN_HISTORY' }));
                    }
                }
                else if (data.type === 'WORKSPACES_LIST') {
                    updateWorkspacesList(data.active_workspace, data.workspaces);
                }
                else if (data.type === 'WORKSPACE_EXECUTION_STATE') {
                    updateWorkspaceExecutionState(data.workspace_id, data.state);
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
                else if (data.type === 'DATA_PREVIEW_RESULT') {
                    const contentDiv = document.getElementById('data-preview-content');
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

        // --- HISTORIQUE DES RUNS & PERFORMANCE TELEMETRY RENDERING ---
        let currentRunHistory = [];
        let selectedRunId = null;

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

            // Auto-display performance metrics for the active selected run
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

            // Find the maximum step duration to determine relative width percentage
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
            container.innerHTML = '';
            
            if (!currentRecipe || !currentRecipe.steps) {
                container.innerHTML = '<div class="no-vars-msg">Aucun placeholder de secret détecté dans le flux courant.</div>';
                return;
            }

            // Set to hold unique placeholders detected
            const placeholders = new Set();
            
            // Regex to find placeholders like ${SECRET_NAME}
            const regex = /\${([^}]+)}/g;

            currentRecipe.steps.forEach(step => {
                if (step.args) {
                    Object.values(step.args).forEach(val => {
                        if (typeof val === 'string') {
                            let match;
                            // Reset regex lastIndex
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

            // Ensure hierarchical environment structure
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
                
                // Hide values visually if it is sensitive
                const isSensitive = varName.toLowerCase().includes('secret') || 
                                    varName.toLowerCase().includes('pass') || 
                                    varName.toLowerCase().includes('key') || 
                                    varName.toLowerCase().includes('token');
                
                input.type = isSensitive ? 'password' : 'text';
                input.placeholder = isSensitive ? `Saisir secret pour ${activeEnv.toUpperCase()}...` : `Saisir valeur pour ${activeEnv.toUpperCase()}...`;
                
                // Get value from current active environment sub-object
                input.value = currentRecipe.env[activeEnv][varName] || '';
                
                input.oninput = (e) => {
                    currentRecipe.env[activeEnv][varName] = e.target.value;
                };

                row.appendChild(label);
                row.appendChild(input);
                container.appendChild(row);
            });
        }

        function showConflictModal(step, message, options) {
            const modal = document.getElementById('conflict-modal');
            const messageEl = document.getElementById('conflict-message');
            const actionsEl = document.getElementById('conflict-actions');
            
            messageEl.innerText = message;
            actionsEl.innerHTML = '';
            
            options.forEach(opt => {
                const btn = document.createElement('button');
                btn.className = `modal-btn btn-${opt.value}`;
                btn.innerText = opt.label;
                btn.onclick = () => {
                    modal.classList.remove('active');
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            type: 'USER_CONFIRMATION_RESPONSE',
                            step: step,
                            choice: opt.value
                        }));
                        addLog(`Choix envoyé pour l'étape ${step} : ${opt.label}`, 'success');
                    }
                };
                actionsEl.appendChild(btn);
            });
            
            modal.classList.add('active');
        }

        // --- FONCTIONS D'EDITION VISUELLE DES NOEUDS & SECRETS GLOBAUX ---
        let selectedStepNum = null;

        function editNode(stepNum) {
            selectedStepNum = stepNum;
            const currentSteps = getCurrentStepList();
            const step = currentSteps.find(s => s.step === stepNum);
            if (!step) return;

            const panel = document.getElementById('node-editor-panel');
            const container = document.getElementById('node-editor-container');
            
            // Ouvrir l'éditeur de noeud
            panel.classList.remove('collapsed');
            
            // Titre de l'étape
            document.getElementById('node-editor-title').innerText = `Étape ${stepNum} : ${step.ui.label}`;
            
            // Construire le formulaire d'arguments et dépendances
            let html = `
                <div class="editor-section">
                    <div class="editor-section-title">Infos Générales</div>
                    <div class="editor-input-group">
                        <label>Nom convivial (Label)</label>
                        <input type="text" class="editor-input" id="edit-node-label" value="${step.ui.label}" oninput="saveNodeChanges()">
                    </div>
                </div>
            `;

            // Dépendances (Depends On)
            html += `
                <div class="editor-section">
                    <div class="editor-section-title">Dépendances (depends_on)</div>
                    <div style="display:flex; flex-direction:column; gap:6px;">
            `;
            
            currentSteps.forEach(otherStep => {
                if (otherStep.step !== stepNum) {
                    const isChecked = (step.depends_on || []).includes(otherStep.step) ? 'checked' : '';
                    html += `
                        <div class="editor-checkbox-group">
                            <input type="checkbox" id="dep-${otherStep.step}" ${isChecked} onchange="saveNodeChanges()">
                            <label for="dep-${otherStep.step}">Étape ${otherStep.step} : ${otherStep.ui.label}</label>
                        </div>
                    `;
                }
            });
            if (currentSteps.length <= 1) {
                html += `<div style="font-size:0.8rem; color:var(--text-muted); font-style:italic;">Aucune autre étape disponible pour créer une dépendance.</div>`;
            }
            html += `</div></div>`;

            // Arguments de la primitive
            html += `
                <div class="editor-section">
                    <div class="editor-section-title">Arguments (${step.primitive})</div>
            `;
            if (step.primitive === 'data.clean') {
                html += `
                    <button class="save-secrets-btn" style="background: linear-gradient(135deg, var(--success) 0%, rgba(0,255,102,0.6) 100%); color: #000; font-weight: 800; margin-bottom: 16px;" onclick="openAiMapper(${stepNum})">🗺️ Ouvrir AiMapper</button>
                `;
            }

            const args = step.args || {};
            for (const [key, val] of Object.entries(args)) {
                const inputId = `arg-${key}`;
                if (typeof val === 'boolean') {
                    const isChecked = val ? 'checked' : '';
                    html += `
                        <div class="editor-checkbox-group">
                            <input type="checkbox" id="${inputId}" ${isChecked} onchange="saveNodeChanges()">
                            <label for="${inputId}">${key}</label>
                        </div>
                    `;
                } else {
                    html += `
                        <div class="editor-input-group">
                            <label>${key}</label>
                            <input type="text" class="editor-input" id="${inputId}" value="${val}" oninput="saveNodeChanges()">
                        </div>
                    `;
                }
            }
            html += `</div>`;

            // Delete Step Button
            html += `
                <div class="editor-section" style="display:flex; justify-content:center; padding:16px 20px;">
                    <button class="save-secrets-btn" style="background:linear-gradient(135deg, var(--error) 0%, rgba(239,68,68,0.6) 100%); color:#fff; border:none; box-shadow: 0 4px 12px rgba(239,68,68,0.3); font-weight:800; width:100%;" onclick="deleteStepNode(${stepNum})">🗑️ Supprimer l'étape</button>
                </div>
            `;
            container.innerHTML = html;
        }

        function closeNodeEditor() {
            document.getElementById('node-editor-panel').classList.add('collapsed');
            selectedStepNum = null;
        }

        function saveNodeChanges() {
            if (selectedStepNum === null || !currentRecipe) return;
            const currentSteps = getCurrentStepList();
            const step = currentSteps.find(s => s.step === selectedStepNum);
            if (!step) return;
            saveHistoryState(); // Record parameter adjustments

            // 1. Mettre à jour le Label
            const labelInput = document.getElementById('edit-node-label');
            if (labelInput) {
                step.ui.label = labelInput.value;
                const nodeHeaderLabel = document.querySelector(`#node-step-${selectedStepNum} .node-header span:first-child`);
                if (nodeHeaderLabel) {
                    nodeHeaderLabel.innerText = labelInput.value;
                }
            }

            // 2. Mettre à jour les dépendances
            const deps = [];
            currentSteps.forEach(otherStep => {
                if (otherStep.step !== selectedStepNum) {
                    const chk = document.getElementById(`dep-${otherStep.step}`);
                    if (chk && chk.checked) {
                        deps.push(otherStep.step);
                    }
                }
            });
            step.depends_on = deps;

            // 3. Mettre à jour les arguments
            const args = step.args || {};
            for (const key of Object.keys(args)) {
                const inputId = `arg-${key}`;
                const el = document.getElementById(inputId);
                if (el) {
                    if (el.type === 'checkbox') {
                        step.args[key] = el.checked;
                    } else {
                        // Conserver les nombres ou types corrects si possible
                        const floatVal = parseFloat(el.value);
                        if (!isNaN(floatVal) && String(floatVal) === el.value) {
                            step.args[key] = floatVal;
                        } else if ((el.value === 'true' || el.value === 'false') && typeof step.args[key] === 'boolean') {
                            step.args[key] = el.value === 'true';
                        } else {
                            step.args[key] = el.value;
                        }
                    }
                }
            }

            // Redessiner les connexions
            drawConnections();
            
            // Mettre à jour l'affichage des variables s'il y a de nouveaux placeholders
            detectAndRenderEnvVars();
        }

        function saveGlobalSecrets() {
            if (!currentRecipe || !currentRecipe.env) {
                addLog('Aucun environnement de secrets chargé.', 'error');
                return;
            }
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'SAVE_GLOBAL_SECRETS',
                    secrets: currentRecipe.env
                }));
                addLog('Envoi de la sauvegarde des secrets globaux au coffre-fort...', 'info');
            } else {
                addLog('Déconnecté du serveur, impossible de sauvegarder.', 'error');
            }
        }

        // Nested Drill-down navigation state
        let currentNavPath = []; // Array of objects: { stepNum: number, label: string }

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

        // Global connection drawing state
        let isDrawingConnection = false;
        let connectionSourceStep = null;
        let tempLineSvg = null;

        function startDrawingConnection(stepNum, event) {
            isDrawingConnection = true;
            connectionSourceStep = stepNum;
            
            const svg = document.getElementById('connections-svg');
            
            // Create temporary dashed curve for active dragging
            tempLineSvg = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            tempLineSvg.setAttribute('class', 'connection-line temp');
            svg.appendChild(tempLineSvg);
            
            updateTempLine(event.clientX, event.clientY);
            
            document.addEventListener('mousemove', onMoveConnectionDrag);
            document.addEventListener('mouseup', onEndConnectionDrag);
        }

        function updateTempLine(clientX, clientY) {
            if (!tempLineSvg || connectionSourceStep === null) return;
            const nodeA = activeNodes[connectionSourceStep];
            if (!nodeA) return;
            
            const rectA = nodeA.getBoundingClientRect();
            const canvasRect = document.getElementById('canvas').getBoundingClientRect();
            
            const x1 = (rectA.left - canvasRect.left + rectA.width) / canvasZoom;
            const y1 = (rectA.top - canvasRect.top + rectA.height / 2) / canvasZoom;
            
            const x2 = (clientX - canvasRect.left) / canvasZoom;
            const y2 = (clientY - canvasRect.top) / canvasZoom;
            
            const controlX = x1 + (x2 - x1) / 2;
            tempLineSvg.setAttribute('d', `M ${x1} ${y1} C ${controlX} ${y1}, ${controlX} ${y2}, ${x2} ${y2}`);
        }

        function onMoveConnectionDrag(e) {
            if (isDrawingConnection) {
                updateTempLine(e.clientX, e.clientY);
            }
        }

        function onEndConnectionDrag(e) {
            document.removeEventListener('mousemove', onMoveConnectionDrag);
            document.removeEventListener('mouseup', onEndConnectionDrag);
            
            if (tempLineSvg) {
                tempLineSvg.remove();
                tempLineSvg = null;
            }
            
            isDrawingConnection = false;
            
            // Try to find if drop target is a node handle or a node card
            const targetEl = document.elementFromPoint(e.clientX, e.clientY);
            if (!targetEl) return;
            
            const inputHandle = targetEl.closest('.node-input-handle');
            const targetNode = targetEl.closest('workflow-node');
            
            let targetStep = null;
            if (inputHandle) {
                targetStep = Number(inputHandle.getAttribute('data-step'));
            } else if (targetNode) {
                targetStep = Number(targetNode.getAttribute('step'));
            }
            
            if (targetStep !== null && targetStep !== connectionSourceStep && !isNaN(targetStep)) {
                // Connect them! (targetStep depends on connectionSourceStep)
                const currentSteps = getCurrentStepList();
                const stepB = currentSteps.find(s => s.step === targetStep);
                if (stepB) {
                    if (!stepB.depends_on) stepB.depends_on = [];
                    if (!stepB.depends_on.includes(connectionSourceStep)) {
                        // Check for direct cycle
                        const stepA = currentSteps.find(s => s.step === connectionSourceStep);
                        if (stepA && stepA.depends_on && stepA.depends_on.includes(targetStep)) {
                            addLog("Boucle directe détectée ! Connexion rejetée.", "error");
                        } else {
                            // Test adding dependency with hasCycle
                            stepB.depends_on.push(connectionSourceStep);
                            if (hasCycle(currentSteps)) {
                                // Cycle detected! Rollback connection
                                stepB.depends_on.pop();
                                addLog("Boucle complexe/Cycle détecté ! Connexion rejetée pour conserver le graphe acyclique (DAG).", "error");
                            } else {
                                saveHistoryState(); // Record change
                                addLog(`Connexion créée : Étape ${targetStep} dépend de l'étape ${connectionSourceStep}`, "success");
                                
                                // Re-render and save
                                drawConnections();
                                saveActiveWorkspace();
                                
                                // If node editor is open for target step, update display
                                if (selectedStepNum === targetStep) {
                                    editNode(targetStep);
                                }
                            }
                        }
                    }
                }
            }
            
            connectionSourceStep = null;
        }

        function closeConnectionModal() {
            document.getElementById('connection-modal').style.display = 'none';
        }

        function selectConnection(parentNum, childNum) {
            const currentSteps = getCurrentStepList();
            const childStep = currentSteps.find(s => s.step === childNum);
            const parentStep = currentSteps.find(s => s.step === parentNum);
            if (!childStep || !parentStep) return;

            // Ensure visual storage exists
            if (!childStep.ui) childStep.ui = {};
            if (!childStep.ui.connection_labels) childStep.ui.connection_labels = {};
            
            const currentLabel = childStep.ui.connection_labels[parentNum] || "";
            
            const modal = document.getElementById('connection-modal');
            const desc = document.getElementById('connection-modal-desc');
            const labelInput = document.getElementById('connection-modal-label');
            const deleteBtn = document.getElementById('connection-modal-delete-btn');
            const saveBtn = document.getElementById('connection-modal-save-btn');
            
            desc.innerHTML = `Liaison reliant le nœud source <strong>${parentStep.ui.label}</strong> au nœud cible <strong>${childStep.ui.label}</strong>.`;
            labelInput.value = currentLabel;
            
            // Re-bind click events for this specific pair
            deleteBtn.onclick = () => {
                if (confirm(`Voulez-vous vraiment supprimer la liaison de [${parentStep.ui.label}] vers [${childStep.ui.label}] ?`)) {
                    childStep.depends_on = childStep.depends_on.filter(d => d !== parentNum);
                    if (childStep.ui.connection_labels[parentNum]) {
                        delete childStep.ui.connection_labels[parentNum];
                    }
                    addLog(`Liaison entre '${parentStep.ui.label}' et '${childStep.ui.label}' supprimée.`, 'warning');
                    drawConnections();
                    saveActiveWorkspace();
                    if (selectedStepNum === childNum) {
                        editNode(childNum);
                    }
                    closeConnectionModal();
                }
            };
            
            saveBtn.onclick = () => {
                const newLabel = labelInput.value.trim();
                childStep.ui.connection_labels[parentNum] = newLabel;
                addLog(`Liaison nommée : "${newLabel}"`, 'success');
                drawConnections();
                saveActiveWorkspace();
                closeConnectionModal();
            };
            
            modal.style.display = 'flex';
        }

        function drawConnections() {
            const svg = document.getElementById('connections-svg');
            svg.innerHTML = '';
            
            const currentSteps = getCurrentStepList();
            if (currentSteps.length === 0) return;
            
            currentSteps.forEach(step => {
                const stepNum = step.step;
                const nodeB = activeNodes[stepNum];
                if (!nodeB) return;
                
                const deps = step.depends_on || [];
                deps.forEach(parentNum => {
                    const nodeA = activeNodes[parentNum];
                    if (nodeA) {
                        const rectA = nodeA.getBoundingClientRect();
                        const rectB = nodeB.getBoundingClientRect();
                        const canvasRect = document.getElementById('canvas').getBoundingClientRect();
                        
                        const x1 = (rectA.left - canvasRect.left + rectA.width) / canvasZoom;
                        const y1 = (rectA.top - canvasRect.top + rectA.height / 2) / canvasZoom;
                        
                        const x2 = (rectB.left - canvasRect.left) / canvasZoom;
                        const y2 = (rectB.top - canvasRect.top + rectB.height / 2) / canvasZoom;
                        
                        const controlX = x1 + (x2 - x1) / 2;
                        const pathD = `M ${x1} ${y1} C ${controlX} ${y1}, ${controlX} ${y2}, ${x2} ${y2}`;
                        
                        // Create interactive overlay path (thicker transparent path for easy clicking)
                        const clickPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                        clickPath.setAttribute('d', pathD);
                        clickPath.setAttribute('fill', 'none');
                        clickPath.setAttribute('stroke', 'transparent');
                        clickPath.setAttribute('stroke-width', '16');
                        clickPath.setAttribute('cursor', 'pointer');
                        clickPath.style.pointerEvents = 'auto';
                        clickPath.addEventListener('click', (e) => {
                            e.stopPropagation();
                            selectConnection(parentNum, stepNum);
                        });
                        
                        // Create visual path
                        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                        path.setAttribute('d', pathD);
                        path.setAttribute('class', 'connection-line');
                        path.addEventListener('click', (e) => {
                            e.stopPropagation();
                            selectConnection(parentNum, stepNum);
                        });
                        
                        svg.appendChild(path);
                        svg.appendChild(clickPath);
                        
                        // Render label if present
                        const label = (step.ui && step.ui.connection_labels) ? step.ui.connection_labels[parentNum] : "";
                        if (label) {
                            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                            
                            // Estimate midpoint on cubic Bezier curve
                            const midX = (x1 + 3 * controlX + 3 * controlX + x2) / 8;
                            const midY = (y1 + 3 * y1 + 3 * y2 + y2) / 8;
                            
                            text.setAttribute('x', midX);
                            text.setAttribute('y', midY - 8); // Slightly offset vertically
                            text.setAttribute('text-anchor', 'middle');
                            text.setAttribute('class', 'connection-text');
                            text.style.pointerEvents = 'none';
                            text.textContent = label;
                            
                            svg.appendChild(text);
                        }
                    }
                });
            });
        }

        function renderNodes(steps) {
            const canvas = document.getElementById('canvas');
            canvas.innerHTML = ''; // Clear canvas
            activeNodes = {};

            const startX = 50;
            const startY = 80;
            const horizontalSpacing = 420; // Increased spacing to prevent default overlaps
            const verticalSpacing = 200;
            const maxPerRow = 3;

            steps.forEach((step, idx) => {
                const row = Math.floor(idx / maxPerRow);
                const col = idx % maxPerRow;
                
                let finalX = startX + col * horizontalSpacing;
                let finalY = startY + row * verticalSpacing;

                if (step.ui && step.ui.position && typeof step.ui.position.x === 'number') {
                    finalX = step.ui.position.x;
                    finalY = step.ui.position.y;
                } else {
                    if (!step.ui) step.ui = {};
                    step.ui.position = { x: finalX, y: finalY };
                }

                const node = document.createElement('workflow-node');
                node.setAttribute('step', step.step);
                node.setAttribute('label', step.ui.label);
                node.setAttribute('primitive', step.primitive);
                node.setAttribute('x', finalX);
                node.setAttribute('y', finalY);
                canvas.appendChild(node);
                activeNodes[step.step] = node;
            });
            
            // Draw connections after DOM rendering
            setTimeout(drawConnections, 50);
        }

        // Redraw connections on window resize
        window.addEventListener('resize', drawConnections);

        function updateNodeStatus(step, status) {
            const node = document.getElementById(`node-step-${step}`);
            if (node) {
                node.className = `node ${status}`;
            }
        }

        function triggerUpload() {
            document.getElementById('recipe-upload').click();
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

        function clearRecipe() {
            currentRecipe = null;
            document.getElementById('canvas').innerHTML = '';
            document.getElementById('connections-svg').innerHTML = '';
            document.getElementById('env-vars-container').innerHTML = '<div class="no-vars-msg">Aucun placeholder de secret détecté dans le flux courant.</div>';
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'CLEAR_RECIPE'
                }));
            }
            addLog('Workflow courant effacé.', 'info');
        }

        function runRecipe() {
            if (!currentRecipe || !currentRecipe.steps || currentRecipe.steps.length === 0) {
                addLog('Erreur : aucun workflow à exécuter.', 'error');
                return;
            }
            if (ws && ws.readyState === WebSocket.OPEN) {
                addLog(`Lancement de l'exécution sur l'environnement : ${activeEnv.toUpperCase()}...`, 'info');
                currentRecipe.steps.forEach(s => updateNodeStatus(s.step, 'pending'));
                
                ws.send(JSON.stringify({
                    type: 'RUN_RECIPE',
                    recipe: currentRecipe,
                    target_env: activeEnv
                }));
            } else {
                addLog('Erreur : déconnecté du serveur d\'orchestration.', 'error');
            }
        }

        // --- LOGIQUE CHAT MODE ÉTUDE ---
        let studyOriginalIntent = '';
        let studyChatHistory = [];

        function openStudyChat(originalIntent, analysis, questions) {
            studyOriginalIntent = originalIntent;
            studyChatHistory = []; // Reset history
            
            const modal = document.getElementById('study-chat-modal');
            const msgArea = document.getElementById('study-chat-messages');
            
            msgArea.innerHTML = '';
            modal.classList.add('active');
            
            // Add initial analysis bubble
            appendChatBubble('assistant', `<strong>Analyse de l'Intention :</strong><br>${analysis}`);
            
            // Add assistant questions bubble
            if (questions && questions.length > 0) {
                let qText = "<strong>Questions de clarification :</strong><br><ul>";
                questions.forEach(q => {
                    qText += `<li>${q}</li>`;
                });
                qText += "</ul>";
                appendChatBubble('assistant', qText);
                studyChatHistory.push({ role: 'assistant', content: `Analysis: ${analysis}. Questions: ${questions.join(' | ')}` });
            }
        }

        function appendChatBubble(sender, text) {
            const msgArea = document.getElementById('study-chat-messages');
            const bubble = document.createElement('div');
            bubble.className = `chat-bubble ${sender}`;
            bubble.innerHTML = text;
            msgArea.appendChild(bubble);
            msgArea.scrollTop = msgArea.scrollHeight;
        }

        function sendStudyChatReply() {
            const input = document.getElementById('study-chat-input');
            const text = input.value.trim();
            if (!text) return;
            
            appendChatBubble('user', text);
            studyChatHistory.push({ role: 'user', content: text });
            input.value = '';
            
            // Envoi au serveur pour obtenir de nouvelles clarifications
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'SUBMIT_STUDY_CHAT',
                    original_intent: studyOriginalIntent,
                    chat_history: studyChatHistory
                }));
            }
        }

        function generateStudyRecipe() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'GENERATE_STUDY_RECIPE',
                    original_intent: studyOriginalIntent,
                    chat_history: studyChatHistory
                }));
                closeStudyChat();
            }
        }

        function closeStudyChat() {
            document.getElementById('study-chat-modal').classList.remove('active');
        }

        function togglePromptDrawer() {
            const drawer = document.getElementById('prompt-drawer');
            drawer.classList.toggle('active');
            if (drawer.classList.contains('active')) {
                document.getElementById('intent-input').focus();
                // Close other drawers
                document.getElementById('settings-drawer').classList.remove('active');
            }
        }

        function toggleSettingsDrawer() {
            const drawer = document.getElementById('settings-drawer');
            drawer.classList.toggle('active');
            if (drawer.classList.contains('active')) {
                // Close other drawers
                document.getElementById('prompt-drawer').classList.remove('active');
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
            const provider = document.getElementById('setting-provider').value;
            const modelSelect = document.getElementById('setting-model');
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

        function saveSettings() {
            const provider = document.getElementById('setting-provider').value;
            const model = document.getElementById('setting-model').value;
            const baseUrl = document.getElementById('setting-base-url').value;

            addLog(`Application des réglages IA : Provider=${provider}, Model=${model}`, 'info');

            // Send config update request to the python server or store locally if server handled
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'UPDATE_LLM_SETTINGS',
                    provider: provider,
                    model: model,
                    base_url: baseUrl
                }));
            }
            
            toggleSettingsDrawer();
        }

        function changeEnvPod(env) {
            activeEnv = env;
            // Update active state in Env selector (both floats and panel)
            document.querySelectorAll('.env-pod-btn').forEach(btn => {
                btn.classList.toggle('active', btn.getAttribute('data-env') === env);
            });
            document.getElementById('env-panel-title').innerText = `Secrets (${env.toUpperCase()})`;
            addLog(`Environnement actif basculé sur : ${env.toUpperCase()}`, 'info');
            detectAndRenderEnvVars();
        }

        function submitIntent() {
            const input = document.getElementById('intent-input');
            const intent = input.value.trim();
            const isStudyMode = document.getElementById('study-mode-checkbox').checked;
            if (intent && ws && ws.readyState === WebSocket.OPEN) {
                addLog(`Soumission de l'intention (Mode Étude=${isStudyMode}) : "${intent.substring(0, 60)}..."`, 'info');
                
                savePromptToHistory(intent);
                
                ws.send(JSON.stringify({
                    type: 'SUBMIT_INTENT',
                    intent: intent,
                    study_mode: isStudyMode
                }));
                input.value = '';
                // Close prompt drawer after successful submission
                document.getElementById('prompt-drawer').classList.remove('active');
                document.getElementById('prompt-history-list').style.display = 'none';
            } else {
                addLog('Erreur : impossible d\'envoyer l\'intention (déconnecté ou vide).', 'error');
            }
        }

        // Send user intent on Enter keydown (prevent default to not insert newline, unless Shift is pressed)
        document.getElementById('intent-input').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitIntent();
            }
        });

        // Prompt history tracking logic
        let promptHistory = [];
        try {
            promptHistory = JSON.parse(localStorage.getItem('prompt_history')) || [];
        } catch (e) {
            promptHistory = [];
        }
        let historyIndex = -1;

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
            if (listDiv.style.display === 'none') {
                renderPromptHistory();
                listDiv.style.display = 'block';
            } else {
                listDiv.style.display = 'none';
            }
        }

        function renderPromptHistory() {
            const container = document.getElementById('prompt-history-list');
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
                    document.getElementById('intent-input').value = p;
                    container.style.display = 'none';
                });
                container.appendChild(item);
            });
        }

        // Bind ArrowUp/ArrowDown for quick history navigation when textarea is focused
        document.getElementById('intent-input').addEventListener('keydown', function(e) {
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

        // Add Enter key listener for study chat input
        document.getElementById('study-chat-input').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                sendStudyChatReply();
            }
        });

        // --- WORKSPACE & TRIGGER MANAGEMENT (WFGY CORE v3) ---
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
            document.getElementById('workshop-actions').style.display = tabName === 'workshop' ? 'flex' : 'none';
            document.getElementById('dashboard-actions').style.display = tabName === 'dashboard' ? 'flex' : 'none';
            
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

        function openCreateWorkspaceModal() {
            const name = prompt("Entrez le nom du nouveau flux de travail :");
            if (name && name.trim()) {
                ws.send(JSON.stringify({
                    type: 'CREATE_WORKSPACE',
                    name: name.trim()
                }));
            }
        }

        function renameWorkspace(id, currentName) {
            const newName = prompt(`Renommer le flux "${currentName}" en :`, currentName);
            if (newName && newName.trim() && newName !== currentName) {
                ws.send(JSON.stringify({
                    type: 'RENAME_WORKSPACE',
                    workspace_id: id,
                    new_name: newName.trim()
                }));
            }
        }

        function deleteWorkspace(id) {
            if (confirm("Êtes-vous sûr de supprimer ce flux ? Le fichier de recette sera également supprimé.")) {
                ws.send(JSON.stringify({
                    type: 'DELETE_WORKSPACE',
                    workspace_id: id
                }));
            }
        }

        function openWorkspace(id) {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'SELECT_WORKSPACE',
                    workspace_id: id
                }));
                switchTab('workshop');
            }
        }

        function saveActiveWorkspace() {
            if (ws && ws.readyState === WebSocket.OPEN && currentRecipe) {
                ws.send(JSON.stringify({
                    type: 'SAVE_WORKSPACE',
                    recipe: currentRecipe
                }));
            } else {
                addLog("Aucune recette active à enregistrer.", "error");
            }
        }

        function configureTrigger(id) {
            const w = localWorkspaces[id];
            if (!w) return;
            
            document.getElementById('trigger-workspace-id').value = id;
            
            const trig = w.trigger || { enabled: false, type: 'none' };
            document.getElementById('trigger-enabled').checked = trig.enabled || false;
            document.getElementById('trigger-type').value = trig.type || 'none';
            document.getElementById('trigger-cron-expr').value = trig.cron_expression || '*/5 * * * *';
            document.getElementById('trigger-event-dir').value = trig.watch_directory || 'test_results/inbox';
            document.getElementById('trigger-event-pattern').value = trig.pattern || '*.csv';
            
            const webhookUrl = `http://localhost:8766/trigger?workspace=${id}`;
            document.getElementById('trigger-webhook-url').value = webhookUrl;
            
            toggleTriggerInputs();
            
            document.getElementById('trigger-modal').style.display = 'flex';
        }

        function closeTriggerModal() {
            document.getElementById('trigger-modal').style.display = 'none';
        }

        function toggleTriggerInputs() {
            const type = document.getElementById('trigger-type').value;
            document.querySelectorAll('.trigger-fields').forEach(el => el.style.display = 'none');
            
            if (type === 'cron') {
                document.getElementById('trigger-cron-fields').style.display = 'block';
            } else if (type === 'event') {
                document.getElementById('trigger-event-fields').style.display = 'block';
            } else if (type === 'webhook') {
                document.getElementById('trigger-webhook-fields').style.display = 'block';
            }
        }

        function saveTriggerConfig() {
            const id = document.getElementById('trigger-workspace-id').value;
            const enabled = document.getElementById('trigger-enabled').checked;
            const type = document.getElementById('trigger-type').value;
            
            const trigger = {
                enabled: enabled,
                type: type
            };
            
            if (type === 'cron') {
                trigger.cron_expression = document.getElementById('trigger-cron-expr').value.trim();
            } else if (type === 'event') {
                trigger.watch_directory = document.getElementById('trigger-event-dir').value.trim();
                trigger.pattern = document.getElementById('trigger-event-pattern').value.trim();
            }
            
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'UPDATE_WORKSPACE_TRIGGER',
                    workspace_id: id,
                    trigger: trigger
                }));
            }
            
            closeTriggerModal();
        }

        function copyWebhookUrl() {
            const input = document.getElementById('trigger-webhook-url');
            input.select();
            input.setSelectionRange(0, 9999);
            navigator.clipboard.writeText(input.value);
            alert("URL Webhook copiée !");
        }

        // AiMapper implementation
        let mapperStepNum = null;
        let mapperSourceHeaders = [];
        let mapperRightSourceHeaders = [];
        let mapperMappings = [];
        let lastFocusedInput = null;

        function openAiMapper(stepNum) {
            mapperStepNum = stepNum;
            const step = currentRecipe.steps.find(s => s.step === stepNum);
            if (!step || step.primitive !== 'data.clean') return;

            // Open overlay modal
            const modal = document.getElementById('aimapper-modal');
            modal.style.display = 'flex';
            
            document.getElementById('aimapper-source-path').innerText = `Source : ${step.args.source || ''}`;
            
            // Set relation join inputs
            document.getElementById('aimapper-join-right-source').value = step.args.right_source || '';
            document.getElementById('aimapper-join-type').value = step.args.how_join || 'left';

            // Clear lists
            document.getElementById('aimapper-source-list').innerHTML = '<div style="color:var(--text-muted); font-style:italic; padding:10px;">Chargement...</div>';
            document.getElementById('aimapper-mapping-body').innerHTML = '';
            document.getElementById('aimapper-dest-list').innerHTML = '';

            // Load existing mappings
            if (step.ui && step.ui.mappings) {
                mapperMappings = JSON.parse(JSON.stringify(step.ui.mappings));
                mapperMappings.forEach(m => {
                    if (m.expression && !m.sourceCol) {
                        m.sourceCol = m.expression;
                    }
                });
            } else {
                mapperMappings = parseStepArgsToMappings(step);
            }

            // Load existing variables
            if (step.ui && step.ui.variables) {
                mapperVariables = JSON.parse(JSON.stringify(step.ui.variables));
            } else {
                mapperVariables = [];
            }
            renderLocalVariables();

            // Fetch schemas from backend
            mapperSourceHeaders = [];
            mapperRightSourceHeaders = [];

            if (ws && ws.readyState === WebSocket.OPEN) {
                if (step.args.source) {
                    ws.send(JSON.stringify({
                        type: 'GET_SCHEMA',
                        filepath: step.args.source
                    }));
                }
                if (step.args.right_source) {
                    ws.send(JSON.stringify({
                        type: 'GET_SCHEMA',
                        filepath: step.args.right_source
                    }));
                }
            } else {
                renderSourceColumns([]);
                renderMappingRows();
            }
        }

        function onJoinRightSourceChanged() {
            const filepath = document.getElementById('aimapper-join-right-source').value.trim();
            if (ws && ws.readyState === WebSocket.OPEN && filepath) {
                ws.send(JSON.stringify({
                    type: 'GET_SCHEMA',
                    filepath: filepath
                }));
            } else {
                mapperRightSourceHeaders = [];
                populateJoinKeys();
                filterSourceColumns();
            }
        }

        function populateJoinKeys() {
            const step = currentRecipe.steps.find(s => s.step === mapperStepNum);
            const leftKeySelect = document.getElementById('aimapper-join-left-key');
            const rightKeySelect = document.getElementById('aimapper-join-right-key');

            if (!leftKeySelect || !rightKeySelect) return;

            const selectedLeft = leftKeySelect.value || (step ? step.args.left_on : "") || "";
            const selectedRight = rightKeySelect.value || (step ? step.args.right_on : "") || "";

            leftKeySelect.innerHTML = '<option value="">Clé Gauche</option>';
            mapperSourceHeaders.forEach(h => {
                leftKeySelect.innerHTML += `<option value="${h}">${h}</option>`;
            });
            leftKeySelect.value = selectedLeft;

            rightKeySelect.innerHTML = '<option value="">Clé Droite</option>';
            mapperRightSourceHeaders.forEach(h => {
                rightKeySelect.innerHTML += `<option value="${h}">${h}</option>`;
            });
            rightKeySelect.value = selectedRight;
        }

        function parseStepArgsToMappings(step) {
            let mappings = [];
            let selectCols = (step.args.select_columns || "").split(",").map(s => s.trim()).filter(s => s);
            let renames = {};
            (step.args.rename_columns || "").split(",").forEach(part => {
                let idx = part.indexOf(":");
                if (idx !== -1) {
                    renames[part.substring(idx + 1).trim()] = part.substring(0, idx).trim();
                }
            });
            let derives = {};
            (step.args.derive_columns || "").split(",").forEach(part => {
                let idx = part.indexOf("=");
                if (idx !== -1) {
                    derives[part.substring(0, idx).trim()] = part.substring(idx + 1).trim();
                }
            });
            let fillnas = {};
            (step.args.fill_na || "").split(",").forEach(part => {
                let idx = part.indexOf(":");
                if (idx !== -1) {
                    fillnas[part.substring(0, idx).trim()] = part.substring(idx + 1).trim();
                }
            });

            selectCols.forEach(col => {
                let sourceCol = renames[col] || col;
                let expression = derives[col] || "";
                let defaultVal = fillnas[col] || "";
                mappings.push({
                    sourceCol: expression ? expression : sourceCol,
                    expression: expression,
                    destCol: col,
                    defaultVal: defaultVal
                });
            });
            return mappings;
        }

        function renderSourceColumns(headers, isRightTable = false) {
            if (isRightTable) {
                mapperRightSourceHeaders = headers || [];
            } else {
                mapperSourceHeaders = headers || [];
            }
            populateJoinKeys();
            filterSourceColumns();
        }

        function filterSourceColumns() {
            const search = document.getElementById('aimapper-search-source').value.toLowerCase();
            const container = document.getElementById('aimapper-source-list');
            container.innerHTML = '';

            if (mapperSourceHeaders.length === 0 && mapperRightSourceHeaders.length === 0 && mapperVariables.length === 0) {
                container.innerHTML = '<div style="color:var(--text-muted); font-style:italic; padding:10px;">Aucune colonne ou variable</div>';
                return;
            }

            // Primary source columns
            if (mapperSourceHeaders.length > 0) {
                const titleG = document.createElement('div');
                titleG.style.cssText = 'font-size:0.68rem; color:var(--accent); text-transform:uppercase; font-weight:800; padding:2px 4px;';
                titleG.innerText = 'Table A (Source)';
                container.appendChild(titleG);

                mapperSourceHeaders.forEach(header => {
                    if (search && !header.toLowerCase().includes(search)) return;

                    const div = document.createElement('div');
                    div.style.cssText = 'padding:4px 8px; background:rgba(255,255,255,0.03); border:1px solid var(--border); border-radius:6px; cursor:pointer; font-size:0.78rem; font-family:"Roboto Mono", monospace; display:flex; justify-content:space-between; align-items:center; transition:all 0.2s;';
                    div.className = 'aimapper-source-item';
                    div.dataset.header = header;
                    
                    div.innerHTML = `
                        <span>${header}</span>
                        <button class="toggle-logs-btn" style="padding:1px 4px; font-size:0.7rem; border-color:var(--accent); color:var(--accent);" onclick="event.stopPropagation(); quickMapSource('${header}')">➕</button>
                    `;

                    div.addEventListener('click', () => {
                        if (lastFocusedInput) {
                            const start = lastFocusedInput.selectionStart;
                            const end = lastFocusedInput.selectionEnd;
                            const text = lastFocusedInput.value;
                            lastFocusedInput.value = text.substring(0, start) + header + text.substring(end);
                            lastFocusedInput.focus();
                            const event = new Event('input', { bubbles: true });
                            lastFocusedInput.dispatchEvent(event);
                        } else {
                            quickMapSource(header);
                        }
                    });

                    container.appendChild(div);
                });
            }

            // Secondary (right) source columns
            if (mapperRightSourceHeaders.length > 0) {
                const titleD = document.createElement('div');
                titleD.style.cssText = 'font-size:0.68rem; color:var(--running); text-transform:uppercase; font-weight:800; padding:2px 4px; margin-top:6px; border-top:1px solid var(--border);';
                titleD.innerText = 'Table B (Jointure)';
                container.appendChild(titleD);

                mapperRightSourceHeaders.forEach(header => {
                    if (search && !header.toLowerCase().includes(search)) return;

                    const div = document.createElement('div');
                    div.style.cssText = 'padding:4px 8px; background:rgba(0,240,255,0.02); border:1px solid rgba(0,240,255,0.1); border-radius:6px; cursor:pointer; font-size:0.78rem; font-family:"Roboto Mono", monospace; display:flex; justify-content:space-between; align-items:center; transition:all 0.2s;';
                    div.className = 'aimapper-source-item';
                    div.dataset.header = header;
                    
                    div.innerHTML = `
                        <span>${header}</span>
                        <button class="toggle-logs-btn" style="padding:1px 4px; font-size:0.7rem; border-color:var(--running); color:var(--running);" onclick="event.stopPropagation(); quickMapSource('${header}')">➕</button>
                    `;

                    div.addEventListener('click', () => {
                        if (lastFocusedInput) {
                            const start = lastFocusedInput.selectionStart;
                            const end = lastFocusedInput.selectionEnd;
                            const text = lastFocusedInput.value;
                            lastFocusedInput.value = text.substring(0, start) + header + text.substring(end);
                            lastFocusedInput.focus();
                            const event = new Event('input', { bubbles: true });
                            lastFocusedInput.dispatchEvent(event);
                        } else {
                            quickMapSource(header);
                        }
                    });

                    container.appendChild(div);
                });
            }

            // Append variables to source items for quick insertion
            if (mapperVariables.length > 0) {
                const sep = document.createElement('div');
                sep.style.cssText = 'font-size:0.7rem; color:#c084fc; text-transform:uppercase; font-weight:800; padding:4px 4px; border-top:1px solid var(--border); margin-top:6px;';
                sep.innerText = 'Variables';
                container.appendChild(sep);

                mapperVariables.forEach(v => {
                    if (!v.name || !v.name.trim()) return;
                    if (search && !v.name.toLowerCase().includes(search)) return;

                    const div = document.createElement('div');
                    div.style.cssText = 'padding:4px 8px; background:rgba(192, 132, 252, 0.05); border:1px solid rgba(192, 132, 252, 0.2); border-radius:6px; cursor:pointer; font-size:0.75rem; font-family:"Roboto Mono", monospace; color:#c084fc; display:flex; justify-content:space-between; align-items:center; transition:all 0.2s;';
                    div.innerHTML = `<span>${v.name}</span>`;

                    div.addEventListener('click', () => {
                        if (lastFocusedInput) {
                            const start = lastFocusedInput.selectionStart;
                            const end = lastFocusedInput.selectionEnd;
                            const text = lastFocusedInput.value;
                            lastFocusedInput.value = text.substring(0, start) + v.name + text.substring(end);
                            lastFocusedInput.focus();
                            const event = new Event('input', { bubbles: true });
                            lastFocusedInput.dispatchEvent(event);
                        }
                    });
                    container.appendChild(div);
                });
            }
        }

        function quickMapSource(header) {
            if (mapperMappings.some(m => m.sourceCol === header)) {
                return;
            }
            mapperMappings.push({
                sourceCol: header,
                destCol: header,
                defaultVal: ''
            });
            renderMappingRows();
        }

        function populateDatalist() {
            let dl = document.getElementById('aimapper-source-datalist');
            if (!dl) {
                dl = document.createElement('datalist');
                dl.id = 'aimapper-source-datalist';
                document.body.appendChild(dl);
            }
            let html = '';
            mapperSourceHeaders.forEach(h => {
                html += `<option value="${h}"></option>`;
            });
            mapperRightSourceHeaders.forEach(h => {
                html += `<option value="${h}"></option>`;
            });
            mapperVariables.forEach(v => {
                if (v.name) {
                    html += `<option value="${v.name}"></option>`;
                }
            });
            dl.innerHTML = html;
        }

        function renderMappingRows() {
            const tbody = document.getElementById('aimapper-mapping-body');
            tbody.innerHTML = '';

            if (mapperMappings.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--text-muted); font-style:italic; padding:20px;">Aucun mappage configuré. Cliquez sur une colonne source ou sur "Ajouter Colonne" pour commencer.</td></tr>';
                renderDestList();
                return;
            }

            populateDatalist();

            mapperMappings.forEach((m, idx) => {
                const tr = document.createElement('tr');
                tr.className = 'aimapper-row';
                tr.style.borderBottom = '1px solid var(--border)';

                tr.innerHTML = `
                    <td style="padding:4px;">
                        <div style="display:flex; gap:4px; align-items:center;">
                            <input type="text" list="aimapper-source-datalist" class="editor-input aimapper-source-input" style="flex:1; font-family:'Roboto Mono', monospace; font-size:0.78rem; padding:3px 6px; height:26px; border-radius:4px;" value="${m.sourceCol || ''}" placeholder="Sélectionner ou saisir une formule..." onfocus="lastFocusedInput = this" oninput="updateMappingField(${idx}, 'sourceCol', this.value)">
                            <button class="toggle-logs-btn" style="padding:3px 6px; height:26px; font-size:0.72rem; border-color:var(--accent); color:var(--accent);" title="Ouvrir l'éditeur de formule" onclick="openFormulaEditor(${idx})">ƒx</button>
                        </div>
                    </td>
                    <td style="padding:4px;">
                        <input type="text" class="editor-input aimapper-dest-input" style="width:100%; font-family:'Roboto Mono', monospace; font-size:0.78rem; padding:3px 6px; height:26px; border-radius:4px;" value="${m.destCol || ''}" placeholder="Nom colonne de sortie" oninput="updateMappingField(${idx}, 'destCol', this.value)">
                    </td>
                    <td style="padding:4px;">
                        <input type="text" class="editor-input aimapper-default-input" style="width:100%; font-family:'Roboto Mono', monospace; font-size:0.78rem; padding:3px 6px; height:26px; border-radius:4px;" value="${m.defaultVal || ''}" placeholder="Valeur si vide" oninput="updateMappingField(${idx}, 'defaultVal', this.value)">
                    </td>
                    <td style="padding:4px; text-align:center;">
                        <button class="toggle-logs-btn" style="padding:2px 6px; font-size:0.75rem; border-color:var(--error); color:var(--error); background:rgba(239,68,68,0.05);" onclick="deleteMappingRow(${idx})">🗑️</button>
                    </td>
                `;

                tbody.appendChild(tr);
            });

            renderDestList();
        }

        function updateMappingField(idx, field, value) {
            if (mapperMappings[idx]) {
                mapperMappings[idx][field] = value;
                if (field === 'sourceCol' && value) {
                    const isFormula = !mapperSourceHeaders.includes(value) || value.includes(" ") || value.includes("*") || value.includes("+") || value.includes("-") || value.includes("/") || value.includes("IF");
                    if (!isFormula && !mapperMappings[idx].destCol) {
                        mapperMappings[idx].destCol = value;
                        const destInput = document.querySelectorAll('.aimapper-dest-input')[idx];
                        if (destInput) destInput.value = value;
                    }
                }
                renderDestList();
            }
        }

        function deleteMappingRow(idx) {
            mapperMappings.splice(idx, 1);
            renderMappingRows();
        }

        function addMappingRow() {
            mapperMappings.push({
                sourceCol: '',
                destCol: '',
                defaultVal: ''
            });
            renderMappingRows();
        }

        function renderDestList() {
            const container = document.getElementById('aimapper-dest-list');
            container.innerHTML = '';

            const uniqueDests = new Set();
            mapperMappings.forEach(m => {
                if (m.destCol && m.destCol.trim()) {
                    uniqueDests.add(m.destCol.trim());
                }
            });

            if (uniqueDests.size === 0) {
                container.innerHTML = '<div style="color:var(--text-muted); font-style:italic; padding:10px;">Aucune colonne de sortie</div>';
                return;
            }

            uniqueDests.forEach(col => {
                const div = document.createElement('div');
                div.style.cssText = 'padding:5px 8px; background:rgba(0, 255, 102, 0.03); border:1px solid rgba(0, 255, 102, 0.15); border-radius:6px; font-size:0.78rem; font-family:"Roboto Mono", monospace; color:var(--success);';
                div.innerText = col;
                container.appendChild(div);
            });
        }

        let activeFormulaRowIdx = null;

        function openFormulaEditor(idx) {
            activeFormulaRowIdx = idx;
            const m = mapperMappings[idx];
            if (!m) return;

            const modal = document.getElementById('aimapper-formula-modal');
            modal.style.display = 'flex';

            document.getElementById('formula-editor-textarea').value = m.sourceCol || '';

            // Populate source columns and variables in helper list
            const container = document.getElementById('formula-editor-fields');
            container.innerHTML = '';

            mapperSourceHeaders.forEach(header => {
                const btn = document.createElement('div');
                btn.style.cssText = 'padding:4px 8px; background:rgba(255,255,255,0.02); border:1px solid var(--border); border-radius:4px; cursor:pointer; font-size:0.75rem; font-family:monospace; display:flex; justify-content:space-between; align-items:center; transition: background 0.2s;';
                btn.innerHTML = `<span>${header}</span> <span style="font-size:0.65rem; color:var(--accent);">colonne A</span>`;
                btn.onclick = () => insertTextAtCursor(header);
                btn.onmouseenter = () => btn.style.background = 'rgba(0, 240, 255, 0.05)';
                btn.onmouseleave = () => btn.style.background = 'rgba(255,255,255,0.02)';
                container.appendChild(btn);
            });

            mapperRightSourceHeaders.forEach(header => {
                const btn = document.createElement('div');
                btn.style.cssText = 'padding:4px 8px; background:rgba(0, 240, 255, 0.02); border:1px solid rgba(0, 240, 255, 0.1); border-radius:4px; cursor:pointer; font-size:0.75rem; font-family:monospace; display:flex; justify-content:space-between; align-items:center; transition: background 0.2s;';
                btn.innerHTML = `<span>${header}</span> <span style="font-size:0.65rem; color:var(--running);">colonne B</span>`;
                btn.onclick = () => insertTextAtCursor(header);
                btn.onmouseenter = () => btn.style.background = 'rgba(0, 240, 255, 0.1)';
                btn.onmouseleave = () => btn.style.background = 'rgba(0, 240, 255, 0.02)';
                container.appendChild(btn);
            });

            mapperVariables.forEach(v => {
                if (!v.name) return;
                const btn = document.createElement('div');
                btn.style.cssText = 'padding:4px 8px; background:rgba(192, 132, 252, 0.05); border:1px solid rgba(192, 132, 252, 0.2); border-radius:4px; cursor:pointer; font-size:0.75rem; font-family:monospace; color:#c084fc; display:flex; justify-content:space-between; align-items:center; transition: background 0.2s;';
                btn.innerHTML = `<span>${v.name}</span> <span style="font-size:0.65rem; color:#c084fc;">variable</span>`;
                btn.onclick = () => insertTextAtCursor(v.name);
                btn.onmouseenter = () => btn.style.background = 'rgba(192, 132, 252, 0.1)';
                btn.onmouseleave = () => btn.style.background = 'rgba(192, 132, 252, 0.05)';
                container.appendChild(btn);
            });

            const sysVars = [
                { name: '${CURRENT_YEAR}', desc: 'Année courante (ex: 2026)' },
                { name: '${TODAY}', desc: 'Date du jour (YYYY-MM-DD)' },
                { name: '${NOW}', desc: 'Date et heure (YYYY-MM-DD HH:MM:SS)' },
                { name: '${HOSTNAME}', desc: 'Nom de la machine' },
                { name: '${USERNAME}', desc: 'Utilisateur système' },
                { name: '${OS_NAME}', desc: 'Système d\'exploitation (windows/linux)' }
            ];

            sysVars.forEach(v => {
                const btn = document.createElement('div');
                btn.style.cssText = 'padding:4px 8px; background:rgba(0, 240, 255, 0.05); border:1px solid rgba(0, 240, 255, 0.2); border-radius:4px; cursor:pointer; font-size:0.75rem; font-family:monospace; color:#00f0ff; display:flex; justify-content:space-between; align-items:center; transition: background 0.2s;';
                btn.innerHTML = `<span>${v.name}</span> <span style="font-size:0.65rem; color:#00f0ff;" title="${v.desc}">système</span>`;
                btn.onclick = () => insertTextAtCursor(v.name);
                btn.onmouseenter = () => btn.style.background = 'rgba(0, 240, 255, 0.15)';
                btn.onmouseleave = () => btn.style.background = 'rgba(0, 240, 255, 0.05)';
                container.appendChild(btn);
            });
        }

        function closeFormulaEditor() {
            document.getElementById('aimapper-formula-modal').style.display = 'none';
            activeFormulaRowIdx = null;
        }

        function applyFormulaEditor() {
            if (activeFormulaRowIdx === null) return;
            const formula = document.getElementById('formula-editor-textarea').value;
            
            updateMappingField(activeFormulaRowIdx, 'sourceCol', formula);
            
            // Sync UI input field
            const sourceInputs = document.querySelectorAll('.aimapper-source-input');
            if (sourceInputs[activeFormulaRowIdx]) {
                sourceInputs[activeFormulaRowIdx].value = formula;
            }

            closeFormulaEditor();
        }

        function insertTextAtCursor(text) {
            const textarea = document.getElementById('formula-editor-textarea');
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            const currentVal = textarea.value;
            textarea.value = currentVal.substring(0, start) + text + currentVal.substring(end);
            textarea.focus();
            textarea.selectionStart = textarea.selectionEnd = start + text.length;
        }

        function setFormulaText(text) {
            document.getElementById('formula-editor-textarea').value = text;
            document.getElementById('formula-editor-textarea').focus();
        }

        function closeAiMapper() {
            document.getElementById('aimapper-modal').style.display = 'none';
            mapperStepNum = null;
            lastFocusedInput = null;
        }

        function applyAiMapper() {
            if (mapperStepNum === null || !currentRecipe) return;

            const invalid = mapperMappings.some(m => !m.destCol || !m.destCol.trim());
            if (invalid) {
                alert("Erreur : Veuillez spécifier un nom de colonne de sortie pour chaque ligne de mappage.");
                return;
            }

            serializeMappingsToStepArgs(mapperStepNum, mapperMappings, mapperVariables);
            
            if (selectedStepNum === mapperStepNum) {
                editNode(mapperStepNum);
            }
            
            addLog(`Mappage AiMapper appliqué pour l'étape ${mapperStepNum}`, 'success');
            closeAiMapper();
        }

        function serializeMappingsToStepArgs(stepNum, mappings, variables) {
            const step = currentRecipe.steps.find(s => s.step === stepNum);
            if (!step) return;

            if (!step.ui) step.ui = {};
            step.ui.mappings = mappings;
            step.ui.variables = variables;

            // Serialize join arguments
            const rightSource = document.getElementById('aimapper-join-right-source').value.trim();
            const joinType = document.getElementById('aimapper-join-type').value;
            const leftOn = document.getElementById('aimapper-join-left-key').value;
            const rightOn = document.getElementById('aimapper-join-right-key').value;

            if (rightSource) {
                step.args.right_source = rightSource;
                step.args.how_join = joinType;
                step.args.left_on = leftOn;
                step.args.right_on = rightOn;
            } else {
                delete step.args.right_source;
                delete step.args.how_join;
                delete step.args.left_on;
                delete step.args.right_on;
            }

            let selectCols = [];
            let renameCols = [];
            let deriveCols = [];
            let fillnaCols = [];

            mappings.forEach(m => {
                if (!m.destCol) return;
                selectCols.push(m.destCol);
                
                let val = m.sourceCol || "";
                let isKnownHeader = mapperSourceHeaders.includes(val) || mapperRightSourceHeaders.includes(val);
                let isFormula = val && (!isKnownHeader || val.includes(" ") || val.includes("*") || val.includes("+") || val.includes("-") || val.includes("/") || val.includes("IF") || val.includes("<") || val.includes(">") || val.includes("="));
                
                if (isFormula) {
                    let expr = val;
                    variables.forEach(v => {
                        if (v.name && v.name.trim()) {
                            let regex = new RegExp('\\b' + v.name.trim() + '\\b', 'g');
                            expr = expr.replace(regex, v.value);
                        }
                    });
                    deriveCols.push(`${m.destCol}=${expr}`);
                } else if (val && val !== m.destCol) {
                    renameCols.push(`${val}:${m.destCol}`);
                }
                if (m.defaultVal) {
                    fillnaCols.push(`${m.destCol}:${m.defaultVal}`);
                }
            });

            step.args.select_columns = selectCols.join(",");
            step.args.rename_columns = renameCols.join(",");
            step.args.derive_columns = deriveCols.join(",");
            step.args.fill_na = fillnaCols.join(",");

            saveActiveWorkspace();
        }

        // Local Variables implementation
        let mapperVariables = [];

        function addLocalVariable() {
            mapperVariables.push({
                name: 'var_' + (mapperVariables.length + 1),
                value: ''
            });
            renderLocalVariables();
            filterSourceColumns();
        }

        function deleteLocalVariable(idx) {
            mapperVariables.splice(idx, 1);
            renderLocalVariables();
            filterSourceColumns();
        }

        function updateLocalVariable(idx, field, value) {
            if (mapperVariables[idx]) {
                mapperVariables[idx][field] = value;
                if (field === 'name') {
                    filterSourceColumns();
                }
            }
        }

        function renderLocalVariables() {
            const container = document.getElementById('aimapper-variables-list');
            container.innerHTML = '';

            if (mapperVariables.length === 0) {
                container.innerHTML = '<div style="color:var(--text-muted); font-style:italic; padding:10px; font-size:0.8rem;">Aucune variable locale</div>';
                return;
            }

            mapperVariables.forEach((v, idx) => {
                const div = document.createElement('div');
                div.style.cssText = 'display:flex; gap:4px; align-items:center;';
                
                div.innerHTML = `
                    <input type="text" class="editor-input" style="flex:1; font-family:monospace; font-size:0.75rem; padding:4px 6px; border-color:rgba(192, 132, 252, 0.3);" value="${v.name}" placeholder="Nom" oninput="updateLocalVariable(${idx}, 'name', this.value)">
                    <span style="color:var(--text-muted); font-size:0.75rem;">=</span>
                    <input type="text" class="editor-input" style="flex:1.2; font-family:monospace; font-size:0.75rem; padding:4px 6px;" value="${v.value}" placeholder="Valeur" oninput="updateLocalVariable(${idx}, 'value', this.value)">
                    <button class="toggle-logs-btn" style="padding:2px 6px; border-color:var(--error); color:var(--error); background:rgba(239,68,68,0.05);" onclick="deleteLocalVariable(${idx})">🗑️</button>
                `;
                
                container.appendChild(div);
            });
        }

        // Theme management
        function toggleTheme() {
            const isLight = document.body.classList.toggle('light-theme');
            localStorage.setItem('theme', isLight ? 'light' : 'dark');
            addLog(`Thème basculé sur : ${isLight ? 'Clair (Moderne Noir & Blanc)' : 'Sombre'}`, 'info');
            drawConnections(); // Redraw paths to match colors if needed
        }

        // Canvas Zoom management
        let canvasZoom = 1;
        function updateCanvasZoom() {
            const canvas = document.getElementById('canvas');
            if (canvas) {
                canvas.style.transform = `scale(${canvasZoom})`;
                canvas.style.transformOrigin = 'top left';
                // Adjust SVG connections thickness if needed
                const svg = document.getElementById('connections-svg');
                // Adjust zoom text in DOM
                const zoomValText = document.getElementById('zoom-level-val');
                if (zoomValText) {
                    zoomValText.innerText = `${Math.round(canvasZoom * 100)}%`;
                }
                drawConnections();
            }
        }

        function zoomIn() {
            if (canvasZoom < 2.0) {
                canvasZoom += 0.1;
                updateCanvasZoom();
            }
        }

        function zoomOut() {
            if (canvasZoom > 0.5) {
                canvasZoom -= 0.1;
                updateCanvasZoom();
            }
        }

        function zoomReset() {
            canvasZoom = 1.0;
            updateCanvasZoom();
        }

        // Initialize on load
        window.addEventListener('DOMContentLoaded', () => {
            initWebSocket();
            updateSettingsModelOptions();
            initPrimitivesCatalog();
            
            // Restore theme preference
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme === 'light') {
                document.body.classList.add('light-theme');
            }
        });

        // Data Preview Functions
        function requestDataPreview(stepNum) {
            if (!currentRecipe || !currentRecipe.steps) return;
            const step = currentRecipe.steps.find(s => s.step === stepNum);
            if (!step) return;

            let filepath = '';
            const args = step.args || {};
            if (args.destination) {
                filepath = args.destination;
            } else if (args.local_path) {
                filepath = args.local_path;
            } else if (args.file_path) {
                filepath = args.file_path;
            } else if (args.path) {
                filepath = args.path;
            } else if (args.source) {
                filepath = args.source;
            }

            if (!filepath) {
                document.getElementById('data-preview-filepath').innerText = "Aucun fichier associé à cette étape";
                document.getElementById('data-preview-content').innerHTML = `
                    <div style="color: var(--text-muted); font-style: italic; text-align: center; padding: 15px; font-size: 0.85rem;">
                        L'étape "${step.ui.label}" (${step.primitive}) n'a pas de fichier de données associé.
                    </div>
                `;
                document.getElementById('data-preview-panel').classList.remove('collapsed');
                return;
            }

            // Resolve env placeholders
            let resolvedPath = filepath;
            const regex = /\${([^}]+)}/g;
            let match;
            regex.lastIndex = 0;
            while ((match = regex.exec(filepath)) !== null) {
                const varName = match[1];
                let val = null;
                if (currentRecipe.env && currentRecipe.env[activeEnv]) {
                    val = currentRecipe.env[activeEnv][varName];
                }
                if (val === null || val === undefined) {
                    val = '';
                }
                resolvedPath = resolvedPath.replace(`\${${varName}}`, val);
            }

            document.getElementById('data-preview-filepath').innerText = resolvedPath;
            document.getElementById('data-preview-content').innerHTML = `
                <div style="color: var(--accent); font-style: italic; text-align: center; padding: 15px; font-size: 0.85rem; display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <span style="width:12px; height:12px; border:2px solid var(--accent); border-top-color:transparent; border-radius:50%; display:inline-block; animation:spin 1s linear infinite;"></span>
                    Chargement de l'aperçu...
                </div>
            `;
            
            document.getElementById('data-preview-panel').classList.remove('collapsed');

            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'GET_DATA_PREVIEW',
                    filepath: resolvedPath
                }));
            }
        }

        function closeDataPreview() {
            document.getElementById('data-preview-panel').classList.add('collapsed');
        }

        // --- MANUEL INTERACTIVE EDITING & CATALOG ---
        const primitiveCatalogData = {
            "I/O (Fichiers)": [
                { name: "io.copy", label: "Copier des fichiers", args: { source: "", destination: "", overwrite: true } },
                { name: "io.move", label: "Déplacer des fichiers", args: { source: "", destination: "", overwrite: true } },
                { name: "io.delete", label: "Supprimer des fichiers", args: { path: "", secure_retention: true } },
                { name: "io.metadata", label: "Obtenir les métadonnées", args: { path: "", destination: "" } },
                { name: "io.write_file", label: "Écrire un fichier", args: { content: "", destination: "" } }
            ],
            "Réseau & Services": [
                { name: "net.download", label: "Télécharger par HTTP", args: { url: "", destination: "" } },
                { name: "net.upload", label: "Téléverser par HTTP", args: { file_path: "", url: "", method: "POST", headers: "" } },
                { name: "net.ftp_download", label: "Télécharger FTP", args: { host: "", port: "21", user: "", password: "", remote_path: "", local_path: "" } },
                { name: "net.ftp_upload", label: "Téléverser FTP", args: { host: "", port: "21", user: "", password: "", remote_path: "", local_path: "" } },
                { name: "net.sftp_download", label: "Télécharger SFTP", args: { host: "", port: "22", user: "", password: "", key_path: "", key_passphrase: "", remote_path: "", local_path: "" } },
                { name: "net.sftp_upload", label: "Téléverser SFTP", args: { host: "", port: "22", user: "", password: "", key_path: "", key_passphrase: "", remote_path: "", local_path: "" } },
                { name: "google.sheets_read", label: "Lire Google Sheets", args: { credentials: "", spreadsheet_id: "", worksheet_title: "", local_path: "" } },
                { name: "google.sheets_write", label: "Écrire Google Sheets", args: { credentials: "", spreadsheet_id: "", worksheet_title: "", local_path: "", clear_sheet: true } },
                { name: "net.http_request", label: "Requête HTTP avancée", args: { url: "", method: "GET", destination: "", headers: "", body: "", extract_regex: "", extract_destination: "" } },
                { name: "net.notify", label: "Notification SMTP / Webhook", args: { type: "webhook", smtp_host: "localhost", smtp_port: "25", smtp_user: "", smtp_pass: "", to: "", subject: "ETL Alert", url: "", message: "" } }
            ],
            "Transformations de données": [
                { name: "data.filter", label: "Filtrer des lignes", args: { source: "", destination: "", field: "", operator: "equals", value: "" } },
                { name: "data.clean", label: "Nettoyer et mapper (AiMapper)", args: { source: "", destination: "", mappings: {}, right_source: "", left_on: "", right_on: "", how_join: "left" } },
                { name: "data.validate", label: "Validation Qualité (DLQ)", args: { source: "", destination: "", quarantine: "", rules: "[]" } },
                { name: "data.csv_to_json", label: "CSV vers JSON", args: { source: "", destination: "" } },
                { name: "data.json_to_csv", label: "JSON vers CSV", args: { source: "", destination: "" } },
                { name: "data.xml_to_json", label: "XML vers JSON", args: { source: "", destination: "" } },
                { name: "data.json_to_xml", label: "Exporter en XML", args: { source: "", destination: "", root_element: "root", row_element: "row" } },
                { name: "data.to_xlsx", label: "Exporter en Excel XLSX", args: { source: "", destination: "", sheet_name: "Sheet1" } },
                { name: "data.delta", label: "Réconciliation Delta CDC", args: { source: "", target: "", keys: "", destination_upsert: "", destination_delete: "", destination_sync: "" } },
                { name: "data.type_cast", label: "Typage strict de schéma", args: { source: "", destination: "", casts: "{}" } }
            ],
            "Bases de Données": [
                { name: "db.query", label: "Requête SQL SELECT", args: { connection_string: "", query: "", destination: "" } },
                { name: "db.insert", label: "Insertion SQL", args: { connection_string: "", table_name: "", source: "", mode: "insert" } },
                { name: "mongodb.find", label: "Recherche MongoDB", args: { connection_string: "", database: "", collection: "", filter: "{}", projection: "", destination: "" } },
                { name: "mongodb.insert", label: "Insertion MongoDB", args: { connection_string: "", database: "", collection: "", source: "", mode: "insert" } }
            ],
            "Analytique & Statistiques": [
                { name: "data.groupby", label: "Agrégations Group By", args: { source: "", destination: "", keys: "", aggregations: "" } },
                { name: "data.metrics", label: "Statistiques descriptives", args: { source: "", destination: "", columns: "" } },
                { name: "data.lookup", label: "Jointure dictionnaire", args: { source: "", destination: "", lookup_source: "", left_on: "", right_on: "", select_columns: "" } },
                { name: "data.deduplicate", label: "Supprimer les doublons", args: { source: "", destination: "", keys: "", keep: "first" } },
                { name: "data.anonymize", label: "Masquage / RGPD", args: { source: "", destination: "", columns: "" } },
                { name: "data.pivot", label: "Pivoter (format large)", args: { source: "", destination: "", index: "", on: "", values: "", aggregate: "sum" } },
                { name: "data.unpivot", label: "Dépivoter (format long)", args: { source: "", destination: "", index: "", on: "", variable_name: "variable", value_name: "value" } }
            ],
            "Intelligence Artificielle": [
                { name: "ai.summarize", label: "Résumé de texte NLP", args: { source: "", destination: "", text_column: "", summary_column: "", model_provider: "", model_id: "", base_url: "" } },
                { name: "ai.extract", label: "Extraction d'entités NLP", args: { source: "", destination: "", text_column: "", schema: "{}", model_provider: "", model_id: "", base_url: "" } }
            ],
            "Contrôle": [
                { name: "core.sub_flow", label: "Sous-flux de traitement", args: { steps: [] } },
                { name: "core.loop", label: "Boucle d'itération", args: { type: "variables", list: "", steps: [] } }
            ]
        };

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
                    const btn = document.createElement('button');
                    btn.className = 'catalog-item-btn';
                    btn.innerHTML = `<span>${item.label}</span> <span style="font-size:0.65rem; color:var(--accent); font-family:monospace; margin-left:8px;">${item.name}</span>`;
                    btn.onclick = () => addPrimitiveNode(item.name, item.label, item.args);
                    itemsDiv.appendChild(btn);
                });

                // Collapsible logic
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
            
            // Generate unique step index/number
            let nextStepNum = 1;
            if (currentRecipe.steps.length > 0) {
                // Find global max to avoid duplicate step IDs anywhere in nested flows
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

            // Copy args deep structure
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
            
            // Re-render
            renderNodes(steps);
            addLog(`Nœud '${newStep.ui.label}' ajouté manuellement.`, 'success');
        }

        // --- UNDO / REDO HISTORY STACK ENGINE ---
        let undoStack = [];
        let redoStack = [];

        function saveHistoryState() {
            if (!currentRecipe) return;
            // Capture a deep copy of currentRecipe structure
            const stateSnapshot = JSON.stringify(currentRecipe);
            // Limit stack depth to 50
            if (undoStack.length === 0 || undoStack[undoStack.length - 1] !== stateSnapshot) {
                undoStack.push(stateSnapshot);
                if (undoStack.length > 50) {
                    undoStack.shift();
                }
                redoStack = []; // Clear redo stack on new action
            }
        }

        function undoAction() {
            if (undoStack.length <= 1) {
                addLog("Rien à annuler.", "warning");
                return;
            }
            const currentState = undoStack.pop();
            redoStack.push(currentState);
            
            const prevStateStr = undoStack[undoStack.length - 1];
            currentRecipe = JSON.parse(prevStateStr);
            
            // Re-render current navigation depth
            const steps = getCurrentStepList();
            renderNodes(steps);
            detectAndRenderEnvVars();
            saveActiveWorkspace();
            addLog("Action annulée.", "info");
        }

        function redoAction() {
            if (redoStack.length === 0) {
                addLog("Rien à rétablir.", "warning");
                return;
            }
            const nextStateStr = redoStack.pop();
            undoStack.push(nextStateStr);
            
            currentRecipe = JSON.parse(nextStateStr);
            
            const steps = getCurrentStepList();
            renderNodes(steps);
            detectAndRenderEnvVars();
            saveActiveWorkspace();
            addLog("Action rétablie.", "info");
        }

        // Bind Ctrl+Z and Ctrl+Y (or Ctrl+Shift+Z) globally
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey) {
                if (e.key.toLowerCase() === 'z') {
                    e.preventDefault();
                    undoAction();
                } else if (e.key.toLowerCase() === 'y') {
                    e.preventDefault();
                    redoAction();
                }
            }
        });

        // --- CYCLE DETECTION (Tri Topologique) ---
        function hasCycle(steps) {
            const adj = {};
            const visited = {};
            const recStack = {};

            steps.forEach(s => {
                adj[s.step] = s.depends_on || [];
                visited[s.step] = false;
                recStack[s.step] = false;
            });

            function isCyclicUtil(v) {
                if (!visited[v]) {
                    visited[v] = true;
                    recStack[v] = true;

                    const neighbors = adj[v] || [];
                    for (const n of neighbors) {
                        // Skip checking neighbors that are not in current step list (dangling ids)
                        if (adj[n] === undefined) continue;

                        if (!visited[n] && isCyclicUtil(n)) {
                            return true;
                        } else if (recStack[n]) {
                            return true;
                        }
                    }
                }
                recStack[v] = false;
                return false;
            }

            for (const s of steps) {
                if (isCyclicUtil(s.step)) {
                    return true;
                }
            }
            return false;
        }

        // --- SEARCH CANVAS NODES ---
        function searchCanvasNodes(query) {
            const cleanQuery = query.trim().toLowerCase();
            document.querySelectorAll('workflow-node').forEach(node => {
                const label = node.getAttribute('label').toLowerCase();
                const primitive = node.getAttribute('primitive').toLowerCase();
                if (cleanQuery === "") {
                    // Reset styling
                    node.style.opacity = "1";
                    node.style.boxShadow = "";
                } else if (label.includes(cleanQuery) || primitive.includes(cleanQuery)) {
                    node.style.opacity = "1";
                    node.style.boxShadow = "0 0 25px var(--accent), 0 0 5px var(--accent)";
                } else {
                    node.style.opacity = "0.3";
                    node.style.boxShadow = "";
                }
            });
        }

        function clearCanvasNodeSearch() {
            document.getElementById('canvas-node-search').value = "";
            searchCanvasNodes("");
        }

        // --- DUPLICATE NODE ---
        function duplicateNode(stepNum) {
            const steps = getCurrentStepList();
            const sourceStep = steps.find(s => s.step === stepNum);
            if (!sourceStep) return;

            // Generate unique step index
            let nextStepNum = 1;
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

            // Deep clone step object arguments
            const clonedArgs = JSON.parse(JSON.stringify(sourceStep.args));
            
            // Offset visual position slightly
            const originalX = (sourceStep.ui && sourceStep.ui.position) ? sourceStep.ui.position.x : 100;
            const originalY = (sourceStep.ui && sourceStep.ui.position) ? sourceStep.ui.position.y : 100;

            const duplicated = {
                step: nextStepNum,
                primitive: sourceStep.primitive,
                depends_on: [], // Keep duplicate initially independent to avoid cycles
                args: clonedArgs,
                ui: {
                    label: `${sourceStep.ui.label.split(" (Copy)")[0]} (Copy) (${nextStepNum})`,
                    position: {
                        x: originalX + 50,
                        y: originalY + 50
                    }
                }
            };

            steps.push(duplicated);
            saveHistoryState();
            renderNodes(steps);
            saveActiveWorkspace();
            addLog(`Nœud '${duplicated.ui.label}' dupliqué avec succès.`, 'success');
        }

        function deleteStepNode(stepNum) {
            if (!currentRecipe || !currentRecipe.steps) return;
            const steps = getCurrentStepList();
            const index = steps.findIndex(s => s.step === stepNum);
            if (index > -1) {
                const stepLabel = steps[index].ui.label;
                steps.splice(index, 1);
                
                // Clean references in depends_on lists at this nesting level
                steps.forEach(s => {
                    if (s.depends_on) {
                        s.depends_on = s.depends_on.filter(d => d !== stepNum);
                    }
                });

                saveHistoryState();
                addLog(`Nœud '${stepLabel}' supprimé du flux.`, 'warning');
                closeNodeEditor();
                renderNodes(steps);
                saveActiveWorkspace();
            }
        }