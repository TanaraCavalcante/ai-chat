<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>W-Tech AI Chat</title>
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css" rel="stylesheet">
    <style>
        html, body { height: 100%; margin: 0; overflow: hidden; }
        body { display: flex; flex-direction: column; background: #f8fafc; }

        /* Navbar */
        .wtech-navbar { background: #1a2f6e; }
        .wtech-navbar img.logo { height: 36px; }

        /* Sidebar */
        #sidebar {
            width: 190px; min-width: 190px;
            background: #fff; border-right: 1px solid #e2e8f0;
            display: flex; flex-direction: column; gap: 14px;
            padding: 14px 12px; overflow-y: auto;
        }

        /* Badges */
        .badge-no-doc   { background: #fee2e2; color: #991b1b; }
        .badge-indexing { background: #fef9c3; color: #854d0e; }
        .badge-active   { background: #dcfce7; color: #166534; }

        /* Upload zone */
        .upload-zone {
            border: 2px dashed #94a3b8; border-radius: 8px;
            padding: 12px; text-align: center; cursor: pointer;
            transition: border-color .2s, background .2s;
        }
        .upload-zone:hover { border-color: #1a2f6e; background: #f0f4ff; }

        /* Indexing steps */
        .step-item { font-size: 11px; color: #94a3b8; display: flex; align-items: center; gap: 6px; }
        .step-item.active { color: #1a2f6e; font-weight: 600; }
        .step-item.done   { color: #16a34a; }

        /* Chat area */
        #chat-messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }

        /* Bubbles */
        .bubble-user { background: #1a2f6e; color: #fff; border-radius: 14px 14px 2px 14px; padding: 9px 14px; max-width: 72%; font-size: 13px; }
        .bubble-bot  { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px 14px 14px 2px; padding: 9px 14px; max-width: 72%; font-size: 13px; }

        /* Bot avatar */
        .bot-avatar {
            width: 28px; height: 28px; min-width: 28px;
            background: #1a2f6e; border: 2px solid #3a5cc5;
            border-radius: 50%; overflow: hidden;
            display: flex; align-items: center; justify-content: center;
        }
        .bot-avatar img { width: 100%; height: 100%; object-fit: contain; }
        .bot-avatar .fallback { color: #fff; font-size: 10px; font-weight: 900; display: none; }

        /* Input bar */
        #input-bar { background: #fff; border-top: 1px solid #e2e8f0; padding: 10px 14px; }
        .input-pill {
            display: flex; align-items: center; gap: 8px;
            border: 1.5px solid #dee2e6; border-radius: 24px;
            padding: 6px 8px 6px 16px; background: #fff;
        }
        #chat-input { flex: 1; border: none; outline: none; font-size: 13px; background: transparent; }
        #fonti-counter { font-size: 11px; color: #94a3b8; white-space: nowrap; font-weight: 500; }
        .btn-send {
            width: 34px; height: 34px; min-width: 34px; border-radius: 50%; border: none;
            background: #1a2f6e; color: #fff; display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: background .2s;
        }
        .btn-send:disabled { background: #e2e8f0; color: #94a3b8; cursor: default; }

        /* Ricomincia */
        #btn-ricomincia { border: 1px solid #fca5a5; background: #fff5f5; color: #ef4444; font-size: 11px; padding: 6px 10px; border-radius: 6px; cursor: pointer; }
        #btn-ricomincia:hover { background: #fee2e2; }

        /* Toast container */
        #toast-container { position: fixed; bottom: 16px; right: 16px; z-index: 9999; display: flex; flex-direction: column; gap: 8px; }
    </style>
</head>
<body>

{{-- NAVBAR --}}
<nav class="wtech-navbar d-flex align-items-center gap-2 px-3 py-2">
    <img src="{{ asset('images/logo.png') }}" alt="W-Tech" class="logo"
         onerror="this.style.display='none'">
    <div>
        <div class="text-white fw-bold" style="font-size:14px; line-height:1.2;">W-Tech AI Chat</div>
        <div class="text-white-50" style="font-size:10px; line-height:1.2;">Assistente documentale</div>
    </div>
</nav>

{{-- LAYOUT PRINCIPAL --}}
<div style="display:flex; flex:1; overflow:hidden;">

    {{-- SIDEBAR --}}
    <div id="sidebar">

        {{-- Badge stato --}}
        <div>
            <div class="text-uppercase fw-semibold mb-1" style="font-size:9px; color:#94a3b8; letter-spacing:.5px;">Stato</div>
            <span id="status-badge" class="badge-no-doc px-3 py-1 rounded-pill fw-semibold" style="font-size:10px; display:inline-block;">● Nessun documento</span>
        </div>

        {{-- Steps de indexação (oculto por defeito) --}}
        <div id="indexing-steps" style="display:none;">
            <div class="text-uppercase fw-semibold mb-1" style="font-size:9px; color:#94a3b8; letter-spacing:.5px;">Indicizzazione</div>
            <div id="filename-progress" class="fw-semibold text-primary mb-2" style="font-size:10px; word-break:break-all;"></div>
            <div class="progress mb-2" style="height:4px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated" style="width:100%; background:#1a2f6e;"></div>
            </div>
            <div style="display:flex; flex-direction:column; gap:5px;">
                <div id="step-read"  class="step-item"><i class="fa-solid fa-circle-dot fa-xs"></i> Lettura file</div>
                <div id="step-chunk" class="step-item"><i class="fa-solid fa-circle-dot fa-xs"></i> Divisione in chunk</div>
                <div id="step-embed" class="step-item"><i class="fa-solid fa-circle-dot fa-xs"></i> Generazione embeddings</div>
                <div id="step-faiss" class="step-item"><i class="fa-solid fa-circle-dot fa-xs"></i> Indicizzazione FAISS</div>
            </div>
        </div>

        {{-- Lista de documentos (oculta por defeito) --}}
        <div id="doc-list-section" style="display:none;">
            <div class="text-uppercase fw-semibold mb-1" style="font-size:9px; color:#94a3b8; letter-spacing:.5px;">Documenti</div>
            <div id="doc-list" style="display:flex; flex-direction:column; gap:6px;"></div>
        </div>

        {{-- Zona upload --}}
        <div id="upload-zone" class="upload-zone" onclick="document.getElementById('file-input').click()">
            <input type="file" id="file-input" style="display:none;" accept=".pdf,.txt,.docx,.xlsx">
            <i class="fa-solid fa-paperclip mb-1 d-block" style="font-size:18px; color:#64748b;"></i>
            <div class="fw-semibold" id="upload-label" style="font-size:11px; color:#475569;">Carica documento</div>
            <div style="font-size:9px; color:#94a3b8; margin-top:3px;">PDF · TXT · DOCX · XLSX · max 20 MB</div>
        </div>

        {{-- Ricomincia (oculto por defeito) --}}
        <button id="btn-ricomincia" style="display:none; margin-top:auto;" onclick="ricomincia()">
            <i class="fa-solid fa-rotate-left fa-xs"></i> Ricomincia
        </button>

    </div>

    {{-- CHAT AREA --}}
    <div style="flex:1; display:flex; flex-direction:column; overflow:hidden;">

        {{-- Mensagens --}}
        <div id="chat-messages">
            <div id="chat-empty" style="margin:auto; text-align:center; color:#94a3b8; font-size:13px;">
                <i class="fa-regular fa-file-lines d-block mb-2" style="font-size:30px;"></i>
                <div class="fw-semibold mb-1" style="color:#64748b;">Nessun documento caricato</div>
                Carica un documento nella barra laterale<br>per iniziare a fare domande.
            </div>
        </div>

        {{-- Input bar --}}
        <div id="input-bar">
            <div class="input-pill">
                <input type="text" id="chat-input"
                       placeholder="Carica un documento per iniziare…"
                       disabled
                       onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendMessage();}">
                <span id="fonti-counter">0 fonti</span>
                <button id="btn-send" class="btn-send" onclick="sendMessage()" disabled>
                    <i class="fa-solid fa-arrow-right fa-sm"></i>
                </button>
            </div>
        </div>

    </div>
</div>

{{-- Toast container --}}
<div id="toast-container"></div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script>
// ── Estado ────────────────────────────────────────────────────────────────────
let sessionId = null;
let docs = []; // [{name: string, chunks: number}]

// ── Init ──────────────────────────────────────────────────────────────────────
document.getElementById('file-input').addEventListener('change', function () {
    if (this.files[0]) handleFileUpload(this.files[0]);
});

// ── Atualiza a UI com base no estado atual ────────────────────────────────────
function updateUI() {
    const hasDocs = docs.length > 0;

    // Badge de estado
    const badge = document.getElementById('status-badge');
    if (hasDocs) {
        badge.className = 'badge-active px-3 py-1 rounded-pill fw-semibold';
        badge.style.display = 'inline-block';
        badge.textContent = `● ${docs.length} ${docs.length === 1 ? 'fonte attiva' : 'fonti attive'}`;
    } else {
        badge.className = 'badge-no-doc px-3 py-1 rounded-pill fw-semibold';
        badge.style.display = 'inline-block';
        badge.textContent = '● Nessun documento';
    }

    // Lista de documentos
    const listSection = document.getElementById('doc-list-section');
    const listEl = document.getElementById('doc-list');
    if (hasDocs) {
        listSection.style.display = '';
        listEl.innerHTML = docs.map(d => `
            <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:6px; padding:8px; font-size:10px;">
                <div class="fw-semibold text-truncate" style="color:#166534; max-width:150px;">
                    <i class="fa-regular fa-file fa-xs me-1"></i>${escapeHtml(d.name)}
                </div>
                <div style="color:#4ade80;">${d.chunks} chunk</div>
            </div>
        `).join('');
    } else {
        listSection.style.display = 'none';
    }

    // Label e estado da zona de upload
    document.getElementById('upload-label').textContent = hasDocs ? 'Aggiungi fonte' : 'Carica documento';
    const zone = document.getElementById('upload-zone');
    if (docs.length >= 5) {
        zone.style.opacity = '0.4';
        zone.style.pointerEvents = 'none';
    } else {
        zone.style.opacity = '1';
        zone.style.pointerEvents = '';
    }

    // Botão Ricomincia
    document.getElementById('btn-ricomincia').style.display = hasDocs ? '' : 'none';

    // Input bar
    const input = document.getElementById('chat-input');
    const btnSend = document.getElementById('btn-send');
    input.disabled = !hasDocs;
    btnSend.disabled = !hasDocs;
    input.placeholder = hasDocs ? 'Inizia a digitare…' : 'Carica un documento per iniziare…';

    // Contador de fontes
    document.getElementById('fonti-counter').textContent = `${docs.length} fonti`;

    // Empty state do chat
    const emptyEl = document.getElementById('chat-empty');
    if (emptyEl) emptyEl.style.display = hasDocs ? 'none' : '';
}

// ── Upload de documento ───────────────────────────────────────────────────────
function handleFileUpload(file) {
    if (docs.length >= 5) {
        showToast('Limite di 5 documenti per sessione raggiunto');
        document.getElementById('file-input').value = '';
        return;
    }

    // Mostrar estado de indexação
    document.getElementById('status-badge').className = 'badge-indexing px-3 py-1 rounded-pill fw-semibold';
    document.getElementById('status-badge').textContent = '⏳ Indicizzazione…';
    document.getElementById('indexing-steps').style.display = '';
    document.getElementById('upload-zone').style.display = 'none';
    document.getElementById('filename-progress').textContent = file.name;

    // Reset visual dos steps
    ['step-read', 'step-chunk', 'step-embed', 'step-faiss'].forEach(id => {
        const el = document.getElementById(id);
        el.className = 'step-item';
        el.querySelector('i').className = 'fa-solid fa-circle-dot fa-xs';
    });

    // Animação client-side dos steps (simulada com timers)
    setTimeout(() => markStepDone('step-read'), 300);
    setTimeout(() => markStepDone('step-chunk'), 900);
    setTimeout(() => markStepDone('step-embed'), 1800);
    // step-faiss é marcado quando a resposta HTTP chegar

    // Enviar ficheiro ao Laravel
    const formData = new FormData();
    formData.append('file', file);
    if (sessionId) formData.append('session_id', sessionId);
    formData.append('_token', document.querySelector('meta[name="csrf-token"]').content);

    fetch('/upload', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(data => {
            if (data.error || data.errors) {
                const msg = data.error || Object.values(data.errors).flat().join(' ');
                showToast(msg);
                resetAfterError();
                return;
            }
            // Completa o último step e actualiza o estado
            markStepDone('step-faiss');
            setTimeout(() => {
                sessionId = data.session_id;
                docs.push({ name: data.filename, chunks: data.chunks });
                document.getElementById('indexing-steps').style.display = 'none';
                document.getElementById('upload-zone').style.display = '';
                document.getElementById('file-input').value = '';
                updateUI();
            }, 500);
        })
        .catch(() => {
            showToast('Servizio non disponibile. Avvia api.py.');
            resetAfterError();
        });
}

function markStepDone(id) {
    const el = document.getElementById(id);
    el.className = 'step-item done';
    el.querySelector('i').className = 'fa-solid fa-check fa-xs';
}

function resetAfterError() {
    document.getElementById('indexing-steps').style.display = 'none';
    document.getElementById('upload-zone').style.display = '';
    document.getElementById('file-input').value = '';
    updateUI();
}

// ── Enviar mensagem ───────────────────────────────────────────────────────────
function sendMessage() {
    const input = document.getElementById('chat-input');
    const pergunta = input.value.trim();
    if (!pergunta || !sessionId) return;

    input.value = '';

    // Remove empty state se ainda estiver visível
    const emptyEl = document.getElementById('chat-empty');
    if (emptyEl) emptyEl.remove();

    appendUserBubble(pergunta);
    const spinnerId = appendSpinnerBubble();
    scrollToBottom();

    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
        },
        body: JSON.stringify({ pergunta }),
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById(spinnerId)?.remove();
        if (data.error) {
            if (data.error.includes('Sessione non trovata')) {
                showToast('Sessione scaduta. Ricarica un documento.', 'warning');
                sessionId = null;
                docs = [];
                updateUI();
            } else {
                appendBotBubble(`<em style="color:#ef4444;">${escapeHtml(data.error)}</em>`);
            }
        } else {
            appendBotBubble(escapeHtml(data.resposta).replace(/\n/g, '<br>'));
        }
        scrollToBottom();
    })
    .catch(() => {
        document.getElementById(spinnerId)?.remove();
        appendBotBubble('<em style="color:#ef4444;">Servizio non disponibile.</em>');
        scrollToBottom();
    });
}

function avatarHtml() {
    return `<div class="bot-avatar">
        <img src="/images/logo.png" alt="W"
             onerror="this.style.display='none';this.nextElementSibling.style.display='block'">
        <span class="fallback">W</span>
    </div>`;
}

function appendUserBubble(text) {
    document.getElementById('chat-messages').insertAdjacentHTML('beforeend', `
        <div style="display:flex; justify-content:flex-end;">
            <div class="bubble-user">${escapeHtml(text)}</div>
        </div>
    `);
}

function appendBotBubble(html) {
    document.getElementById('chat-messages').insertAdjacentHTML('beforeend', `
        <div style="display:flex; align-items:flex-end; gap:8px;">
            ${avatarHtml()}
            <div class="bubble-bot">${html}</div>
        </div>
    `);
}

function appendSpinnerBubble() {
    const id = 'spinner-' + Date.now();
    document.getElementById('chat-messages').insertAdjacentHTML('beforeend', `
        <div id="${id}" style="display:flex; align-items:flex-end; gap:8px;">
            ${avatarHtml()}
            <div class="bubble-bot" style="color:#94a3b8; font-style:italic; font-size:12px;">
                <span class="me-1">● ●</span> elaborazione in corso…
            </div>
        </div>
    `);
    return id;
}

function scrollToBottom() {
    const el = document.getElementById('chat-messages');
    el.scrollTop = el.scrollHeight;
}

// ── Ricomincia ────────────────────────────────────────────────────────────────
function ricomincia() {
    if (!confirm('Ricominciare? La sessione e la cronologia verranno eliminate.')) return;

    fetch('/clear', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
        },
        body: JSON.stringify({ session_id: sessionId }),
    }).finally(() => {
        sessionId = null;
        docs = [];
        document.getElementById('chat-messages').innerHTML = `
            <div id="chat-empty" style="margin:auto; text-align:center; color:#94a3b8; font-size:13px;">
                <i class="fa-regular fa-file-lines d-block mb-2" style="font-size:30px;"></i>
                <div class="fw-semibold mb-1" style="color:#64748b;">Nessun documento caricato</div>
                Carica un documento nella barra laterale<br>per iniziare a fare domande.
            </div>
        `;
        updateUI();
    });
}

// ── Toasts ────────────────────────────────────────────────────────────────────
function showToast(message, type = 'danger') {
    const id = 'toast-' + Date.now();
    document.getElementById('toast-container').insertAdjacentHTML('beforeend', `
        <div id="${id}" style="background:${type==='danger'?'#ef4444':'#f59e0b'}; color:#fff; padding:10px 14px; border-radius:8px; font-size:13px; display:flex; gap:8px; align-items:center; box-shadow:0 2px 8px rgba(0,0,0,.15);">
            <span style="flex:1;">${escapeHtml(message)}</span>
            <button onclick="document.getElementById('${id}').remove()" style="background:none;border:none;color:#fff;cursor:pointer;font-size:16px;">×</button>
        </div>
    `);
    setTimeout(() => document.getElementById(id)?.remove(), 5000);
}

// ── Utils ─────────────────────────────────────────────────────────────────────
function escapeHtml(text) {
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(text));
    return d.innerHTML;
}

// ── Boot ──────────────────────────────────────────────────────────────────────
updateUI();
</script>
</body>
</html>
