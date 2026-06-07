// [WFGY] Zone: SAFE | λ: 0.2 | Action: Extract WebSocket API communication layer

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

function saveSettings() {
    const provider = document.getElementById('setting-provider').value;
    const model = document.getElementById('setting-model').value;
    const baseUrl = document.getElementById('setting-base-url').value;

    addLog(`Application des réglages IA : Provider=${provider}, Model=${model}`, 'info');

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
        document.getElementById('prompt-drawer').classList.remove('active');
        document.getElementById('prompt-history-list').style.display = 'none';
    } else {
        addLog('Erreur : impossible d\'envoyer l\'intention (déconnecté ou vide).', 'error');
    }
}

function sendStudyChatReply() {
    const input = document.getElementById('study-chat-input');
    const text = input.value.trim();
    if (!text) return;
    
    appendChatBubble('user', text);
    studyChatHistory.push({ role: 'user', content: text });
    input.value = '';
    
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
