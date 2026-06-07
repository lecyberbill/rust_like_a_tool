// [WFGY] Zone: SAFE | λ: 0.1 | Action: Modularized modal controllers and helpers

function showConflictModal(step, message, options) {
    const modal = document.getElementById('conflict-modal');
    const messageEl = document.getElementById('conflict-message');
    const actionsEl = document.getElementById('conflict-actions');
    
    if (!modal || !messageEl || !actionsEl) return;
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

function openStudyChat(originalIntent, analysis, questions) {
    studyOriginalIntent = originalIntent;
    studyChatHistory = [];
    
    const modal = document.getElementById('study-chat-modal');
    const msgArea = document.getElementById('study-chat-messages');
    if (!modal || !msgArea) return;
    
    msgArea.innerHTML = '';
    modal.classList.add('active');
    
    appendChatBubble('assistant', `<strong>Analyse de l'Intention :</strong><br>${analysis}`);
    
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

function closeStudyChat() {
    const modal = document.getElementById('study-chat-modal');
    if (modal) modal.classList.remove('active');
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

function copyWebhookUrl() {
    const input = document.getElementById('trigger-webhook-url');
    if (input) {
        input.select();
        input.setSelectionRange(0, 9999);
        navigator.clipboard.writeText(input.value);
        alert("URL Webhook copiée !");
    }
}

function closeDataPreview() {
    const panel = document.getElementById('data-preview-panel');
    if (panel) panel.classList.add('collapsed');
}

function openAuditTrailModal() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'GET_AUDIT_TRAIL' }));
    }
    document.getElementById('audit-modal').style.display = 'flex';
}

function closeAuditTrailModal() {
    document.getElementById('audit-modal').style.display = 'none';
}

function renderAuditTrailList(auditRecords) {
    currentAuditTrail = auditRecords || [];
    const tbody = document.getElementById('audit-table-body');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    if (currentAuditTrail.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 30px; color: var(--text-muted);">Aucun enregistrement d\'audit disponible.</td></tr>';
        return;
    }
    
    currentAuditTrail.forEach(record => {
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid var(--border)';
        
        const date = new Date(record.timestamp);
        const dateStr = date.toLocaleString();
        const isSuccess = record.status === 'success';
        const statusBadge = `<span class="status-badge" style="background: ${isSuccess ? 'rgba(0,255,102,0.1)' : 'rgba(239,68,68,0.1)'}; color: ${isSuccess ? 'var(--success)' : 'var(--error)'}; border: 1px solid ${isSuccess ? 'var(--success)' : 'var(--error)'}; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;">${record.status.toUpperCase()}</span>`;
        
        tr.innerHTML = `
            <td style="padding: 10px;">${dateStr}</td>
            <td style="padding: 10px; font-weight: bold; color: var(--accent);">${record.workspace_id}</td>
            <td style="padding: 10px;">${record.username}</td>
            <td style="padding: 10px; font-family: 'Roboto Mono', monospace; font-size: 0.8rem;">${record.hostname} (${record.os_name})</td>
            <td style="padding: 10px;">${statusBadge}</td>
            <td style="padding: 10px; font-family: 'Roboto Mono', monospace; font-weight: bold;">${record.duration_ms} ms</td>
            <td style="padding: 10px; text-align: right;">
                <button class="toggle-logs-btn" onclick="openAuditDetailsModal('${record.run_id}')" style="background: rgba(192, 132, 252, 0.05); color: #c084fc; border-color: rgba(192, 132, 252, 0.2);">🔍 Voir détails</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function openAuditDetailsModal(runId) {
    const record = currentAuditTrail.find(r => r.run_id === runId);
    if (!record) return;
    
    const container = document.getElementById('audit-details-content');
    if (!container) return;
    
    let stepsHtml = '';
    const steps = record.steps_executed || [];
    steps.forEach(s => {
        const isSuccess = s.status === 'success';
        const color = isSuccess ? 'var(--success)' : (s.status === 'skipped' ? 'var(--text-muted)' : 'var(--error)');
        stepsHtml += `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; background: rgba(255,255,255,0.02); border: 1px solid var(--border); border-radius: 6px; margin-bottom: 6px;">
                <div>
                    <span style="font-weight: bold; color: ${color};">Étape ${s.step}</span> : ${s.label}
                </div>
                <div style="font-family: 'Roboto Mono', monospace; font-size: 0.8rem;">
                    <span style="color: ${color}; font-weight: bold;">${s.status.toUpperCase()}</span> (${s.duration_ms} ms)
                </div>
            </div>
        `;
    });
    
    let lineageHtml = '';
    const lineage = record.data_lineage || {};
    const lineageKeys = Object.keys(lineage);
    if (lineageKeys.length === 0) {
        lineageHtml = '<div style="color: var(--text-muted); font-style: italic;">Aucun lignage de données enregistré.</div>';
    } else {
        lineageKeys.forEach(filePath => {
            const info = lineage[filePath];
            const consumersStr = info.consumers && info.consumers.length > 0 ? info.consumers.join(', ') : 'Aucun';
            lineageHtml += `
                <div style="padding: 8px; background: rgba(0, 240, 255, 0.02); border: 1px solid rgba(0, 240, 255, 0.1); border-radius: 6px; margin-bottom: 8px; font-family: 'Roboto Mono', monospace; font-size: 0.78rem; word-break: break-all;">
                    <div style="font-weight: bold; color: var(--accent); margin-bottom: 4px;">📄 ${filePath}</div>
                    <div style="display: flex; flex-direction: column; gap: 2px; padding-left: 10px; color: var(--text-muted);">
                        <div>Produit par : Étape ${info.producer || 'Externe / Inconnu'}</div>
                        <div>Consommé par : Étapes [${consumersStr}]</div>
                    </div>
                </div>
            `;
        });
    }
    
    container.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; border-bottom: 1px solid var(--border); padding-bottom: 16px;">
            <div>
                <div style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase;">ID du Flux</div>
                <div style="font-weight: bold; font-size: 1rem; color: var(--text);">${record.workspace_id}</div>
                <div style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; margin-top: 10px;">ID Exécution</div>
                <div style="font-family: 'Roboto Mono', monospace; font-size: 0.85rem;">${record.run_id}</div>
            </div>
            <div>
                <div style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase;">Date / Heure</div>
                <div>${new Date(record.timestamp).toLocaleString()}</div>
                <div style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; margin-top: 10px;">Environnement</div>
                <div>Hôte: ${record.hostname} (${record.os_name})<br>User: ${record.username}</div>
            </div>
        </div>
        
        <h5 style="margin-top: 0; margin-bottom: 8px; color: var(--success); text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.5px;">📋 Étapes exécutées</h5>
        <div style="margin-bottom: 16px;">
            ${stepsHtml || '<div style="color: var(--text-muted); font-style: italic;">Aucune étape exécutée.</div>'}
        </div>
        
        <h5 style="margin-top: 0; margin-bottom: 8px; color: var(--accent); text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.5px;">🔗 Lignage des Fichiers (Data Lineage)</h5>
        <div>
            ${lineageHtml}
        </div>
    `;
    
    document.getElementById('audit-details-modal').style.display = 'flex';
}

function closeAuditDetailsModal() {
    document.getElementById('audit-details-modal').style.display = 'none';
}
