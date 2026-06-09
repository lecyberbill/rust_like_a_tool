// [WFGY] Zone: SAFE | λ: 0.1 | Action: Modularized canvas and drawing logic

let canvasZoom = 1;
let canvasPanX = 0;
let canvasPanY = 0;
let isPanMode = false;
let isPanning = false;
let panStartX = 0;
let panStartY = 0;
let undoStack = [];
let redoStack = [];
let dataLineageMode = false;
let cachedLineage = null;
let isDrawingConnection = false;
let connectionSourceStep = null;
let tempLineSvg = null;

// Shared Globals
let ws;
let activeNodes = {};
let currentRecipe = null;
let activeEnv = 'dev';
let selectedStepNum = null;
let currentNavPath = [];
let currentRunHistory = [];
let selectedRunId = null;
let currentAuditTrail = [];
let studyOriginalIntent = '';
let studyChatHistory = [];
let promptHistory = [];
let historyIndex = -1;


function toggleTheme() {
    const isLight = document.body.classList.toggle('light-theme');
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
    addLog(`Thème basculé sur : ${isLight ? 'Clair (Moderne Noir & Blanc)' : 'Sombre'}`, 'info');
    drawConnections();
}

function updateCanvasTransform() {
    const transform = `translate(${canvasPanX}px, ${canvasPanY}px) scale(${canvasZoom})`;
    const canvas = document.getElementById('canvas');
    const svg = document.getElementById('connections-svg');
    if (canvas) {
        canvas.style.transform = transform;
        canvas.style.transformOrigin = '0 0';
    }
    if (svg) {
        svg.style.transform = transform;
        svg.style.transformOrigin = '0 0';
    }
    const zoomValText = document.getElementById('zoom-level-val');
    if (zoomValText) {
        zoomValText.innerText = `${Math.round(canvasZoom * 100)}%`;
    }
    drawConnections();
}

function updateCanvasZoom() {
    updateCanvasTransform();
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
    canvasPanX = 0;
    canvasPanY = 0;
    updateCanvasTransform();
}

function togglePanMode() {
    isPanMode = !isPanMode;
    const btn = document.getElementById('btn-pan-mode');
    if (btn) {
        btn.classList.toggle('active', isPanMode);
        btn.title = isPanMode ? 'Désactiver le déplacement' : 'Déplacer le canevas (Main)';
    }
    const canvas = document.getElementById('canvas-wrapper');
    if (canvas) {
        canvas.style.cursor = isPanMode ? 'grab' : '';
    }
    addLog(isPanMode ? 'Mode Déplacement activé — glisser pour déplacer le canevas' : 'Mode Édition activé', 'info');
}

function startCanvasPan(e) {
    if (!isPanMode) return;
    isPanning = true;
    panStartX = e.clientX - canvasPanX;
    panStartY = e.clientY - canvasPanY;
    const canvas = document.getElementById('canvas-wrapper');
    if (canvas) canvas.style.cursor = 'grabbing';
    e.preventDefault();
}

function doCanvasPan(e) {
    if (!isPanning || !isPanMode) return;
    canvasPanX = e.clientX - panStartX;
    canvasPanY = e.clientY - panStartY;
    updateCanvasTransform();
}

function stopCanvasPan(e) {
    if (!isPanning) return;
    isPanning = false;
    const canvas = document.getElementById('canvas-wrapper');
    if (canvas && isPanMode) canvas.style.cursor = 'grab';
}

function startDrawingConnection(stepNum, event) {
    isDrawingConnection = true;
    connectionSourceStep = stepNum;
    
    const svg = document.getElementById('connections-svg');
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
        const currentSteps = getCurrentStepList();
        const stepB = currentSteps.find(s => s.step === targetStep);
        if (stepB) {
            if (!stepB.depends_on) stepB.depends_on = [];
            if (!stepB.depends_on.includes(connectionSourceStep)) {
                const stepA = currentSteps.find(s => s.step === connectionSourceStep);
                if (stepA && stepA.depends_on && stepA.depends_on.includes(targetStep)) {
                    addLog("Boucle directe détectée ! Connexion rejetée.", "error");
                } else {
                    stepB.depends_on.push(connectionSourceStep);
                    if (hasCycle(currentSteps)) {
                        stepB.depends_on.pop();
                        addLog("Boucle complexe/Cycle détecté ! Connexion rejetée pour conserver le graphe acyclique (DAG).", "error");
                    } else {
                        saveHistoryState();
                        addLog(`Connexion créée : Étape ${targetStep} dépend de l'étape ${connectionSourceStep}`, "success");
                        
                        drawConnections();
                        saveActiveWorkspace();
                        
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

function toggleDataLineageMode() {
    dataLineageMode = !dataLineageMode;
    const btn = document.getElementById('btn-toggle-lineage');
    if (btn) {
        if (dataLineageMode) {
            btn.classList.add('active');
            btn.style.background = 'rgba(0, 240, 255, 0.1)';
            btn.style.boxShadow = '0 0 10px var(--accent-glow)';
            addLog("Mode Lignage de Données (Lineage) activé.", "info");
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'GET_DATA_LINEAGE' }));
            }
        } else {
            btn.classList.remove('active');
            btn.style.background = '';
            btn.style.boxShadow = '';
            cachedLineage = null;
            addLog("Mode Lignage désactivé (Affichage des dépendances d'exécution).", "info");
            drawConnections();
        }
    }
}

function drawConnections() {
    const svg = document.getElementById('connections-svg');
    if (!svg) return;
    svg.innerHTML = '';
    
    const currentSteps = getCurrentStepList();
    if (currentSteps.length === 0) return;

    if (dataLineageMode) {
        if (cachedLineage) {
            renderDataLineageOverlays(cachedLineage);
        } else {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'GET_DATA_LINEAGE' }));
            }
        }
        return;
    }
    
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
                
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', pathD);
                path.setAttribute('class', 'connection-line');
                path.addEventListener('click', (e) => {
                    e.stopPropagation();
                    selectConnection(parentNum, stepNum);
                });
                
                svg.appendChild(path);
                svg.appendChild(clickPath);
                
                const label = (step.ui && step.ui.connection_labels) ? step.ui.connection_labels[parentNum] : "";
                if (label) {
                    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    const midX = (x1 + 3 * controlX + 3 * controlX + x2) / 8;
                    const midY = (y1 + 3 * y1 + 3 * y2 + y2) / 8;
                    
                    text.setAttribute('x', midX);
                    text.setAttribute('y', midY - 8);
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
    if (!canvas) return;
    canvas.innerHTML = '';
    activeNodes = {};

    const startX = 50;
    const startY = 80;
    const horizontalSpacing = 420;
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
    
    setTimeout(drawConnections, 50);
}

window.addEventListener('resize', drawConnections);

function renderDataLineageOverlays(lineage) {
    cachedLineage = lineage;
    const svg = document.getElementById('connections-svg');
    if (!svg) return;
    svg.innerHTML = '';
    
    if (!lineage) return;
    
    Object.keys(lineage).forEach(fileKey => {
        const info = lineage[fileKey];
        const producer = info.producer;
        const consumers = info.consumers || [];
        
        if (producer && activeNodes[producer]) {
            consumers.forEach(consumer => {
                if (activeNodes[consumer]) {
                    const nodeA = activeNodes[producer];
                    const nodeB = activeNodes[consumer];
                    
                    const rectA = nodeA.getBoundingClientRect();
                    const rectB = nodeB.getBoundingClientRect();
                    const canvasRect = document.getElementById('canvas').getBoundingClientRect();
                    
                    const x1 = (rectA.left - canvasRect.left + rectA.width) / canvasZoom;
                    const y1 = (rectA.top - canvasRect.top + rectA.height / 2) / canvasZoom;
                    
                    const x2 = (rectB.left - canvasRect.left) / canvasZoom;
                    const y2 = (rectB.top - canvasRect.top + rectB.height / 2) / canvasZoom;
                    
                    const controlX = x1 + (x2 - x1) / 2;
                    const pathD = `M ${x1} ${y1} C ${controlX} ${y1}, ${controlX} ${y2}, ${x2} ${y2}`;
                    
                    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    path.setAttribute('d', pathD);
                    path.setAttribute('fill', 'none');
                    path.setAttribute('stroke', '#00f0ff');
                    path.setAttribute('stroke-width', '2.5');
                    path.setAttribute('stroke-dasharray', '6,4');
                    path.style.filter = 'drop-shadow(0 0 3px rgba(0, 240, 255, 0.4))';
                    
                    svg.appendChild(path);
                    
                    const filename = info.file_path.split('/').pop().split('\\').pop();
                    if (filename) {
                        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                        const midX = (x1 + 3 * controlX + 3 * controlX + x2) / 8;
                        const midY = (y1 + 3 * y1 + 3 * y2 + y2) / 8;
                        
                        text.setAttribute('x', midX);
                        text.setAttribute('y', midY - 8);
                        text.setAttribute('text-anchor', 'middle');
                        text.setAttribute('fill', '#00f0ff');
                        text.setAttribute('font-size', '0.72rem');
                        text.setAttribute('font-weight', 'bold');
                        text.style.fontFamily = 'monospace';
                        text.style.pointerEvents = 'none';
                        text.textContent = filename;
                        
                        svg.appendChild(text);
                    }
                }
            });
        }
    });
}

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

function saveHistoryState() {
    if (!currentRecipe) return;
    const stateSnapshot = JSON.stringify(currentRecipe);
    if (undoStack.length === 0 || undoStack[undoStack.length - 1] !== stateSnapshot) {
        undoStack.push(stateSnapshot);
        if (undoStack.length > 50) {
            undoStack.shift();
        }
        redoStack = [];
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

document.addEventListener('keydown', (e) => {
    if (e.ctrlKey) {
        if (e.key.toLowerCase() === 'z') {
            e.preventDefault();
            undoAction();
        } else if (e.key.toLowerCase() === 'y') {
            e.preventDefault();
            redoAction();
        } else if (e.key.toLowerCase() === 'd') {
            e.preventDefault();
            if (selectedStepNum !== null) {
                duplicateNode(selectedStepNum);
            }
        }
    }
});

function searchCanvasNodes(query) {
    const cleanQuery = query.trim().toLowerCase();
    document.querySelectorAll('workflow-node').forEach(node => {
        const label = node.getAttribute('label').toLowerCase();
        const primitive = node.getAttribute('primitive').toLowerCase();
        if (cleanQuery === "") {
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
    const input = document.getElementById('canvas-node-search');
    if (input) input.value = "";
    searchCanvasNodes("");
}
