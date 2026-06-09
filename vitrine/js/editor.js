// [WFGY] Zone: SAFE | λ: 0.1 | Action: Modularized editor panel components

function editNode(stepNum) {
    selectedStepNum = stepNum;
    const currentSteps = getCurrentStepList();
    const step = currentSteps.find(s => s.step === stepNum);
    if (!step) return;

    const panel = document.getElementById('node-editor-panel');
    const container = document.getElementById('node-editor-container');
    if (!panel || !container) return;
    
    panel.classList.remove('collapsed');
    document.getElementById('node-editor-title').innerText = `Étape ${stepNum} : ${step.ui.label}`;

    let html = `
        <div class="editor-section" style="display:flex; flex-wrap:wrap; gap:8px; padding:8px 16px; border-bottom:1px solid var(--border);">
            <button class="editor-tool-btn" title="Documentation" onclick="showPrimitiveDoc('${step.primitive}')" style="background:var(--bg-card); color:var(--text);">ℹ️ Doc</button>
            <button class="editor-tool-btn" title="Dupliquer" onclick="duplicateNode(${stepNum})" style="background:var(--bg-card); color:var(--text);">📋 Dupliquer</button>
            ${step.primitive === 'data.clean' ? `<button class="editor-tool-btn" title="AiMapper" onclick="openAiMapper(${stepNum})" style="background:linear-gradient(135deg, var(--success) 0%, rgba(0,255,102,0.6) 100%); color:#000; font-weight:800;">🗺️ AiMapper</button>` : ''}
            <button class="editor-tool-btn" title="Supprimer" onclick="deleteStepNode(${stepNum})" style="background:var(--error); color:#fff;">🗑️ Supprimer</button>
        </div>
        <div class="editor-section">
            <div class="editor-section-title">Infos Générales</div>
            <div class="editor-input-group">
                <label>Nom convivial (Label)</label>
                <input type="text" class="editor-input" id="edit-node-label" value="${step.ui.label}" oninput="saveNodeChanges()">
            </div>
        </div>
    `;

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

    html += `
        <div class="editor-section">
            <div class="editor-section-title">Arguments (${step.primitive})</div>
    `;
    if (step.primitive === 'data.clean') {
        html += `
            <button class="save-secrets-btn" style="background: linear-gradient(135deg, var(--success) 0%, rgba(0,255,102,0.6) 100%); color: #000; font-weight: 800; margin-bottom: 16px;" onclick="openAiMapper(${stepNum})">🗺️ Ouvrir AiMapper</button>
        `;
    }

    const deps = step.depends_on || [];
    const args = step.args || {};
    const enumOpts = (typeof primitiveEnums !== 'undefined' && primitiveEnums[step.primitive]) || {};
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
        } else if (Array.isArray(val)) {
            // Tableau (steps, then_steps, else_steps...)
            const isSteps = key === 'steps' || key.endsWith('_steps');
            html += `
                <div class="editor-input-group">
                    <label>${key}</label>
                    <div style="display:flex; align-items:center; gap:8px; padding:6px 10px; background:var(--bg-card); border:1px solid var(--border); border-radius:6px;">
                        <span style="font-size:0.85rem;color:var(--text-muted);">${val.length} élément${val.length > 1 ? 's' : ''}</span>
                        ${isSteps && val.length > 0 ? `<button class="editor-tool-btn" style="font-size:0.75rem;padding:2px 8px;" onclick="drillDown(${stepNum}, '${step.ui.label}')">🔍 Voir</button>` : ''}
                    </div>
                </div>
            `;
        } else if (typeof val === 'object' && val !== null) {
            // Objet (mappings, cases...)
            const jsonStr = JSON.stringify(val, null, 2);
            const preview = jsonStr.length > 60 ? jsonStr.substring(0, 60) + '…' : jsonStr;
            html += `
                <div class="editor-input-group">
                    <label>${key}</label>
                    <textarea class="editor-input" id="${inputId}" style="min-height:70px;font-family:monospace;font-size:0.75rem;" oninput="saveNodeChanges()">${jsonStr}</textarea>
                </div>
            `;
        } else if (enumOpts[key]) {
            let hint = '';
            if (key === 'source' && !val && deps.length > 0) {
                const parentStep = currentSteps.find(s => s.step === deps[0]);
                if (parentStep) {
                    hint = `<div style="font-size:0.75rem;color:var(--accent);font-style:italic;margin-top:2px;">↳ hérité depuis « ${parentStep.ui.label} » (étape ${deps[0]})</div>`;
                }
            }
            html += `
                <div class="editor-input-group">
                    <label>${key}</label>
                    <select class="editor-input" id="${inputId}" onchange="saveNodeChanges()">
                        ${enumOpts[key].map(opt => `<option value="${opt}"${val === opt || (val === true && opt === 'true') || (val === false && opt === 'false') ? ' selected' : ''}>${opt}</option>`).join('')}
                    </select>
                    ${hint}
                </div>
            `;
        } else {
            let hint = '';
            // Source héritée du parent
            if (key === 'source' && !val && deps.length > 0) {
                const parentStep = currentSteps.find(s => s.step === deps[0]);
                if (parentStep) {
                    hint = `<div style="font-size:0.75rem;color:var(--accent);font-style:italic;margin-top:2px;">↳ hérité depuis « ${parentStep.ui.label} » (étape ${deps[0]})</div>`;
                }
            }
            // Destination auto-générée
            if (key === 'destination' && !val) {
                hint = `<div style="font-size:0.75rem;color:var(--text-muted);font-style:italic;margin-top:2px;">↳ auto-généré si vide (workspace/output/step_${stepNum}_...)</div>`;
            }
            // data.merge.sources → textarea multi-lignes
            if (key === 'sources') {
                html += `
                    <div class="editor-input-group">
                        <label>${key} <span style="font-weight:normal;font-size:0.7rem;color:var(--text-muted);">(un chemin par ligne)</span></label>
                        <textarea class="editor-input" id="${inputId}" style="min-height:60px;font-family:monospace;font-size:0.8rem;" oninput="saveNodeChanges()">${val}</textarea>
                        ${hint}
                    </div>
                `;
            } else {
                html += `
                    <div class="editor-input-group">
                        <label>${key}</label>
                        <input type="text" class="editor-input" id="${inputId}" value="${val}" oninput="saveNodeChanges()">
                        ${hint}
                    </div>
                `;
            }
        }
    }
    html += `</div>`;


    container.innerHTML = html;
}

function closeNodeEditor() {
    const panel = document.getElementById('node-editor-panel');
    if (panel) panel.classList.add('collapsed');
    selectedStepNum = null;
}

function saveNodeChanges() {
    if (selectedStepNum === null || !currentRecipe) return;
    const currentSteps = getCurrentStepList();
    const step = currentSteps.find(s => s.step === selectedStepNum);
    if (!step) return;
    saveHistoryState();

    const labelInput = document.getElementById('edit-node-label');
    if (labelInput) {
        step.ui.label = labelInput.value;
        const nodeHeaderLabel = document.querySelector(`#node-step-${selectedStepNum} .node-header span:first-child`);
        if (nodeHeaderLabel) {
            nodeHeaderLabel.innerText = labelInput.value;
        }
    }

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

    const args = step.args || {};
    for (const key of Object.keys(args)) {
        const inputId = `arg-${key}`;
        const el = document.getElementById(inputId);
        if (el) {
            if (el.type === 'checkbox') {
                step.args[key] = el.checked;
            } else if (el.tagName === 'TEXTAREA') {
                try {
                    step.args[key] = JSON.parse(el.value);
                } catch {
                    step.args[key] = el.value;
                }
                // data.merge.sources : normaliser les retours à la ligne en virgules
                if (key === 'sources' && typeof step.args[key] === 'string') {
                    step.args[key] = step.args[key].split('\n').map(s => s.trim()).filter(Boolean).join(',');
                }
            } else {
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

    drawConnections();
    detectAndRenderEnvVars();
}



function duplicateNode(stepNum) {
    const steps = getCurrentStepList();
    const sourceStep = steps.find(s => s.step === stepNum);
    if (!sourceStep) return;

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

    const clonedArgs = JSON.parse(JSON.stringify(sourceStep.args));
    
    const originalX = (sourceStep.ui && sourceStep.ui.position) ? sourceStep.ui.position.x : 100;
    const originalY = (sourceStep.ui && sourceStep.ui.position) ? sourceStep.ui.position.y : 100;

    const duplicated = {
        step: nextStepNum,
        primitive: sourceStep.primitive,
        depends_on: [],
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
