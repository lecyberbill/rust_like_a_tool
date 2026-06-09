// [WFGY] Zone: SAFE | λ: 0.1 | Action: Modularized AiMapper component

let mapperStepNum = null;
let mapperSourceHeaders = [];
let mapperRightSourceHeaders = [];
let mapperMappings = [];
let lastFocusedInput = null;
let mapperVariables = [];
let activeFormulaRowIdx = null;

function openAiMapper(stepNum) {
    mapperStepNum = stepNum;
    const step = currentRecipe.steps.find(s => s.step === stepNum);
    if (!step || step.primitive !== 'data.clean') return;

    const modal = document.getElementById('aimapper-modal');
    modal.style.display = 'flex';
    
    document.getElementById('aimapper-source-path').innerText = `Source : ${step.args.source || ''}`;
    
    document.getElementById('aimapper-join-right-source').value = step.args.right_source || '';
    document.getElementById('aimapper-join-type').value = step.args.how_join || 'left';

    document.getElementById('aimapper-source-list').innerHTML = '<div style="color:var(--text-muted); font-style:italic; padding:10px;">Chargement...</div>';
    document.getElementById('aimapper-mapping-body').innerHTML = '';
    document.getElementById('aimapper-dest-list').innerHTML = '';

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

    if (step.ui && step.ui.variables) {
        mapperVariables = JSON.parse(JSON.stringify(step.ui.variables));
    } else {
        mapperVariables = [];
    }
    renderLocalVariables();

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
    if (!container) return;
    container.innerHTML = '';

    if (mapperSourceHeaders.length === 0 && mapperRightSourceHeaders.length === 0 && mapperVariables.length === 0) {
        container.innerHTML = '<div style="color:var(--text-muted); font-style:italic; padding:10px;">Aucune colonne ou variable</div>';
        return;
    }

    if (mapperSourceHeaders.length > 0) {
        const titleG = document.createElement('div');
        titleG.style.cssText = 'font-size:0.68rem; color:var(--accent); text-transform:uppercase; font-weight:800; padding:2px 4px;';
        titleG.innerText = 'Table A (Source)';
        container.appendChild(titleG);

        mapperSourceHeaders.forEach(header => {
            if (search && !header.toLowerCase().includes(search)) return;

            const div = document.createElement('div');
            div.className = 'aimapper-col-item';
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

    if (mapperRightSourceHeaders.length > 0) {
        const titleD = document.createElement('div');
        titleD.style.cssText = 'font-size:0.68rem; color:var(--running); text-transform:uppercase; font-weight:800; padding:2px 4px; margin-top:6px; border-top:1px solid var(--border);';
        titleD.innerText = 'Table B (Jointure)';
        container.appendChild(titleD);

        mapperRightSourceHeaders.forEach(header => {
            if (search && !header.toLowerCase().includes(search)) return;

            const div = document.createElement('div');
            div.className = 'aimapper-col-item right-source';
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

    if (mapperVariables.length > 0) {
        const sep = document.createElement('div');
        sep.style.cssText = 'font-size:0.7rem; color:#c084fc; text-transform:uppercase; font-weight:800; padding:4px 4px; border-top:1px solid var(--border); margin-top:6px;';
        sep.innerText = 'Variables';
        container.appendChild(sep);

        mapperVariables.forEach(v => {
            if (!v.name || !v.name.trim()) return;
            if (search && !v.name.toLowerCase().includes(search)) return;

            const div = document.createElement('div');
            div.className = 'aimapper-col-item variable';
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
    if (!tbody) return;
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
                <button class="toggle-logs-btn" style="padding:2px 6px; font-size:0.75rem; border-color:var(--error); color:var(--error);" onclick="deleteMappingRow(${idx})">🗑️</button>
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
    if (!container) return;
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
        div.className = 'aimapper-col-item dest';
        div.innerText = col;
        container.appendChild(div);
    });
}

function openFormulaEditor(idx) {
    activeFormulaRowIdx = idx;
    const m = mapperMappings[idx];
    if (!m) return;

    const modal = document.getElementById('aimapper-formula-modal');
    modal.style.display = 'flex';

    document.getElementById('formula-editor-textarea').value = m.sourceCol || '';

    const container = document.getElementById('formula-editor-fields');
    if (!container) return;
    container.innerHTML = '';

    mapperSourceHeaders.forEach(header => {
        const btn = document.createElement('div');
        btn.className = 'aimapper-btn-icon';
        btn.innerHTML = `<span>${header}</span> <span style="font-size:0.65rem; color:var(--accent);">colonne A</span>`;
        btn.onclick = () => insertTextAtCursor(header);
        container.appendChild(btn);
    });

    mapperRightSourceHeaders.forEach(header => {
        const btn = document.createElement('div');
        btn.className = 'aimapper-btn-icon right-source';
        btn.innerHTML = `<span>${header}</span> <span style="font-size:0.65rem; color:var(--running);">colonne B</span>`;
        btn.onclick = () => insertTextAtCursor(header);
        container.appendChild(btn);
    });

    mapperVariables.forEach(v => {
        if (!v.name) return;
        const btn = document.createElement('div');
        btn.className = 'aimapper-btn-icon variable';
        btn.innerHTML = `<span>${v.name}</span> <span style="font-size:0.65rem; color:#c084fc;">variable</span>`;
        btn.onclick = () => insertTextAtCursor(v.name);
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
        btn.className = 'aimapper-btn-icon formula';
        btn.innerHTML = `<span>${v.name}</span> <span style="font-size:0.65rem; color:var(--accent);" title="${v.desc}">système</span>`;
        btn.onclick = () => insertTextAtCursor(v.name);
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
    const textarea = document.getElementById('formula-editor-textarea');
    if (textarea) {
        textarea.value = text;
        textarea.focus();
    }
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
    if (!container) return;
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
            <button class="toggle-logs-btn" style="padding:2px 6px; border-color:var(--error); color:var(--error);" onclick="deleteLocalVariable(${idx})">🗑️</button>
        `;
        
        container.appendChild(div);
    });
}
