<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Power Model Tool v8.2 (Tree View Control)</title>
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

    <style>
        body { padding: 20px; background-color: #f4f6f9; font-family: 'Segoe UI', Microsoft JhengHei, sans-serif; }
        .nav-tabs .nav-link { cursor: pointer; color: #495057; font-size: 0.95rem; }
        .nav-tabs .nav-link.active { font-weight: bold; border-top: 3px solid #0d6efd; color: #0d6efd; background: #fff; }
        .tab-content-area { display: none; padding-top: 20px; }
        .tab-content-area.active { display: block; animation: fadeIn 0.3s; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        
        .mermaid { background: white; padding: 0; text-align: center; } 
        #treeViewport { 
            border: 1px solid #e9ecef; background: white; border-radius: 4px; 
            min-height: 200px; position: relative; transition: all 0.3s; overflow: visible; 
        }
        .zoom-controls { position: absolute; top: 10px; right: 10px; z-index: 10; background: rgba(255,255,255,0.8); padding: 5px; border-radius: 4px; border: 1px solid #ddd; }
        .tree-collapsed { display: none !important; }
        .edgeLabel { font-size: 0.8em !important; color: #666 !important; } 
        .edgeLabel .label rect { fill: #fcfcfc !important; stroke: #e0e0e0 !important; stroke-width: 0.5px; rx: 2px; ry: 2px; }
        .clickable-node { cursor: pointer; user-select: none; border-bottom: 1px dashed #adb5bd; transition: all 0.2s; }
        .clickable-node:hover { background-color: #e9ecef; color: #0d6efd; border-bottom-color: #0d6efd; }
        .table-sm td, .table-sm th { vertical-align: middle; }
        
        .profile-col { min-width: 100px; border-left: 1px solid #dee2e6; }
        .profile-input { width: 100%; border: 1px solid transparent; text-align: center; background: transparent; padding: 2px; }
        .profile-input:hover { border-color: #e9ecef; background: #fff; }
        .profile-input:focus { border-color: #86b7fe; outline: 0; background: white; }
        .result-pass { color: #198754; font-weight: bold; background-color: #d1e7dd; }
        .result-fail { color: #dc3545; font-weight: bold; background-color: #f8d7da; }
        .sticky-col { position: sticky; left: 0; background-color: #fff; z-index: 2; border-right: 2px solid #dee2e6; }

        .project-name-input { border: none; background: transparent; font-style: italic; color: #6c757d; text-align: right; width: 300px; }
        .project-name-input:focus { outline: none; border-bottom: 1px solid #0d6efd; color: #000; }

        .comp-disabled { opacity: 0.6; filter: grayscale(100%); background-color: #f8f9fa; }
        .comp-disabled .card-header { background-color: #e9ecef; color: #6c757d; }

        /* Chat UI */
        #chat-btn { position: fixed; bottom: 20px; right: 20px; z-index: 1050; border-radius: 50%; width: 60px; height: 60px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); transition: transform 0.2s; }
        #chat-btn:hover { transform: scale(1.1); }
        #chat-panel { 
            position: fixed; bottom: 90px; right: 20px; width: 400px; height: 600px; z-index: 1050; 
            background: white; border-radius: 12px; box-shadow: 0 5px 20px rgba(0,0,0,0.2); 
            display: none; flex-direction: column; overflow: hidden; border: 1px solid #dee2e6;
        }
        .chat-header { background: #0d6efd; color: white; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; }
        .chat-body { flex: 1; padding: 15px; overflow-y: auto; background: #f8f9fa; font-size: 0.9em; }
        .chat-footer { padding: 10px; border-top: 1px solid #dee2e6; background: white; }
        .msg { margin-bottom: 10px; padding: 8px 12px; border-radius: 10px; max-width: 85%; word-wrap: break-word; }
        .msg-user { background: #e7f1ff; color: #000; align-self: flex-end; margin-left: auto; border-bottom-right-radius: 2px; }
        .msg-ai { background: #fff; border: 1px solid #e9ecef; align-self: flex-start; margin-right: auto; border-bottom-left-radius: 2px; }
        .msg-sys { font-size: 0.8em; color: #6c757d; text-align: center; margin-bottom: 15px; font-style: italic; }
        .msg-ai p { margin-bottom: 0.5rem; }
        .msg-ai pre { background: #f4f4f4; padding: 5px; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>

<div class="container-fluid" style="max-width: 1800px;">
    <div id="globalError" class="alert alert-danger d-none mb-3 shadow-sm">
        <strong>System Error:</strong> <span id="globalErrorMsg"></span>
    </div>

    <div class="d-flex justify-content-between align-items-center mb-3 border-bottom pb-2">
        <h3 class="mb-0 text-dark"><i class="bi bi-cpu text-primary"></i> Power Model Tool <span class="badge bg-success fs-6 align-middle">v8.2</span></h3>
        <div class="text-muted small d-flex align-items-center">
            <span class="me-2">Project:</span>
            <input type="text" id="projectNameInput" class="project-name-input" value="Tracker Gen 3" onchange="window.updateProjectName(this.value)">
        </div>
    </div>

    <ul class="nav nav-tabs">
        <li class="nav-item"><a class="nav-link active" onclick="window.switchTab('tab1', this)">1. Power Distribution</a></li>
        <li class="nav-item"><a class="nav-link" onclick="window.switchTab('tab2', this)">2. Component</a></li>
        <li class="nav-item"><a class="nav-link" onclick="window.switchTab('tab3', this)">3. Power Source</a></li>
        <li class="nav-item"><a class="nav-link" onclick="window.switchTab('tab4', this)">4. Connections</a></li>
        <li class="nav-item"><a class="nav-link" onclick="window.switchTab('tab5', this)">5. Use Case Mgmt</a></li>
        <li class="nav-item"><a class="nav-link" onclick="window.switchTab('tab6', this)">6. Battery Life (Matrix)</a></li>
        <li class="nav-item"><a class="nav-link" onclick="window.switchTab('tab7', this)">7. Energy Breakdown</a></li>
        <li class="nav-item"><a class="nav-link" onclick="window.switchTab('tab8', this)">8. Configuration</a></li>
    </ul>

    <div id="tabContainer">
        <div id="tab1" class="tab-content-area active">
            <div id="validationAlert" class="alert alert-danger d-none shadow-sm mb-3"><i class="bi bi-exclamation-triangle-fill me-2"></i> <span id="validationMsg"></span></div>
            <div class="context-bar d-flex justify-content-between align-items-center mb-3">
                <div class="d-flex align-items-center">
                    <label class="fw-bold me-2 text-secondary"><i class="bi bi-layers-half"></i> Scenario:</label>
                    <select class="form-select form-select-sm w-auto fw-bold text-primary use-case-select" onchange="window.switchUseCase(this.value)"></select>
                </div>
                <div class="d-flex align-items-center">
                    <span class="text-muted small me-2">Total Avg Load:</span>
                    <span class="fw-bold fs-5 text-dark" id="tab1TotalCurrent">--</span> 
                    <span class="small text-muted ms-1">uA (VSYS)</span>
                </div>
            </div>
            <div class="row">
                <div class="col-12">
                    <div class="card mb-4 shadow-sm">
                        <div class="card-header bg-light fw-bold d-flex justify-content-between align-items-center py-2">
                            <span>System Power Tree</span>
                            <div>
                                <button class="btn btn-sm btn-outline-secondary me-2" onclick="window.toggleTreeDirection()" id="btnTreeDir" title="Switch Direction"><i class="bi bi-arrow-down-up"></i> Dir: TD</button>
                                <button class="btn btn-sm btn-outline-secondary" onclick="window.toggleTreeVisibility()" id="btnToggleTree"><i class="bi bi-arrows-collapse"></i> Hide Diagram</button>
                            </div>
                        </div>
                        <div id="treeViewport">
                            <div class="zoom-controls">
                                <div class="btn-group btn-group-sm">
                                    <button class="btn btn-light border" onclick="window.zoomTree(0.1)"><i class="bi bi-plus-lg"></i></button>
                                    <button class="btn btn-light border" onclick="window.zoomTree(-0.1)"><i class="bi bi-dash-lg"></i></button>
                                    <button class="btn btn-light border" onclick="window.resetZoomTree()"><i class="bi bi-arrow-counterclockwise"></i></button>
                                </div>
                            </div>
                            <div class="mermaid" id="powerTreeDiagram">graph TD; Node[Initializing...]</div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card mb-3 border-primary h-100">
                                <div class="card-header bg-primary text-white fw-bold">Component Breakdown</div>
                                <div class="card-body p-0 table-responsive">
                                    <table class="table table-sm table-hover mb-0 text-center align-middle">
                                        <thead class="table-light"><tr><th>Component</th><th>Mode Mix</th><th>Avg Load (uA)</th><th>Avg Power (uW)</th><th>%</th></tr></thead>
                                        <tbody id="componentTableBody"></tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card h-100">
                                <div class="card-header bg-light fw-bold">Detailed Rail Analysis</div>
                                <div class="card-body p-0 table-responsive">
                                    <table class="table table-sm table-hover mb-0 text-center align-middle" style="font-size: 0.9em;">
                                        <thead class="table-light"><tr><th>Rail Name</th><th>State</th><th>Vout (V)</th><th>Eff (%)</th><th>Load (uA)</th><th>Input (uA)</th><th>Source</th></tr></thead>
                                        <tbody id="analysisTableBody"></tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="d-none"><canvas id="powerPieChart"></canvas></div>
            </div>
        </div>

        <div id="tab2" class="tab-content-area">
            <div class="d-flex justify-content-between align-items-center alert alert-info py-2 shadow-sm">
                <span><i class="bi bi-pencil"></i> Component Current Consumption (uA) & Modes</span>
                <button class="btn btn-sm btn-success shadow-sm" onclick="window.addNewComponent()"><i class="bi bi-plus-circle"></i> Add Component</button>
            </div>
            <div id="componentEditorContainer"></div>
        </div>

        <div id="tab3" class="tab-content-area">
            <div class="d-flex justify-content-between align-items-center alert alert-info py-2 shadow-sm">
                <span><i class="bi bi-lightning-fill"></i> Power Rails & Modes</span>
                <button class="btn btn-sm btn-success shadow-sm" onclick="window.addNewSource()"><i class="bi bi-plus-circle"></i> Add Power Rail</button>
            </div>
            <div id="sourceEditorContainer" class="vstack gap-3"></div>
            <div class="mt-4 p-3 bg-light border rounded">
                <label class="fw-bold text-secondary mb-1">Power Architecture Notes:</label>
                <textarea class="form-control" rows="3" id="tab3NoteInput" placeholder="e.g. PMIC I2C settings, buck regulator part numbers..." onchange="window.updateTab3Note(this.value)"></textarea>
            </div>
        </div>

        <div id="tab4" class="tab-content-area">
            <div class="alert alert-info py-2"><i class="bi bi-diagram-3"></i> Connections (Component -> Rail)</div>
            <div class="card"><div class="card-body p-0"><table class="table table-striped align-middle mb-0"><thead class="table-light"><tr><th>Component</th><th>Node Name</th><th>Connected Rail</th></tr></thead><tbody id="connectionEditorBody"></tbody></table></div></div>
            <div class="mt-4 p-3 bg-light border rounded">
                <label class="fw-bold text-secondary mb-1">Connection Notes:</label>
                <textarea class="form-control" rows="3" id="tab4NoteInput" placeholder="e.g. Power filtering requirements, dedicated LDOs..." onchange="window.updateTab4Note(this.value)"></textarea>
            </div>
        </div>

        <div id="tab5" class="tab-content-area">
            <div class="context-bar d-flex align-items-center mb-3 bg-light">
                <label class="fw-bold me-2 text-secondary"><i class="bi bi-sliders"></i> Scenario:</label>
                <select class="form-select form-select-sm w-auto fw-bold text-primary use-case-select" onchange="window.switchUseCase(this.value)"></select>
                <span class="ms-auto text-muted small"><i class="bi bi-info-circle"></i> Define active states for this scenario.</span>
            </div>
            <div class="row">
                <div class="col-md-7">
                    <div class="card shadow-sm h-100">
                        <div class="card-header bg-white fw-bold">1. Component Duty Cycles</div>
                        <div class="card-body p-0">
                            <table class="table table-hover mb-0 align-middle">
                                <thead class="table-light"><tr><th>Component</th><th>Mode Distribution</th><th style="width:100px;">Action</th></tr></thead>
                                <tbody id="ucComponentBody"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="col-md-5">
                    <div class="card shadow-sm h-100">
                        <div class="card-header bg-white fw-bold">2. Power Source Control</div>
                        <div class="card-body p-0">
                            <table class="table table-hover mb-0 align-middle">
                                <thead class="table-light"><tr><th>Rail</th><th>Mode Select</th><th>Status</th></tr></thead>
                                <tbody id="ucSourceBody"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div id="tab6" class="tab-content-area">
            <div class="card mb-3">
                <div class="card-body p-3 bg-light d-flex justify-content-between align-items-center">
                    <div>
                        <label class="fw-bold text-secondary me-2">Battery Capacity (mAh):</label>
                        <input type="number" id="batCapacity" class="form-control d-inline-block w-auto text-center fw-bold text-primary" value="64.5" onchange="window.calcDOUMatrix()">
                    </div>
                    <div>
                        <span class="text-muted small me-3"><i class="bi bi-info-circle"></i> Input: Seconds per Day</span>
                        <button class="btn btn-primary btn-sm" onclick="window.addNewProfile()"><i class="bi bi-plus-lg"></i> Add Profile</button>
                    </div>
                </div>
            </div>
            <div class="card shadow-sm">
                <div class="card-body p-0 table-responsive" style="max-height: 750px;">
                    <table class="table table-bordered table-hover mb-0 align-middle text-center" style="font-size:0.9em; table-layout: fixed;">
                        <thead class="table-light sticky-top" style="z-index: 5;" id="matrixThead"></thead>
                        <tbody id="matrixTbody"></tbody>
                        <tfoot class="table-light sticky-bottom" style="z-index: 5;" id="matrixTfoot"></tfoot>
                    </table>
                </div>
            </div>
        </div>

        <div id="tab7" class="tab-content-area">
            <div class="row">
                <div class="col-md-8 offset-md-2">
                    <div class="card shadow-sm">
                        <div class="card-header text-center fw-bold d-flex justify-content-between align-items-center">
                            <span><i class="bi bi-pie-chart-fill"></i> Daily Energy Breakdown (uWh)</span>
                            <select id="douChartProfileSelect" class="form-select form-select-sm w-auto" onchange="window.renderDouChart()"></select>
                        </div>
                        <div class="card-body">
                            <div style="height: 350px; position: relative;">
                                <canvas id="douPieChart"></canvas>
                            </div>
                            <div class="mt-4 table-responsive">
                                <table class="table table-sm table-striped table-bordered text-center align-middle mb-0">
                                    <thead class="table-light">
                                        <tr><th>Source / Component</th><th>Energy (uWh)</th><th>%</th></tr>
                                    </thead>
                                    <tbody id="douBreakdownBody"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div id="tab8" class="tab-content-area">
            <div class="row">
                <div class="col-md-6">
                    <div class="card h-100">
                        <div class="card-header fw-bold">File Management</div>
                        <div class="card-body text-center d-flex flex-column justify-content-center">
                            <p class="text-muted">Save/Load your project data.</p>
                            <div class="d-grid gap-3">
                                <button class="btn btn-outline-success" onclick="window.exportConfig()"><i class="bi bi-download"></i> Export JSON</button>
                                <div class="input-group"><input type="file" class="form-control" id="importFile" accept=".json"><button class="btn btn-outline-primary" type="button" onclick="window.importConfig()">Import</button></div>
                                <hr>
                                <button class="btn btn-outline-danger btn-sm" onclick="window.resetToFactory()"><i class="bi bi-exclamation-triangle-fill me-2"></i> Reset to Default</button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card h-100 border-info">
                        <div class="card-header fw-bold bg-info text-white"><i class="bi bi-robot"></i> Google AI Settings</div>
                        <div class="card-body">
                            <div class="mb-3">
                                <label class="form-label small fw-bold">Provider</label>
                                <select class="form-select form-select-sm" id="aiProvider" onchange="window.toggleAuthFields()">
                                    <option value="studio">AI Studio (API Key)</option>
                                    <option value="vertex">Google Cloud Vertex AI (Token)</option>
                                </select>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label small fw-bold">Model Name</label>
                                <input type="text" class="form-control form-control-sm" id="aiModel" value="gemini-1.5-pro">
                            </div>

                            <div id="field-apikey" class="mb-3">
                                <label class="form-label small fw-bold">API Key <span class="text-muted fw-normal">(for AI Studio)</span></label>
                                <input type="password" class="form-control form-control-sm" id="aiApiKey" placeholder="AIzSy...">
                            </div>

                            <div id="field-vertex" class="d-none">
                                <div class="mb-3">
                                    <label class="form-label small fw-bold">Project ID</label>
                                    <input type="text" class="form-control form-control-sm" id="gcpProjectId" placeholder="my-gcp-project-id">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label small fw-bold">Access Token <span class="text-muted fw-normal">(Run: <code>gcloud auth print-access-token</code>)</span></label>
                                    <input type="password" class="form-control form-control-sm" id="gcpToken" placeholder="ya29.a0...">
                                </div>
                                <div class="alert alert-warning py-1 small"><i class="bi bi-exclamation-triangle"></i> Requires GCP Project with Vertex AI API enabled.</div>
                            </div>

                            <div class="d-grid gap-2 mt-3">
                                <button class="btn btn-primary btn-sm" onclick="window.saveAISettings()">Save Settings</button>
                                <button class="btn btn-outline-secondary btn-sm" onclick="window.testAIConnection()" id="btnTestAI">Test Connection</button>
                            </div>
                            <div id="aiTestResult" class="mt-2 small"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<button id="chat-btn" class="btn btn-primary d-flex align-items-center justify-content-center" onclick="window.toggleChat()">
    <i class="bi bi-chat-dots-fill fs-3"></i>
</button>

<div id="chat-panel">
    <div class="chat-header">
        <strong><i class="bi bi-robot me-2"></i> Power Assistant</strong>
        <button class="btn btn-sm btn-close btn-close-white" onclick="window.toggleChat()"></button>
    </div>
    <div class="chat-body d-flex flex-column" id="chatBody">
        <div class="msg msg-sys">Welcome! Set up AI in Tab 8 (Vertex AI or AI Studio) to start.</div>
    </div>
    <div class="chat-footer">
        <div class="input-group">
            <input type="text" id="chatInput" class="form-control" placeholder="Ask about power..." onkeypress="if(event.key==='Enter') window.sendChatMessage()">
            <button class="btn btn-primary" onclick="window.sendChatMessage()"><i class="bi bi-send"></i></button>
        </div>
    </div>
</div>

<div class="modal fade" id="dutyCycleModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header"><h5 class="modal-title">Edit Duty Cycle: <span id="modalCompName" class="fw-bold text-primary"></span></h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
            <div class="modal-body"><div id="modalInputsContainer"></div><div class="d-flex justify-content-between align-items-center mt-3 pt-3 border-top"><span class="fw-bold">Total: <span id="modalTotalSum">0</span>%</span><span id="modalWarning" class="text-danger small fw-bold d-none">Total must be 100%</span></div></div>
            <div class="modal-footer"><button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button type="button" class="btn btn-primary" onclick="window.saveDutyCycle()">Save Changes</button></div>
        </div>
    </div>
</div>

<script>
window.onerror = function(msg, url, lineNo) { document.getElementById("globalError").classList.remove("d-none"); document.getElementById("globalErrorMsg").innerText = `${msg} (Line: ${lineNo})`; return false; };
function sanitizeId(str) { return 'n_' + str.replace(/[^a-zA-Z0-9]/g, '_'); }

let STATE = null;
let powerChart = null, douChart = null;
let currentEditingComp = null;
let currentZoom = 1.0;
// [v8.2] Global variable for tree direction
let currentTreeDir = 'TD';
let dutyModal = null;
let chatHistory = [];

if (typeof mermaid !== 'undefined') mermaid.initialize({ startOnLoad: true, theme: 'default', securityLevel: 'loose' });

// --- 3. POWER ENGINE (uA) ---
window.PowerEngine = {
    calculateRailDepth: function(railName, sourceMap, memo = {}) {
        if (memo[railName] !== undefined) return memo[railName];
        const src = sourceMap[railName]; if (!src || !src.input) { memo[railName] = 0; return 0; }
        return 1 + this.calculateRailDepth(src.input, sourceMap, memo);
    },
    calculate: function(data, specificUseCaseId = null) {
        const ucId = specificUseCaseId || data.currentUseCaseId;
        const uc = data.useCases[ucId];
        const sourceMap = {}; 
        
        data.sources.forEach(s => {
            const activeModeName = (uc.sources && uc.sources[s.name]) ? uc.sources[s.name] : "ON";
            let activeMode = s.modes[activeModeName];
            if (!activeMode) activeMode = { vOut: 0, iq: 0, eff: 85 }; 
            sourceMap[s.name] = { def: s, modeName: activeModeName, vOut: activeMode.vOut, iq: activeMode.iq, eff: activeMode.eff, input: s.input };
        });

        let railReport = {};
        data.sources.forEach(s => { railReport[s.name] = { loadCurrent: 0, inputCurrent: 0, state: sourceMap[s.name].modeName, connectedComponents: [] }; });

        data.connections.forEach(conn => {
            const weights = uc.components[conn.comp];
            const comp = data.components.find(c => c.name === conn.comp);
            if (comp && weights) {
                let avgNodeCurrent = 0;
                Object.keys(weights).forEach(mode => {
                    const duty = weights[mode] || 0;
                    if(duty > 0 && comp.modes[mode]) {
                        const i = comp.modes[mode][conn.node] || 0;
                        avgNodeCurrent += i * (duty / 100.0);
                    }
                });
                if(railReport[conn.rail]) {
                    railReport[conn.rail].loadCurrent += avgNodeCurrent;
                    if(avgNodeCurrent > 0) railReport[conn.rail].connectedComponents.push(conn.comp);
                }
            }
        });

        const sortedRails = data.sources.slice().sort((a, b) => this.calculateRailDepth(b.name, sourceMap) - this.calculateRailDepth(a.name, sourceMap));
        sortedRails.forEach(src => {
            const r = railReport[src.name]; const p = sourceMap[src.name]; const def = p.def;
            if (def.type === "SWITCH" && p.vOut > 0) { const parent = sourceMap[p.input]; if (parent) p.vOut = parent.vOut; }
            const Iq = parseFloat(p.iq); const Iout = r.loadCurrent; const Vout = parseFloat(p.vOut);

            if (def.type === "BATTERY") r.inputCurrent = 0;
            else if (p.modeName === "OFF") r.inputCurrent = Iq;
            else if (def.type === "LDO" || def.type === "SWITCH") r.inputCurrent = Iout + Iq;
            else {
                const inputSrc = sourceMap[p.input];
                if(inputSrc) {
                    const Vin = parseFloat(inputSrc.vOut); const Eff = parseFloat(p.eff)/100;
                    if (Vin > 0 && Eff > 0 && Vout > 0) r.inputCurrent = (Iout > 0) ? ((Vout * Iout) / (Vin * Eff)) + Iq : Iq;
                    else r.inputCurrent = Iq;
                } else r.inputCurrent = Iq;
            }
            if(p.input && railReport[p.input]) railReport[p.input].loadCurrent += r.inputCurrent;
            r.finalVout = Vout; r.activeEff = p.eff;
        });
        return { report: railReport, sorted: sortedRails.reverse(), errors: [] };
    },
    calculateComponentBreakdown: function(data, ucId) {
        const res = this.calculate(data, ucId); 
        const uc = data.useCases[ucId || data.currentUseCaseId];
        let compPower = {}, totalLoadPower = 0;
        data.components.forEach(c => compPower[c.name] = { totalMW: 0, totalmA: 0 });
        data.connections.forEach(conn => {
            const weights = uc.components[conn.comp];
            const comp = data.components.find(c => c.name === conn.comp);
            if (comp && weights) {
                let avgNodeCurrent = 0;
                Object.keys(weights).forEach(mode => { const duty = weights[mode] || 0; if (duty > 0 && comp.modes[mode]) avgNodeCurrent += (comp.modes[mode][conn.node] || 0) * (duty / 100.0); });
                const railInfo = res.report[conn.rail];
                const railVout = railInfo ? railInfo.finalVout : 0;
                if(avgNodeCurrent > 0) { const p = railVout * avgNodeCurrent; compPower[conn.comp].totalMW += p; compPower[conn.comp].totalmA += avgNodeCurrent; totalLoadPower += p; }
            }
        });
        return { byComponent: compPower, totalMW: totalLoadPower };
    }
};

// --- DATA & INIT ---
const USE_CASE_NAMES = [ 
    "On-wrist stationary, BLE connected", "On-wrist stationary, BLE connected, Inductive button active", "On-wrist, BLE very fast advertising", "Off-wrist, BLE advertising", 
    "On-wrist active, BLE connected", "Sync, BLE connected fast with payload", "Sync, BLE connected fast no payload", "Live data (steps + HR)", 
    "Incoming text notifications", "Incoming call notifications", "Alarm", "Goal celebration", "Quick View - Turn on display", 
    "Quick View - Turn on display - ECG", "Double Tap - Turn on display", "Button Press - Turn on display", "Single Tap - View stats", 
    "Reminder to move - alert", "Reminder to move - celebration", "NFC Transit Pass Only", "NFC Payment Transaction (NFC incremental without Display)", 
    "NFC Payment Transaction (Display + vibe without NFC)", "6-Axis Accel Exercise", "Inkling Incremental - logging data", "Inkling Incremental - BLE sync", 
    "Vibe feedback incremental power on inductive button press", "Touch Timeout UI active", "On-wrist active, GPS", "Lead Imp sEDA", 
    "Always On Display", "NLP cloud processing", "Display On", "SNORE DETECT", "VOICE/SOUND DETECT", "KEYWORD DETECT", "Touch LP Active"
];
const DEFAULT_DATA = {
    projectName: "Tracker Gen 3",
    components: [
        { name: "AFE", modes: { "Active": { "TX": 12000, "RX": 2000 }, "Standby": { "TX": 0, "RX": 100 }, "Off": { "TX": 0, "RX": 0 } } },
        { name: "MCU", modes: { "Active": { "Core": 10000, "1V8": 2000 }, "Sleep": { "Core": 500, "1V8": 100 }, "Off": { "Core": 0, "1V8": 0 } } },
        { name: "Display", modes: { "Active": { "DIS_OVDD": 5000, "DIS_OVSS": 5000, "DIS_AVDD": 1000 }, "Off": { "DIS_OVDD": 0, "DIS_OVSS": 0, "DIS_AVDD": 0 } } }
    ],
    sources: [
        { name: "VSYS", type: "BATTERY", input: null, eff: 100, modes: { "ON": { vOut: 3.85, iq: 0, eff: 100 } } },
        { name: "PMIC_BUCK_1V8", type: "BUCK", input: "VSYS", eff: 85, modes: { "ON": { vOut: 1.8, iq: 10, eff: 85 }, "OFF": { vOut: 0, iq: 1, eff: null } } },
        { name: "PMIC_BB", type: "BOOST", input: "VSYS", eff: 80, modes: { "ON": { vOut: 3.9, iq: 10, eff: 80 }, "OFF": { vOut: 0, iq: 1, eff: null } } },
        { name: "PMIC_LDO1", type: "LDO", input: "VSYS", eff: null, modes: { "ON": { vOut: 1.8, iq: 5, eff: null }, "OFF": { vOut: 0, iq: 1, eff: null } } },
        { name: "PMIC_LDO2", type: "LDO", input: "PMIC_BB", eff: null, modes: { "ON": { vOut: 3.5, iq: 5, eff: null }, "OFF": { vOut: 0, iq: 1, eff: null } } },
        { name: "OVDD", type: "BOOST", input: "VSYS", eff: 80, modes: { "ON": { vOut: 3.3, iq: 15, eff: 80 }, "OFF": { vOut: 0, iq: 1, eff: null } } },
        { name: "OVSS", type: "BUCK-BOOST", input: "VSYS", eff: 80, modes: { "ON": { vOut: 3.3, iq: 15, eff: 80 }, "OFF": { vOut: 0, iq: 1, eff: null } } },
        { name: "AVDD_3V3", type: "LDO", input: "VSYS", eff: null, modes: { "ON": { vOut: 3.3, iq: 5, eff: null }, "OFF": { vOut: 0, iq: 1, eff: null } } }
    ],
    connections: [
        { comp: "AFE", node: "TX", rail: "PMIC_LDO2" }, { comp: "AFE", node: "RX", rail: "PMIC_LDO1" }, 
        { comp: "MCU", node: "Core", rail: "PMIC_BUCK_1V8" }, { comp: "MCU", node: "1V8", rail: "PMIC_BUCK_1V8" },
        { comp: "Display", node: "DIS_OVDD", rail: "OVDD" }, { comp: "Display", node: "DIS_OVSS", rail: "OVSS" }, { comp: "Display", node: "DIS_AVDD", rail: "AVDD_3V3" }
    ],
    useCases: {}, profiles: [], currentUseCaseId: USE_CASE_NAMES[0]
};

USE_CASE_NAMES.forEach(name => {
    DEFAULT_DATA.useCases[name] = { components: {}, sources: {} };
    DEFAULT_DATA.components.forEach(c => DEFAULT_DATA.useCases[name].components[c.name] = { "Active": 0, "Off": 100 });
});

const PRESET_PROFILES = [
    { name: "P75 User", target: 7.0 }, { name: "P90 User", target: 9.0 },
    { name: "AOD mode", target: 2.0 }, { name: "GPS (25mins)", target: 1.4 },
    { name: "GPS (continuous)", target: 0.21 }
];
PRESET_PROFILES.forEach(p => { let w = {}; USE_CASE_NAMES.forEach(u => w[u] = 0); DEFAULT_DATA.profiles.push({ name: p.name, targetDays: p.target, weights: w }); });

STATE = JSON.parse(JSON.stringify(DEFAULT_DATA));

window.sanitizeDataStructure = function() {
    STATE.components.forEach(c => {
        if(c.enabled === undefined) c.enabled = true;
        if(!c.note) c.note = "";
        if(!c.modeNotes) c.modeNotes = {};
    });
    STATE.sources.forEach(s => { 
        if (!s.modes) s.modes = { "ON": { vOut: s.vOut, iq: s.iq, eff: s.eff }, "OFF": { vOut: 0, iq: 0.0001, eff: null } };
        else Object.keys(s.modes).forEach(m => { if (s.modes[m].eff === undefined) s.modes[m].eff = s.eff !== undefined ? s.eff : 85; });
    });
    const bat = STATE.sources.find(s => s.name === "VBAT");
    if(bat) {
        bat.name = "VSYS";
        STATE.sources.forEach(s => { if(s.input === "VBAT") s.input = "VSYS"; });
        STATE.connections.forEach(c => { if(c.rail === "VBAT") c.rail = "VSYS"; });
    }
    if (!STATE.profiles || STATE.profiles.length === 0) {
        STATE.profiles = [];
        if (STATE.userProfile && Object.keys(STATE.userProfile).length > 0) {
            STATE.profiles.push({ name: "Legacy User", targetDays: 5, weights: JSON.parse(JSON.stringify(STATE.userProfile)) });
        } else {
            PRESET_PROFILES.forEach(p => { let w={}; USE_CASE_NAMES.forEach(u=>w[u]=0); STATE.profiles.push({name:p.name, targetDays:p.target, weights:w}); });
        }
    }
    Object.keys(STATE.useCases).forEach(ucId => {
        const uc = STATE.useCases[ucId];
        Object.keys(uc.components).forEach(cName => {
            if(typeof uc.components[cName] === 'string') {
                const val = uc.components[cName]; uc.components[cName] = {}; 
                const comp = STATE.components.find(x=>x.name===cName);
                if(comp) { Object.keys(comp.modes).forEach(m=>uc.components[cName][m]=0); uc.components[cName][val]=100; }
            }
        });
        STATE.components.forEach(comp => {
            if(!comp.note) comp.note = "";
            if(!comp.modeNotes) comp.modeNotes = {};
            if (!uc.components[comp.name]) {
                uc.components[comp.name] = {};
                Object.keys(comp.modes).forEach(m => uc.components[comp.name][m] = 0);
            }
        });
        if(!uc.sources) uc.sources = {};
        STATE.sources.forEach(s => { if(!uc.sources[s.name]) uc.sources[s.name] = "ON"; });
    });
    if(typeof STATE.tab3Note === 'undefined') STATE.tab3Note = "";
    if(typeof STATE.tab4Note === 'undefined') STATE.tab4Note = "";
    if(typeof STATE.projectName === 'undefined') STATE.projectName = "Tracker Gen 3";
    document.getElementById("projectNameInput").value = STATE.projectName;
}

// --- RENDERERS ---
window.renderUseCaseSelect = function() { document.querySelectorAll('.use-case-select').forEach(s => s.innerHTML = Object.keys(STATE.useCases).map(k => `<option value="${k}" ${k===STATE.currentUseCaseId?"selected":""}>${k}</option>`).join("")); }

window.renderTab5_Controls = function(res) {
    const uc = STATE.useCases[STATE.currentUseCaseId];
    if(!uc) return;
    document.getElementById("ucComponentBody").innerHTML = STATE.components.map(c => {
        const isEnabled = (c.enabled !== false);
        const rowClass = isEnabled ? "" : "text-muted bg-light";
        const weights = uc.components[c.name];
        let summary = [];
        if(weights) Object.keys(weights).forEach(m => { if(weights[m] > 0) summary.push(`${m}: <b>${weights[m]}%</b>`); });
        const summaryHtml = summary.length > 0 ? summary.join(", ") : "<span class='text-danger'>Not Configured</span>";
        const btnHtml = isEnabled ? `<button class="btn btn-sm btn-outline-primary" onclick="window.openDutyCycleEditor('${c.name}')">Edit Duty</button>` : `<span class="badge bg-secondary">Disabled</span>`;
        return `<tr class="${rowClass}"><td class="fw-bold">${c.name}</td><td class="small text-muted">${summaryHtml}</td><td>${btnHtml}</td></tr>`;
    }).join("");

    document.getElementById("ucSourceBody").innerHTML = STATE.sources.filter(s=>s.type!=="BATTERY").map(s=>{ 
        const currentMode = (uc.sources && uc.sources[s.name]) ? uc.sources[s.name] : "ON";
        const modeOpts = Object.keys(s.modes).map(m => `<option value="${m}" ${m===currentMode?"selected":""}>${m}</option>`).join("");
        const rData = res.report[s.name];
        const vOut = rData ? rData.finalVout : 0;
        const isOff = (currentMode === "OFF" || vOut < 0.01);
        let statusBadge = isOff ? '<span class="badge bg-secondary">Inactive</span>' : `<span class="badge bg-success">Active (${vOut}V)</span>`;
        return `<tr><td>${s.name}</td><td><select class="form-select form-select-sm" onchange="STATE.useCases['${STATE.currentUseCaseId}'].sources['${s.name}']=this.value;window.refreshUI()">${modeOpts}</select></td><td>${statusBadge}</td></tr>`; 
    }).join("");
}

window.renderSourceEditor = function() {
    const c = document.getElementById("sourceEditorContainer"); c.innerHTML = ""; 
    const types = ["BUCK", "BOOST", "LDO", "SWITCH", "BUCK-BOOST"];
    STATE.sources.forEach(s => {
        let mainContent = "";
        if (s.type === "BATTERY") {
            const vOut = s.modes["ON"] ? s.modes["ON"].vOut : 3.8;
            mainContent = `<div class="row align-items-center g-2"><div class="col-md-2 fw-bold text-primary">${s.name}</div><div class="col-md-2"><span class="badge bg-secondary">BATTERY</span></div><div class="col-md-4"><div class="input-group input-group-sm"><span class="input-group-text">Voltage</span><input type="number" step="0.1" class="form-control" value="${vOut}" onchange="window.updateSourceMode('${s.name}','ON','vOut',this.value)"><span class="input-group-text">V</span></div></div><div class="col-md-4 text-muted small">Root Source</div></div>`;
        } else {
            let inputOpts = STATE.sources.filter(x => x.name !== s.name).map(x => `<option value="${x.name}" ${x.name===s.input?"selected":""}>${x.name}</option>`).join("");
            let typeOpts = types.map(t => `<option value="${t}" ${t===s.type?"selected":""}>${t}</option>`).join("");
            const isEffLocked = (s.type === 'LDO' || s.type === 'SWITCH');
            let modesHtml = `<div class="table-responsive mt-2"><table class="table table-sm table-bordered mb-0 small bg-white"><thead class="table-light"><tr><th style="width:20%">Mode</th><th>Vout (V)</th><th>Eff (%)</th><th>Iq (uA)</th><th style="width:50px"></th></tr></thead><tbody>`;
            Object.keys(s.modes).forEach(m => {
                const isFixed = (m === "ON" || m === "OFF"); const isVoutDisabled = (s.type === "SWITCH"); 
                modesHtml += `<tr><td>${m}</td><td><input type="number" step="0.1" class="form-control form-control-sm border-0 p-1" value="${s.modes[m].vOut}" ${isVoutDisabled?'disabled style="background:#e9ecef"':''} onchange="window.updateSourceMode('${s.name}','${m}','vOut',this.value)"></td><td><input type="number" step="1" class="form-control form-control-sm border-0 p-1" value="${s.modes[m].eff !== undefined && s.modes[m].eff !== null ? s.modes[m].eff : ''}" ${isEffLocked?'disabled placeholder="N/A" style="background:#e9ecef"':''} onchange="window.updateSourceMode('${s.name}','${m}','eff',this.value)"></td><td><input type="number" step="0.1" class="form-control form-control-sm border-0 p-1" value="${s.modes[m].iq}" onchange="window.updateSourceMode('${s.name}','${m}','iq',this.value)"></td><td class="text-center">${!isFixed ? `<i class="bi bi-trash text-danger" style="cursor:pointer" onclick="window.deleteSourceMode('${s.name}','${m}')"></i>` : ''}</td></tr>`;
            });
            modesHtml += `</tbody></table></div><div class="d-grid mt-1"><button class="btn btn-sm btn-light text-primary border-0" onclick="window.addNewSourceMode('${s.name}')"><i class="bi bi-plus"></i> Add Mode</button></div>`;
            mainContent = `<div class="row align-items-center g-2"><div class="col-md-2"><strong class="clickable-node text-primary" onclick="window.renameSource('${s.name}')">${s.name}</strong></div><div class="col-md-2"><select class="form-select form-select-sm" onchange="window.updateSourceGlobal('${s.name}','type',this.value)">${typeOpts}</select></div><div class="col-md-2"><div class="input-group input-group-sm"><span class="input-group-text">In</span><select class="form-select" onchange="window.updateSourceGlobal('${s.name}','input',this.value)">${inputOpts}</select></div></div><div class="col-md-4"><button class="btn btn-sm btn-outline-secondary w-100" type="button" data-bs-toggle="collapse" data-bs-target="#modes_${sanitizeId(s.name)}"><i class="bi bi-sliders"></i> Vout, Eff and Iq setting</button></div><div class="col-md-2 text-end"><button class="btn btn-sm btn-outline-danger" onclick="window.deleteSource('${s.name}')"><i class="bi bi-trash"></i></button></div><div class="col-12 collapse" id="modes_${sanitizeId(s.name)}"><div class="card card-body bg-light border-0 p-2 mt-1">${modesHtml}</div></div></div>`;
        }
        c.innerHTML += `<div class="card shadow-sm"><div class="card-body py-2">${mainContent}</div></div>`;
    });
    document.getElementById("tab3NoteInput").value = STATE.tab3Note || "";
}

window.renderComponentEditor = function() {
    const c = document.getElementById("componentEditorContainer"); c.innerHTML = "";
    STATE.components.forEach(comp => {
        const isEnabled = (comp.enabled !== false); 
        const cardClass = isEnabled ? "" : "comp-disabled";
        const checkState = isEnabled ? "checked" : "";
        
        let h = `<div class="card mb-3 shadow-sm ${cardClass}"><div class="card-header py-2 fw-bold d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center flex-grow-1">
                <div class="form-check form-switch me-2">
                    <input class="form-check-input" type="checkbox" ${checkState} onchange="window.toggleComponent('${comp.name}')">
                </div>
                <span class="clickable-node text-primary fw-bold" onclick="window.renameComponent('${comp.name}')" title="Click to Rename">${comp.name}</span>
                <input type="text" class="form-control form-control-sm ms-2" style="max-width:200px;" placeholder="Remark..." value="${comp.note || ''}" onchange="window.updateComponentNote('${comp.name}', this.value)">
            </div>
            <button class="btn btn-outline-danger btn-sm py-0" onclick="window.deleteComponent('${comp.name}')">Delete</button></div><div class="card-body p-0"><table class="table table-sm mb-0 table-bordered">`;
        
        Object.keys(comp.modes).forEach(m => {
            const delBtn = `<i class="bi bi-trash text-danger clickable-node" style="font-size:1em" onclick="window.deleteComponentMode('${comp.name}', '${m}')" title="Delete Mode"></i>`;
            h += `<tr><td class="bg-light align-middle" width="120"><span class="clickable-node fw-bold text-primary px-1" onclick="window.renameComponentMode('${comp.name}', '${m}')">${m}</span></td><td class="p-2">`;
            Object.keys(comp.modes[m]).forEach(n => {
                const noteVal = (comp.modeNotes && comp.modeNotes[m] && comp.modeNotes[m][n]) ? comp.modeNotes[m][n] : '';
                h += `<div class="d-inline-flex align-items-center me-3 mb-2 p-1 border rounded bg-white">
                        <span class="clickable-node small fw-bold me-2 px-1 text-primary" onclick="window.renameOrDeleteNode('${comp.name}', '${n}')">${n}</span>
                        <input type="number" step="0.1" value="${comp.modes[m][n]}" class="form-control form-control-sm border-0 p-0 text-end" style="width:60px" onchange="window.updateCompMode('${comp.name}','${m}','${n}',this.value)">
                        <span class="small text-muted ms-1 me-1">uA</span>
                        <input type="text" class="form-control form-control-sm border-0 p-0 ps-1 text-muted bg-light" style="width:60px; font-size:0.8em;" placeholder="Note" value="${noteVal}" onchange="window.updateCompModeNote('${comp.name}','${m}','${n}',this.value)">
                      </div>`;
            });
            h += `<button class="btn btn-sm btn-light border text-muted py-0 px-2 small" onclick="window.addNodeToComponent('${comp.name}', '${m}')">+</button></td><td class="align-middle text-center" width="40">${delBtn}</td></tr>`;
        });
        h += `</table></div><div class="card-footer p-1 text-center"><button class="btn btn-sm btn-outline-secondary border-0" onclick="window.addComponentMode('${comp.name}')"><i class="bi bi-plus-circle"></i> Add Mode</button></div></div>`;
        c.innerHTML += h;
    });
}

window.renderConnectionEditor = function(){ 
    const b=document.getElementById("connectionEditorBody"); b.innerHTML=""; 
    STATE.connections.forEach((conn,i)=>{ 
        let opts=STATE.sources.map(s=>`<option value="${s.name}" ${s.name===conn.rail?"selected":""}>${s.name}</option>`).join(""); 
        b.innerHTML+=`<tr><td><strong>${conn.comp}</strong></td><td>${conn.node}</td><td><select class="form-select form-select-sm" onchange="STATE.connections[${i}].rail=this.value;window.refreshUI()">${opts}</select></td></tr>`; 
    });
    document.getElementById("tab4NoteInput").value = STATE.tab4Note || "";
}

window.renderAnalysisTables = function(res, compRes) { 
    const cBody = document.getElementById("componentTableBody"); cBody.innerHTML = ""; 
    STATE.components.forEach(comp => { 
        if(comp.enabled === false) return; 
        const d = compRes.byComponent[comp.name]; 
        const pct = compRes.totalMW > 0 ? (d.totalMW / compRes.totalMW * 100).toFixed(1) : "0.0"; 
        const weights = STATE.useCases[STATE.currentUseCaseId].components[comp.name]; 
        let mixStr = ""; 
        if(weights) { 
            const main = Object.keys(weights).reduce((a, b) => weights[a] > weights[b] ? a : b); 
            mixStr = `${main} (${weights[main]}%)`; 
        } 
        cBody.innerHTML += `<tr><td class="fw-bold">${comp.name}</td><td><span class="badge bg-light text-dark border">${mixStr}</span></td><td>${d.totalmA.toFixed(1)}</td><td class="fw-bold text-primary">${d.totalMW.toFixed(1)}</td><td><div class="progress" style="height:15px"><div class="progress-bar bg-info" style="width:${pct}%">${pct}%</div></div></td></tr>`; 
    }); 
    const rBody = document.getElementById("analysisTableBody"); rBody.innerHTML = ""; 
    res.sorted.forEach(src => { 
        const r = res.report[src.name]; const def = STATE.sources.find(s=>s.name===src.name); 
        rBody.innerHTML += `<tr class="${(r.state==='OFF'&&r.loadCurrent>0.001)?'row-error':''}"><td class="fw-bold text-start">${src.name}</td><td><span class="badge ${r.state==='OFF'?'bg-secondary':'bg-success'}">${r.state}</span></td><td>${parseFloat(r.finalVout).toFixed(2)}</td><td>${def.modes[r.state].eff||'-'}</td><td>${r.loadCurrent.toFixed(1)}</td><td class="fw-bold text-primary">${r.inputCurrent.toFixed(1)}</td><td class="small">${def.input||"-"}</td></tr>`; 
    }); 
}

window.renderMermaidTree = function(res) { 
    if (!document.getElementById('tab1').classList.contains('active')) return; 
    const el = document.getElementById('powerTreeDiagram'); 
    if (typeof mermaid === 'undefined') { el.innerHTML = 'Mermaid not loaded'; return; } 
    if (!res) res = window.PowerEngine.calculate(STATE); 
    
    window.requestAnimationFrame(() => {
        let g = `graph ${currentTreeDir};\n`; // [v8.2] Use variable for direction
        g += 'classDef source fill:#e1f5fe,stroke:#01579b,stroke-width:2px;\n'; 
        g += 'classDef component fill:#f3e5f5,stroke:#4a148c,stroke-width:1px;\n'; 
        g += 'classDef sourceOff fill:#f0f0f0,stroke:#bdbdbd,stroke-width:2px,color:#9e9e9e;\n'; 
        g += 'classDef compOff fill:#f9f9f9,stroke:#eeeeee,stroke-width:1px,color:#bdbdbd;\n'; 
        g += 'classDef compIdle fill:#ffffff,stroke:#6610f2,stroke-width:2px,stroke-dasharray: 5 5;\n'; 
        g += 'linkStyle default stroke:#6c757d,stroke-width:1px,fill:none;\n'; 
        
        STATE.sources.forEach(s => { const sId = window.sanitizeId(s.name); const rData = res.report[s.name]; let isOff = (rData && rData.finalVout <= 0.01); const className = isOff ? 'sourceOff' : 'source'; if(s.input) { const currentVal = rData ? rData.inputCurrent : 0; const style = currentVal > 1 ? `-- ${currentVal.toFixed(0)}uA -->` : `-.->`; g += `${window.sanitizeId(s.input)} ${style} ${sId}(${s.name});\n`; } else { g += `${sId}(${s.name});\n`; } g += `class ${sId} ${className};\n`; }); 
        
        const uc = STATE.useCases[STATE.currentUseCaseId]; 
        STATE.connections.forEach(c => { 
            const compObj = STATE.components.find(x => x.name === c.comp);
            
            // [v8.2] Hide disabled components completely
            if(compObj && compObj.enabled === false) return; 

            let lineCurrent = 0; const weights = uc.components[c.comp]; const comp = STATE.components.find(x => x.name === c.comp); 
            if (weights && comp) { Object.keys(weights).forEach(mode => { if (comp.modes[mode]) lineCurrent += (comp.modes[mode][c.node] || 0) * ((weights[mode] || 0) / 100.0); }); } 
            
            const cNodeId = window.sanitizeId(c.comp + '_' + c.node); 
            const railId = window.sanitizeId(c.rail); 
            
            const compClass = lineCurrent > 0 ? 'component' : 'compIdle'; 
            const style = lineCurrent > 0 ? `-- ${lineCurrent.toFixed(0)}uA -->` : `-.->`; 
            
            g += `${railId} ${style} ${cNodeId}[${c.comp}<br>${c.node}];\n`; 
            g += `class ${cNodeId} ${compClass};\n`; 
        }); 
        el.innerHTML = g; 
        el.removeAttribute('data-processed'); 
        try { mermaid.init(undefined, el); } catch(e) {} 
    });
}

window.safeRenderPowerPie = function(r) { const cvs = document.getElementById('powerPieChart'); if (!cvs || typeof Chart === 'undefined') return; if(powerChart) powerChart.destroy(); const l=Object.keys(r.byComponent).filter(k=>r.byComponent[k].totalMW>0); powerChart = new Chart(cvs.getContext('2d'), { type: 'doughnut', data: { labels:l, datasets: [{ data:l.map(k=>r.byComponent[k].totalMW), backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796'] }] } }); }

// [v9.0] Vertex AI & Chat Functions
window.toggleAuthFields = function() {
    const provider = document.getElementById('aiProvider').value;
    if(provider === 'studio') {
        document.getElementById('field-apikey').classList.remove('d-none');
        document.getElementById('field-vertex').classList.add('d-none');
        document.getElementById('aiModel').value = 'gemini-1.5-pro';
    } else {
        document.getElementById('field-apikey').classList.add('d-none');
        document.getElementById('field-vertex').classList.remove('d-none');
        document.getElementById('aiModel').value = 'gemini-1.5-pro-001';
    }
}

window.saveAISettings = function() {
    const provider = document.getElementById('aiProvider').value;
    const model = document.getElementById('aiModel').value;
    const key = document.getElementById('aiApiKey').value;
    const pid = document.getElementById('gcpProjectId').value;
    const token = document.getElementById('gcpToken').value;
    
    try {
        localStorage.setItem('pm_ai_provider', provider);
        localStorage.setItem('pm_ai_model', model);
        if(key) localStorage.setItem('pm_ai_key', key);
        if(pid) localStorage.setItem('pm_ai_pid', pid);
        if(token) localStorage.setItem('pm_ai_token', token);
        alert("Settings Saved!");
    } catch(e) {
        alert("Warning: Settings not saved (Sandboxed).");
    }
}

window.loadAISettings = function() {
    try {
        const provider = localStorage.getItem('pm_ai_provider') || 'studio';
        const model = localStorage.getItem('pm_ai_model');
        const key = localStorage.getItem('pm_ai_key');
        const pid = localStorage.getItem('pm_ai_pid');
        
        document.getElementById('aiProvider').value = provider;
        window.toggleAuthFields();
        if(model) document.getElementById('aiModel').value = model;
        if(key) document.getElementById('aiApiKey').value = key;
        if(pid) document.getElementById('gcpProjectId').value = pid;
    } catch(e) { console.warn("LocalStorage access denied"); }
}

window.toggleChat = function() {
    const panel = document.getElementById('chat-panel');
    panel.style.display = (panel.style.display === 'flex') ? 'none' : 'flex';
}

window.getCompactState = function() {
    const s = JSON.parse(JSON.stringify(STATE));
    delete s.currentUseCaseId;
    delete s.profiles; 
    return s;
}

window.appendMessage = function(role, text) {
    const div = document.createElement('div');
    div.className = `msg msg-${role}`;
    if (role === 'ai') {
        div.innerHTML = marked.parse(text); 
    } else {
        div.innerText = text;
    }
    const body = document.getElementById('chatBody');
    body.appendChild(div);
    body.scrollTop = body.scrollHeight;
}

window.sendChatMessage = async function() {
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (!msg) return;

    window.appendMessage('user', msg);
    input.value = "";
    
    const systemPrompt = `You are an expert Power Consumption Analyst. Here is the current system configuration (JSON): ${JSON.stringify(window.getCompactState())}. Answer strictly based on this data.`;

    chatHistory.push({ role: 'user', content: msg });
    if (chatHistory.length > 10) chatHistory = chatHistory.slice(-10);

    const btn = document.querySelector('.chat-footer button');
    btn.disabled = true;
    
    try {
        const messages = [{ role: 'system', content: systemPrompt }, ...chatHistory];
        const reply = await window.callLLM(messages);
        
        window.appendMessage('ai', reply);
        chatHistory.push({ role: 'model', content: reply }); 
    } catch (e) {
        window.appendMessage('sys', "Error: " + e.message);
    } finally {
        btn.disabled = false;
    }
}

window.callLLM = async function(messages) {
    const provider = document.getElementById('aiProvider').value;
    const model = document.getElementById('aiModel').value;
    
    let url, headers, payload;

    if(provider === 'studio') {
        const key = document.getElementById('aiApiKey').value;
        if (!key) throw new Error("Missing API Key");
        url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${key}`;
        headers = { 'Content-Type': 'application/json' };
    } else {
        const pid = document.getElementById('gcpProjectId').value;
        const token = document.getElementById('gcpToken').value;
        if (!pid || !token) throw new Error("Missing Project ID or Token");
        url = `https://us-central1-aiplatform.googleapis.com/v1/projects/${pid}/locations/us-central1/publishers/google/models/${model}:generateContent`;
        headers = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` };
    }

    const contents = messages.filter(m => m.role === 'user' || m.role === 'model').map(m => ({ role: m.role, parts: [{ text: m.content }] }));
    const sysMsg = messages.find(m => m.role === 'system');
    
    payload = { contents: contents };
    if (sysMsg) payload.systemInstruction = { parts: [{ text: sysMsg.content }] };

    const response = await fetch(url, { method: 'POST', headers: headers, body: JSON.stringify(payload) });
    
    if (!response.ok) {
        const errText = await response.text();
        throw new Error(`API Error ${response.status}: ${errText}`);
    }

    const data = await response.json();
    if (data.error) throw new Error(data.error.message);
    if (!data.candidates || data.candidates.length === 0) return "(No response)";
    return data.candidates[0].content.parts[0].text;
}

window.testAIConnection = async function() {
    const btn = document.getElementById('btnTestAI');
    const resDiv = document.getElementById('aiTestResult');
    btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    resDiv.innerHTML = "";
    
    try {
        const reply = await window.callLLM([{ role: 'user', content: 'Hello' }]);
        resDiv.innerHTML = `<span class="text-success fw-bold"><i class="bi bi-check-circle"></i> ${reply}</span>`;
    } catch (e) {
        resDiv.innerHTML = `<span class="text-danger fw-bold"><i class="bi bi-x-circle"></i> ${e.message}</span>`;
    } finally {
        btn.disabled = false; btn.innerHTML = 'Test Connection';
    }
}

// --- SYSTEM & CRUD ACTIONS ---
// [v8.2] Action for direction toggle
window.toggleTreeDirection = function() {
    currentTreeDir = (currentTreeDir === 'TD') ? 'LR' : 'TD';
    const btn = document.getElementById('btnTreeDir');
    if(currentTreeDir === 'TD') {
        btn.innerHTML = '<i class="bi bi-arrow-down-up"></i> Dir: TD';
    } else {
        btn.innerHTML = '<i class="bi bi-arrow-left-right"></i> Dir: LR';
    }
    window.refreshUI(); // Trigger re-render
}

window.switchUseCase = function(id) { STATE.currentUseCaseId = id; document.querySelectorAll('.use-case-select').forEach(s => s.value = id); window.refreshUI(); }
window.switchTab = function(tabId, navElement) { 
    document.querySelectorAll('.tab-content-area').forEach(el => el.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    navElement.classList.add('active');
    if(tabId === 'tab1') window.refreshUI(); 
    if(tabId === 'tab6') window.calcDOUMatrix();
    if(tabId === 'tab7') window.renderDouChart();
}
window.exportConfig = function(){ const a=document.createElement('a'); a.href="data:text/json;charset=utf-8,"+encodeURIComponent(JSON.stringify(STATE)); a.download="config.json"; a.click(); }
window.importConfig = function(){ const f=document.getElementById('importFile').files[0]; if(f){ const r=new FileReader(); r.onload=e=>{STATE=JSON.parse(e.target.result);window.init();alert("Imported!");}; r.readAsText(f); } }
window.resetToFactory = function() { if(!confirm("Reset?")) return; STATE = JSON.parse(JSON.stringify(DEFAULT_DATA)); window.init(); }
window.zoomTree = function(delta) { currentZoom += delta; if(currentZoom < 0.2) currentZoom = 0.2; document.getElementById('powerTreeDiagram').style.transform = `scale(${currentZoom})`; }
window.resetZoomTree = function() { currentZoom = 1.0; document.getElementById('powerTreeDiagram').style.transform = `scale(1)`; }
window.toggleTreeVisibility = function() { const vp = document.getElementById('treeViewport'); const btn = document.getElementById('btnToggleTree'); if (vp.classList.contains('tree-collapsed')) { vp.classList.remove('tree-collapsed'); btn.innerHTML = '<i class="bi bi-arrows-collapse"></i> Hide Diagram'; } else { vp.classList.add('tree-collapsed'); btn.innerHTML = '<i class="bi bi-arrows-expand"></i> Show Diagram'; } }

// [v8.1] Rename Component Feature
window.renameComponent = function(oldName) {
    const newName = prompt("Rename Component:", oldName);
    if (!newName || newName === oldName) return;
    if (STATE.components.find(c => c.name === newName)) {
        alert("Name already exists!");
        return;
    }

    // 1. Update Component Definition
    const comp = STATE.components.find(c => c.name === oldName);
    comp.name = newName;

    // 2. Update Connections
    STATE.connections.forEach(conn => {
        if (conn.comp === oldName) conn.comp = newName;
    });

    // 3. Update Use Cases
    Object.values(STATE.useCases).forEach(uc => {
        if (uc.components[oldName]) {
            uc.components[newName] = uc.components[oldName];
            delete uc.components[oldName];
        }
    });

    // 4. Update UI
    window.renderComponentEditor();
    window.renderConnectionEditor();
    window.refreshUI();
}

window.addNewProfile = function() {
    const n = prompt("Profile Name:"); if (!n) return;
    let w = {}; Object.keys(STATE.useCases).forEach(uc => w[uc] = 0);
    STATE.profiles.push({ name: n, targetDays: 5, weights: w });
    window.calcDOUMatrix();
}
window.renameProfile = function(idx) { const n = prompt("Name:", STATE.profiles[idx].name); if (n) { STATE.profiles[idx].name = n; window.calcDOUMatrix(); } }
window.deleteProfile = function(idx) { if (STATE.profiles.length <= 1) return; if (!confirm("Delete?")) return; STATE.profiles.splice(idx, 1); window.calcDOUMatrix(); }
window.updateProfileTarget = function(idx, v) { STATE.profiles[idx].targetDays = parseFloat(v); window.calcDOUMatrix(); }
window.updateProfileWeight = function(idx, uc, v) { STATE.profiles[idx].weights[uc] = parseFloat(v); window.calcDOUMatrix(); }
window.updateProjectName = function(val) { STATE.projectName = val; }

window.calcDOUMatrix = function() {
    const batCap = parseFloat(document.getElementById("batCapacity").value);
    const thead = document.getElementById("matrixThead");
    const tbody = document.getElementById("matrixTbody");
    const tfoot = document.getElementById("matrixTfoot");
    const chartSelect = document.getElementById("douChartProfileSelect");

    let hRow1 = `<tr><th class="sticky-col bg-light" style="width:250px;">Use Case / Spec</th><th style="width:100px;">Avg (uA)</th>`;
    let hRow2 = `<tr><td class="sticky-col bg-light text-end fw-bold">Target (Days) <i class="bi bi-arrow-right"></i></td><td class="bg-light"></td>`;
    chartSelect.innerHTML = "";
    
    STATE.profiles.forEach((p, idx) => {
        hRow1 += `<th class="profile-col profile-header"><span class="clickable-node text-primary" onclick="window.renameProfile(${idx})">${p.name}</span><i class="bi bi-trash text-danger ms-2 clickable-node small" onclick="window.deleteProfile(${idx})"></i></th>`;
        hRow2 += `<td class="profile-col"><input type="number" step="0.1" class="form-control form-control-sm text-center fw-bold text-primary border-0" value="${p.targetDays != null ? p.targetDays : ''}" onchange="window.updateProfileTarget(${idx}, this.value)"></td>`;
        chartSelect.innerHTML += `<option value="${idx}">${p.name}</option>`;
    });
    hRow1 += `</tr>`; hRow2 += `</tr>`;
    thead.innerHTML = hRow1 + hRow2;

    const ucCurrents = {};
    Object.keys(STATE.useCases).forEach(uc => {
        ucCurrents[uc] = window.PowerEngine.calculate(STATE, uc).report["VSYS"].loadCurrent;
    });

    let bodyHtml = "";
    Object.keys(STATE.useCases).forEach(uc => {
        const i_uA = ucCurrents[uc];
        bodyHtml += `<tr><td class="sticky-col bg-light text-start small">${uc}</td><td class="bg-light small">${i_uA.toFixed(1)}</td>`;
        STATE.profiles.forEach((p, idx) => {
            const val = p.weights[uc];
            bodyHtml += `<td class="profile-col"><input type="number" class="profile-input" value="${val != null ? val : ''}" onchange="window.updateProfileWeight(${idx}, '${uc}', this.value)"></td>`;
        });
        bodyHtml += `</tr>`;
    });
    tbody.innerHTML = bodyHtml;

    let fRow1 = `<tr><td class="sticky-col bg-light text-end fw-bold">Total Duration (s)</td><td class="bg-light">-</td>`;
    let fRow2 = `<tr><td class="sticky-col bg-light text-end fw-bold">Total Energy (uAh)</td><td class="bg-light">-</td>`;
    let fRow3 = `<tr><td class="sticky-col bg-light text-end fw-bold fs-5">Est. Days</td><td class="bg-light">-</td>`;

    STATE.profiles.forEach((p, idx) => {
        let totalSec = 0, total_uAh = 0;
        Object.keys(STATE.useCases).forEach(uc => {
            const sec = p.weights[uc] || 0;
            if (sec > 0) {
                totalSec += sec;
                total_uAh += ucCurrents[uc] * (sec / 3600.0);
            }
        });
        const bat_uAh = batCap * 1000.0;
        const estDays = total_uAh > 0 ? (bat_uAh / total_uAh) : 0;
        const passClass = estDays >= p.targetDays ? "result-pass" : "result-fail";

        fRow1 += `<td class="profile-col text-muted small">${totalSec.toFixed(0)} s</td>`;
        fRow2 += `<td class="profile-col fw-bold">${total_uAh.toFixed(0)}</td>`;
        fRow3 += `<td class="profile-col ${passClass} fs-5">${estDays.toFixed(2)} d</td>`;
    });
    fRow1 += `</tr>`; fRow2 += `</tr>`; fRow3 += `</tr>`;
    tfoot.innerHTML = fRow1 + fRow2 + fRow3;

    window.renderDouChart();
}

window.calculateDailyEnergyBreakdown = function(profile) {
    let breakdown = {}; 
    STATE.components.forEach(c => {
        if (c.enabled !== false) breakdown[c.name] = 0; 
    });
    STATE.sources.forEach(s => { if(s.type !== 'BATTERY') breakdown[s.name + " (Loss+Iq)"] = 0; });

    Object.keys(STATE.useCases).forEach(ucName => {
        const duration = profile.weights[ucName] || 0;
        if (duration <= 0) return;
        const hours = duration / 3600.0;
        const res = window.PowerEngine.calculate(STATE, ucName);
        const report = res.report;
        
        STATE.connections.forEach(conn => {
            const comp = STATE.components.find(c => c.name === conn.comp);
            if (!comp || comp.enabled === false) return; 

            const weights = STATE.useCases[ucName].components[conn.comp];
            if(weights) {
                let avgI = 0; 
                Object.keys(weights).forEach(m => {
                    if(comp.modes[m]) avgI += (comp.modes[m][conn.node]||0) * ((weights[m]||0)/100.0);
                });
                const v = report[conn.rail] ? report[conn.rail].finalVout : 0;
                breakdown[conn.comp] += (v * avgI * hours); 
            }
        });

        STATE.sources.forEach(s => {
            if (s.type === 'BATTERY') return;
            const r = report[s.name];
            const pOut = r.finalVout * r.loadCurrent;
            const def = STATE.sources.find(x => x.name === s.name);
            const vIn = (report[def.input]) ? report[def.input].finalVout : 0;
            const pIn = vIn * r.inputCurrent;
            breakdown[s.name + " (Loss+Iq)"] += Math.max(0, pIn - pOut) * hours;
        });
    });
    return breakdown;
}

window.renderDouChart = function() {
    const ctx = document.getElementById('douPieChart'); if (!ctx) return;
    const profileIdx = document.getElementById("douChartProfileSelect").value || 0;
    const profile = STATE.profiles[profileIdx];
    if(!profile) return;
    
    const bd = window.calculateDailyEnergyBreakdown(profile);
    const sortedKeys = Object.keys(bd).sort((a,b) => bd[b] - bd[a]).filter(k=>bd[k]>1);
    const totalEnergy = Object.values(bd).reduce((a,b) => a+b, 0);

    const tbody = document.getElementById('douBreakdownBody');
    tbody.innerHTML = sortedKeys.map(k => {
        const val = bd[k];
        const pct = totalEnergy > 0 ? (val / totalEnergy * 100).toFixed(1) : "0.0";
        return `<tr><td class="text-start">${k}</td><td>${val.toFixed(0)}</td><td>${pct}%</td></tr>`;
    }).join("");

    if(douChart) douChart.destroy();
    if(typeof Chart !== 'undefined') {
        douChart = new Chart(ctx.getContext('2d'), { 
            type: 'doughnut', 
            data: { 
                labels: sortedKeys, 
                datasets: [{ 
                    data: sortedKeys.map(k => bd[k]), 
                    backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796', '#5a5c69', '#f8f9fc'] 
                }] 
            }, 
            options: { 
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { position: 'right' }, 
                    datalabels: {
                        formatter: (value, ctx) => {
                            let sum = 0;
                            let dataArr = ctx.chart.data.datasets[0].data;
                            dataArr.map(data => { sum += data; });
                            let percentage = (value*100 / sum).toFixed(1)+"%";
                            return percentage;
                        },
                        color: '#fff',
                        font: { weight: 'bold' }
                    }
                }
            },
            plugins: [ChartDataLabels]
        });
    }
}

// CRUD
window.addNewSourceMode = function(n){const m=prompt("Mode:");if(!m)return;const s=STATE.sources.find(x=>x.name===n);if(s.modes[m])return;s.modes[m]={vOut:0,iq:0.001,eff:85};window.refreshUI();window.renderSourceEditor();}
window.deleteSourceMode = function(n,m){if(m==="ON"||m==="OFF")return;if(!confirm("Del?"))return;delete STATE.sources.find(x=>x.name===n).modes[m];window.refreshUI();window.renderSourceEditor();}
window.updateSourceMode = function(n,m,f,v){const s=STATE.sources.find(x=>x.name===n);if(s&&s.modes[m]){s.modes[m][f]=parseFloat(v);window.refreshUI();}}
window.updateSourceGlobal = function(n,f,v){const s=STATE.sources.find(x=>x.name===n);if(s){s[f]=v;window.refreshUI();window.renderSourceEditor();}}
window.renameSource = function(o){if(o==="VSYS"){alert("No");return;}const n=prompt("Rename:",o);if(!n||n===o)return;if(STATE.sources.find(s=>s.name===n)){alert("Exists");return;}const s=STATE.sources.find(s=>s.name===o);s.name=n;STATE.sources.forEach(x=>{if(x.input===o)x.input=n});STATE.connections.forEach(x=>{if(x.rail===o)x.rail=n});Object.keys(STATE.useCases).forEach(k=>{const u=STATE.useCases[k];if(u.sources&&u.sources[o]){u.sources[n]=u.sources[o];delete u.sources[o]}});window.refreshUI();window.renderSourceEditor();window.renderConnectionEditor();}
window.addNewSource = function(){const n=prompt("Name:");if(!n)return;if(STATE.sources.find(s=>s.name===n)){alert("Exists");return;}STATE.sources.push({name:n,type:"LDO",input:"VSYS",modes:{"ON":{vOut:1.8,iq:0.01,eff:null},"OFF":{vOut:0,iq:0,eff:null}}});Object.keys(STATE.useCases).forEach(u=>{if(!STATE.useCases[u].sources)STATE.useCases[u].sources={};STATE.useCases[u].sources[n]="ON"});window.refreshUI();window.renderSourceEditor();window.renderConnectionEditor();}
window.deleteSource = function(n){if(n==="VSYS"){alert("No");return;}if(STATE.sources.find(s=>s.input===n)){alert("Dependents exist");return;}if(!confirm("Del?"))return;STATE.sources=STATE.sources.filter(s=>s.name!==n);STATE.connections.forEach(c=>{if(c.rail===n)c.rail="VSYS"});Object.keys(STATE.useCases).forEach(u=>{if(STATE.useCases[u].sources)delete STATE.useCases[u].sources[n]});window.refreshUI();window.renderSourceEditor();window.renderConnectionEditor();}
window.openDutyCycleEditor = function(compName) { currentEditingComp = compName; const uc = STATE.useCases[STATE.currentUseCaseId]; const comp = STATE.components.find(c => c.name === compName); const weights = uc.components[compName] || {}; document.getElementById("modalCompName").innerText = compName; const container = document.getElementById("modalInputsContainer"); container.innerHTML = ""; Object.keys(comp.modes).forEach(mode => { const val = weights[mode] !== undefined ? weights[mode] : 0; container.innerHTML += `<div class="row mb-2 align-items-center"><div class="col-4 text-end fw-bold">${mode}</div><div class="col-6"><input type="number" class="form-control duty-input" data-mode="${mode}" value="${val}" min="0" max="100" oninput="window.updateModalTotal()"></div><div class="col-2 text-muted">%</div></div>`; }); window.updateModalTotal(); dutyModal = new bootstrap.Modal(document.getElementById('dutyCycleModal')); dutyModal.show(); }
window.updateModalTotal = function() { let sum = 0; document.querySelectorAll('.duty-input').forEach(inp => sum += parseFloat(inp.value) || 0); const totalEl = document.getElementById("modalTotalSum"); totalEl.innerText = sum; const warn = document.getElementById("modalWarning"); if (Math.abs(sum - 100) > 0.1) { totalEl.classList.remove("text-success"); totalEl.classList.add("text-danger"); warn.classList.remove("d-none"); } else { totalEl.classList.remove("text-danger"); totalEl.classList.add("text-success"); warn.classList.add("d-none"); } }
window.saveDutyCycle = function() { const inputs = document.querySelectorAll('.duty-input'); let sum = 0; inputs.forEach(inp => sum += parseFloat(inp.value) || 0); if (Math.abs(sum - 100) > 0.1) { if(!confirm("Total is not 100%. Save anyway?")) return; } const newWeights = {}; inputs.forEach(inp => newWeights[inp.getAttribute('data-mode')] = parseFloat(inp.value) || 0); STATE.useCases[STATE.currentUseCaseId].components[currentEditingComp] = newWeights; dutyModal.hide(); window.refreshUI(); }
window.renameComponentMode = function(c,o) { const n=prompt("Rename:",o);if(!n||n===o)return;const comp=STATE.components.find(x=>x.name===c);if(comp.modes[n])return;comp.modes[n]=comp.modes[o];delete comp.modes[o]; if(comp.modeNotes && comp.modeNotes[o]) { comp.modeNotes[n]=comp.modeNotes[o]; delete comp.modeNotes[o]; } Object.keys(STATE.useCases).forEach(u=>{if(STATE.useCases[u].components[c]&&STATE.useCases[u].components[c][o]!==undefined){STATE.useCases[u].components[c][n]=STATE.useCases[u].components[c][o];delete STATE.useCases[u].components[c][o];}});window.refreshUI();window.renderComponentEditor(); }
window.addComponentMode = function(c) { const n=prompt("Name:");if(!n)return;const comp=STATE.components.find(x=>x.name===c);if(comp.modes[n])return;const first=Object.keys(comp.modes)[0];const d={};if(first)Object.keys(comp.modes[first]).forEach(k=>d[k]=0);comp.modes[n]=d;Object.keys(STATE.useCases).forEach(u=>{if(STATE.useCases[u].components[c])STATE.useCases[u].components[c][n]=0;});window.refreshUI();window.renderComponentEditor(); }
window.deleteComponentMode = function(c,m) { if(!confirm("Del?"))return;const comp=STATE.components.find(x=>x.name===c);if(Object.keys(comp.modes).length<=1)return;delete comp.modes[m];if(comp.modeNotes) delete comp.modeNotes[m]; Object.keys(STATE.useCases).forEach(u=>{if(STATE.useCases[u].components[c])delete STATE.useCases[u].components[c][m];});window.refreshUI();window.renderComponentEditor();window.renderConnectionEditor(); }
window.renameOrDeleteNode = function(c,o){const n=prompt("Edit:",o);if(n===null)return;const t=n.trim();if(t===""){if(!confirm("Del?"))return;const comp=STATE.components.find(x=>x.name===c);if(comp)Object.keys(comp.modes).forEach(m=>delete comp.modes[m][o]);STATE.connections=STATE.connections.filter(x=>!(x.comp===c&&x.node===o));}else if(t!==o){const comp=STATE.components.find(x=>x.name===c);Object.keys(comp.modes).forEach(m=>{if(comp.modes[m][o]!==undefined){comp.modes[m][t]=comp.modes[m][o];delete comp.modes[m][o]}});STATE.connections.forEach(x=>{if(x.comp===c&&x.node===o)x.node=t});}window.refreshUI();window.renderComponentEditor();window.renderConnectionEditor(); }
window.deleteComponent = function(n){if(!confirm("Del?"))return;STATE.components=STATE.components.filter(x=>x.name!==n);STATE.connections=STATE.connections.filter(x=>x.comp!==n);Object.keys(STATE.useCases).forEach(u=>{delete STATE.useCases[u].components[n]});window.refreshUI();window.renderComponentEditor();window.renderConnectionEditor();}
window.addNodeToComponent = function(c,m){const n=prompt("Node:");if(!n)return;const comp=STATE.components.find(x=>x.name===c);if(comp){Object.keys(comp.modes).forEach(x=>{if(comp.modes[x][n]===undefined)comp.modes[x][n]=0});if(!STATE.connections.find(x=>x.comp===c&&x.node===n))STATE.connections.push({comp:c,node:n,rail:"VSYS"});window.refreshUI();window.renderComponentEditor();window.renderConnectionEditor();}}
window.updateCompMode = function(c,m,n,v){ STATE.components.find(x=>x.name===c).modes[m][n]=parseFloat(v); window.refreshUI(); }
window.addNewComponent = function() { const n = prompt("Name:"); if(!n) return; if(STATE.components.find(x=>x.name===n)){alert("Exists");return;} const newComp = {name:n, enabled:true, modes:{"Active":{VDD:1},"Sleep":{VDD:0.01},"Off":{VDD:0}}, note: ""}; STATE.components.push(newComp); Object.keys(STATE.useCases).forEach(ucId => { STATE.useCases[ucId].components[n] = { "Active": 0, "Sleep": 0, "Off": 0 }; }); const r = STATE.sources.length>0 ? STATE.sources[0].name : "VSYS"; STATE.connections.push({comp:n, node:"VDD", rail:r}); window.refreshUI(); window.renderComponentEditor(); window.renderConnectionEditor(); }
window.toggleComponent = function(name) { const c = STATE.components.find(x => x.name === name); if(c) c.enabled = !c.enabled; window.refreshUI(); window.renderComponentEditor(); }

window.updateComponentNote = function(cName, val) { STATE.components.find(c => c.name === cName).note = val; }
window.updateCompModeNote = function(cName, mode, node, val) { 
    const comp = STATE.components.find(c => c.name === cName);
    if(!comp.modeNotes) comp.modeNotes = {};
    if(!comp.modeNotes[mode]) comp.modeNotes[mode] = {};
    comp.modeNotes[mode][node] = val;
}
window.updateTab3Note = function(val) { STATE.tab3Note = val; }
window.updateTab4Note = function(val) { STATE.tab4Note = val; }

window.init = function() { 
    try { 
        window.sanitizeDataStructure();
        window.renderUseCaseSelect(); 
        window.renderComponentEditor(); 
        window.renderSourceEditor(); 
        window.renderConnectionEditor(); 
        window.calcDOUMatrix(); 
        window.loadAISettings(); 
        setTimeout(() => window.refreshUI(), 100);
    } catch(e) { 
        console.error(e); 
        document.getElementById("globalError").classList.remove("d-none");
        document.getElementById("globalErrorMsg").innerText = "Init Error: " + e.message;
    } 
}

window.refreshUI = function() {
    try {
        const res = window.PowerEngine.calculate(STATE);
        const compRes = window.PowerEngine.calculateComponentBreakdown(STATE);
        window.renderTab5_Controls(res);
        window.renderAnalysisTables(res, compRes); 
        window.safeRenderPowerPie(compRes); 
        window.renderMermaidTree(res); 
        if(res.report && res.report["VSYS"]) {
            document.getElementById("tab1TotalCurrent").innerText = res.report["VSYS"].loadCurrent.toFixed(1);
        }
        if(document.getElementById("tab6").classList.contains("active")) window.calcDOUMatrix();
    } catch(e) { console.error(e); }
}

window.onload = window.init;
</script>
</body>
</html>
