<?php
?>
<!DOCTYPE html>
<html lang="pt-BR">

<head>
    <title>Amazon CC Checker</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/css/toastr.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">

    <style>
    :root {
        --bg-primary: #06060e;
        --bg-secondary: #0c0c1a;
        --bg-card: #111126;
        --bg-elevated: #171738;
        --bg-input: #0e0e24;
        --accent: #6c5ce7;
        --accent-light: #a29bfe;
        --accent-glow: rgba(108, 92, 231, 0.15);
        --accent-strong: rgba(108, 92, 231, 0.35);
        --green: #00e676;
        --green-dim: rgba(0, 230, 118, 0.12);
        --red: #ff5252;
        --red-dim: rgba(255, 82, 82, 0.12);
        --yellow: #ffab40;
        --yellow-dim: rgba(255, 171, 64, 0.12);
        --blue: #448aff;
        --blue-dim: rgba(68, 138, 255, 0.12);
        --cyan: #18ffff;
        --text: #e8e8f0;
        --text-dim: #8888a8;
        --text-muted: #5a5a78;
        --bg-main: #0a0a1e;
        --bg-panel: #111126;
        --text-bright: #f0f0ff;
        --border: #1e1e3a;
        --border-light: #2a2a4a;
        --radius: 14px;
        --radius-sm: 10px;
        --radius-xs: 6px;
        --shadow: 0 8px 32px rgba(0,0,0,0.4);
        --shadow-sm: 0 4px 16px rgba(0,0,0,0.3);
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
        font-family: 'Inter', -apple-system, sans-serif;
        background: var(--bg-primary);
        color: var(--text);
        min-height: 100vh;
        overflow-x: hidden;
    }

    .main-container {
        max-width: 1100px;
        margin: 0 auto;
        padding: 20px 16px;
    }

    /* ── Header ── */
    .header-card {
        background: linear-gradient(145deg, var(--bg-card), var(--bg-elevated));
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 32px 28px 28px;
        margin-bottom: 24px;
        box-shadow: var(--shadow);
        position: relative;
        overflow: hidden;
    }
    .header-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--accent), var(--cyan), var(--accent-light));
    }

    .header-title {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, var(--accent-light), var(--cyan));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 4px;
    }
    .header-subtitle {
        color: var(--text-muted);
        text-align: center;
        font-size: 0.8rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-weight: 500;
        margin-bottom: 24px;
    }

    /* ── Control Buttons ── */
    .controls-row {
        display: flex;
        justify-content: center;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 16px;
    }
    .btn-ctrl {
        padding: 10px 22px;
        border-radius: 50px;
        font-weight: 600;
        font-size: 0.8rem;
        letter-spacing: 0.3px;
        text-transform: uppercase;
        border: none;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 7px;
        transition: all 0.25s cubic-bezier(.4,0,.2,1);
        position: relative;
        overflow: hidden;
    }
    .btn-ctrl:disabled { opacity: 0.4; cursor: not-allowed; transform: none !important; }
    .btn-ctrl::after {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent);
        transform: translateX(-100%);
        transition: transform 0.5s;
    }
    .btn-ctrl:hover:not(:disabled)::after { transform: translateX(100%); }

    .btn-start {
        background: linear-gradient(135deg, #00c853, #00e676);
        color: #0a2e14;
        box-shadow: 0 4px 20px rgba(0,200,83,0.25);
    }
    .btn-start:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 28px rgba(0,200,83,0.35); }
    .btn-pause {
        background: linear-gradient(135deg, #ff9100, #ffab40);
        color: #3e2800;
        box-shadow: 0 4px 20px rgba(255,145,0,0.2);
    }
    .btn-pause:hover:not(:disabled) { transform: translateY(-2px); }
    .btn-stop {
        background: linear-gradient(135deg, #ff1744, #ff5252);
        color: #fff;
        box-shadow: 0 4px 20px rgba(255,23,68,0.2);
    }
    .btn-stop:hover:not(:disabled) { transform: translateY(-2px); }
    .btn-clean-main {
        background: var(--bg-elevated);
        color: var(--text-dim);
        border: 1px solid var(--border-light);
    }
    .btn-clean-main:hover:not(:disabled) { color: var(--red); border-color: rgba(255,82,82,0.3); }
    .btn-generate {
        background: linear-gradient(135deg, #9333ea, #7c3aed);
        color: #fff;
        box-shadow: 0 4px 20px rgba(147,51,234,0.2);
    }
    .btn-generate:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 28px rgba(147,51,234,0.35); }

    /* Generator Modal */
    .gen-overlay {
        display: none;
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.7);
        backdrop-filter: blur(6px);
        z-index: 9000;
        justify-content: center;
        align-items: center;
    }
    .gen-overlay.active { display: flex; }
    .gen-modal {
        background: var(--bg-panel);
        border: 1px solid var(--border-light);
        border-radius: 16px;
        width: 440px;
        max-width: 94vw;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 24px 80px rgba(0,0,0,0.5);
        animation: genSlide 0.25s ease;
    }
    @keyframes genSlide { from { opacity: 0; transform: translateY(20px) scale(0.96); } to { opacity: 1; transform: none; } }
    .gen-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 18px 22px 14px;
        border-bottom: 1px solid var(--border-light);
    }
    .gen-header h3 {
        font-size: 1rem;
        font-weight: 700;
        color: var(--text-bright);
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .gen-close {
        background: none;
        border: none;
        color: var(--text-dim);
        font-size: 1.3rem;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 6px;
        transition: all 0.2s;
    }
    .gen-close:hover { color: var(--red); background: rgba(255,82,82,0.1); }
    .gen-body { padding: 20px 22px; }
    .gen-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
    }
    .gen-group { margin-bottom: 14px; }
    .gen-label {
        display: block;
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--accent-light);
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 5px;
    }
    .gen-input {
        width: 100%;
        padding: 10px 14px;
        background: var(--bg-main);
        border: 1px solid var(--border-light);
        border-radius: 8px;
        color: var(--text-bright);
        font-family: 'SF Mono', 'Consolas', monospace;
        font-size: 0.85rem;
        outline: none;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .gen-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
    .gen-input::placeholder { color: var(--text-dim); }
    .gen-select {
        width: 100%;
        padding: 10px 14px;
        background: var(--bg-main);
        border: 1px solid var(--border-light);
        border-radius: 8px;
        color: var(--text-bright);
        font-size: 0.82rem;
        outline: none;
        cursor: pointer;
        color-scheme: dark;
    }
    .gen-select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
    .gen-select option { background: var(--bg-panel); color: var(--text-bright); }
    .gen-tips {
        background: rgba(108,92,231,0.06);
        border: 1px solid rgba(108,92,231,0.15);
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 0.72rem;
        color: var(--text-dim);
        line-height: 1.7;
        margin-bottom: 16px;
    }
    .gen-actions {
        display: flex;
        gap: 10px;
    }
    .gen-actions .btn-ctrl { flex: 1; justify-content: center; }
    .gen-cancel {
        flex: 1;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 10px 20px;
        border-radius: 10px;
        font-weight: 700;
        font-size: 0.82rem;
        cursor: pointer;
        border: 1px solid var(--border-light);
        background: var(--bg-elevated);
        color: var(--text-dim);
        transition: all 0.2s;
    }
    .gen-cancel:hover { color: var(--red); border-color: rgba(255,82,82,0.3); }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 20px;
        border-radius: 50px;
        font-weight: 600;
        font-size: 0.82rem;
        margin-top: 12px;
        text-align: center;
    }

    /* ── Stats ── */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 12px;
        margin-bottom: 24px;
    }
    @media(max-width:768px) { .stats-grid { grid-template-columns: repeat(3, 1fr); } }

    .stat-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        padding: 16px 12px;
        text-align: center;
        transition: transform 0.2s, border-color 0.2s;
    }
    .stat-card:hover { transform: translateY(-3px); border-color: var(--border-light); }
    .stat-num {
        font-size: 1.6rem;
        font-weight: 800;
        font-variant-numeric: tabular-nums;
        line-height: 1;
        margin-bottom: 4px;
    }
    .stat-lbl {
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: var(--text-muted);
        font-weight: 600;
    }

    /* ── Card panels ── */
    .panel {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: var(--shadow-sm);
    }
    .panel-label {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: var(--text-dim);
        margin-bottom: 14px;
    }
    .panel-label i { font-size: 1rem; color: var(--accent-light); }

    /* ── API Selector ── */
    .api-row {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 18px;
        padding-bottom: 18px;
        border-bottom: 1px solid var(--border);
    }
    .api-dropdown-btn {
        background: var(--bg-input);
        color: var(--text);
        border: 1px solid var(--border-light);
        border-radius: var(--radius-xs);
        padding: 8px 14px;
        font-family: 'Inter', sans-serif;
        font-size: 0.82rem;
        font-weight: 500;
        cursor: pointer;
        transition: border-color 0.2s;
        white-space: nowrap;
        min-width: 170px;
        text-align: left;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .api-dropdown-btn:hover, .api-dropdown-btn:focus { outline: none; border-color: var(--accent); color: var(--text); background: var(--bg-input); }
    .api-dropdown-menu {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-xs);
        padding: 6px 0;
        min-width: 200px;
    }
    .api-dropdown-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 7px 14px;
        font-size: 0.82rem;
        color: var(--text);
        cursor: pointer;
        user-select: none;
    }
    .api-dropdown-item:hover { background: rgba(255,255,255,0.05); }
    .api-dropdown-item input[type=checkbox] { accent-color: var(--accent); width: 14px; height: 14px; cursor: pointer; }
    .api-check-count {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: var(--accent);
        color: #fff;
        border-radius: 10px;
        font-size: 0.65rem;
        font-weight: 700;
        min-width: 18px;
        height: 18px;
        padding: 0 5px;
        margin-left: auto;
    }

    .toggle-wrap {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .toggle-wrap label {
        font-size: 0.78rem;
        color: var(--text-dim);
        cursor: pointer;
        user-select: none;
    }
    .form-check-input:checked { background-color: var(--accent); border-color: var(--accent); }

    /* ── Cookie Section ── */
    .cookie-input-wrap {
        position: relative;
        margin-bottom: 10px;
    }
    .cookie-input {
        width: 100%;
        background: var(--bg-input);
        color: var(--text);
        border: 1px solid var(--border-light);
        border-radius: var(--radius-sm);
        padding: 14px 16px;
        font-family: 'SF Mono', Monaco, Consolas, monospace;
        font-size: 0.78rem;
        transition: border-color 0.25s, box-shadow 0.25s;
    }
    .cookie-input:focus {
        outline: none;
        border-color: var(--accent);
        box-shadow: 0 0 0 3px var(--accent-glow);
    }
    .cookie-input::placeholder { color: var(--text-muted); }

    .cookie-toolbar {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 10px;
    }

    .btn-tool {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 7px 14px;
        border-radius: 50px;
        font-size: 0.72rem;
        font-weight: 600;
        border: 1px solid var(--border-light);
        background: var(--bg-elevated);
        color: var(--text-dim);
        cursor: pointer;
        transition: all 0.2s;
        white-space: nowrap;
    }
    .btn-tool:hover { border-color: var(--accent); color: var(--accent-light); background: var(--accent-glow); }
    .btn-tool:disabled { opacity: 0.4; cursor: not-allowed; }

    .btn-tool-primary {
        background: linear-gradient(135deg, var(--accent), #5a4bd1);
        color: #fff;
        border-color: transparent;
    }
    .btn-tool-primary:hover { box-shadow: 0 4px 16px rgba(108,92,231,0.3); transform: translateY(-1px); color: #fff; }

    .btn-tool-success {
        border-color: rgba(0,230,118,0.25);
        color: var(--green);
    }
    .btn-tool-success:hover { background: var(--green-dim); border-color: rgba(0,230,118,0.4); color: var(--green); }

    .convert-select {
        background: var(--bg-input);
        color: var(--text);
        border: 1px solid var(--border-light);
        border-radius: 50px;
        padding: 7px 14px;
        font-family: 'Inter', sans-serif;
        font-size: 0.72rem;
        font-weight: 600;
        cursor: pointer;
        color-scheme: dark;
    }
    .convert-select:focus { outline: none; border-color: var(--accent); }
    .convert-select option { background: var(--bg-card); color: var(--text); }

    /* ── Multi-cookie slots ── */
    .cookie-slot-row { display:flex; align-items:center; gap:6px; margin-bottom:6px; font-size:0.72rem; color:var(--text-muted); }
    .cookie-slot-num { font-weight:600; }
    .slot-active-pill {
        display:inline-flex; align-items:center; gap:4px;
        background:rgba(34,197,94,0.15); color:#22c55e;
        border-radius:20px; padding:1px 8px; font-size:0.68rem; font-weight:600;
    }
    .extra-cookie-slot {
        margin-top:12px; padding:12px;
        border:1px solid var(--border); border-radius:10px;
        background:rgba(255,255,255,0.02);
        transition:border-color 0.2s;
    }
    .extra-cookie-slot.slot-is-active { border-color:rgba(34,197,94,0.45); }
    .btn-slot-remove {
        margin-left:auto; background:none; border:none;
        color:var(--text-muted); cursor:pointer; font-size:0.82rem; padding:2px 6px; border-radius:4px;
        transition:color 0.15s;
    }
    .btn-slot-remove:hover { color:#ef4444; }
    .slot-validate-status { font-size:0.72rem; margin-left:6px; }

    .cookie-status {
        margin-top: 10px;
        font-size: 0.78rem;
    }
    .cookie-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border-radius: 50px;
        font-size: 0.7rem;
        font-weight: 600;
        animation: fadeSlide 0.3s ease;
    }
    @keyframes fadeSlide {
        from { opacity: 0; transform: translateY(-4px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .badge-active { background: var(--green-dim); color: var(--green); border: 1px solid rgba(0,230,118,0.2); }
    .badge-expired { background: var(--red-dim); color: var(--red); border: 1px solid rgba(255,82,82,0.2); }
    .badge-warn { background: var(--yellow-dim); color: var(--yellow); border: 1px solid rgba(255,171,64,0.2); }
    .badge-info { background: var(--accent-glow); color: var(--accent-light); border: 1px solid rgba(108,92,231,0.2); }
    .badge-neutral { background: var(--bg-elevated); color: var(--text-dim); border: 1px solid var(--border-light); }

    .detect-strip {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 10px;
        padding: 10px 14px;
        border-radius: var(--radius-xs);
        background: var(--bg-primary);
        border: 1px solid var(--border);
    }
    .detect-strip .tag {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--text-dim);
    }
    .detect-strip .tag strong { color: var(--text); }

    /* ── Card list ── */
    .card-textarea {
        width: 100%;
        background: var(--bg-input);
        color: var(--text);
        border: 1px solid var(--border-light);
        border-radius: var(--radius-sm);
        padding: 14px 16px;
        font-family: 'SF Mono', Monaco, Consolas, monospace;
        font-size: 0.75rem;
        line-height: 1.6;
        resize: vertical;
        min-height: 120px;
        transition: border-color 0.25s, box-shadow 0.25s;
    }
    .card-textarea:focus {
        outline: none;
        border-color: var(--accent);
        box-shadow: 0 0 0 3px var(--accent-glow);
    }
    .card-textarea::placeholder { color: var(--text-muted); }

    /* ── Results tabs ── */
    .results-wrap {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        overflow: hidden;
        box-shadow: var(--shadow-sm);
    }

    .tab-bar {
        display: flex;
        background: var(--bg-secondary);
        border-bottom: 1px solid var(--border);
    }
    .tab-btn {
        flex: 1;
        padding: 14px 16px;
        background: transparent;
        border: none;
        color: var(--text-muted);
        font-family: 'Inter', sans-serif;
        font-size: 0.78rem;
        font-weight: 600;
        cursor: pointer;
        position: relative;
        transition: color 0.2s, background 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 7px;
    }
    .tab-btn:hover { color: var(--text-dim); background: rgba(255,255,255,0.02); }
    .tab-btn.active { color: var(--text); background: var(--bg-card); }
    .tab-count-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 20px;
        height: 20px;
        padding: 0 5px;
        border-radius: 10px;
        font-size: 0.68rem;
        font-weight: 700;
        background: rgba(255,255,255,0.08);
        color: var(--text-muted);
        transition: background 0.2s, color 0.2s;
    }
    .tab-btn.active .tab-count-badge { background: rgba(255,255,255,0.12); color: var(--text-dim); }
    .tab-btn.active::after {
        content: '';
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 2px;
        background: var(--accent);
    }

    .tab-panel { display: none; padding: 20px; }
    .tab-panel.active { display: block; }

    .action-bar {
        display: flex;
        gap: 8px;
        margin-bottom: 14px;
    }
    .btn-action {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 7px 14px;
        border-radius: var(--radius-xs);
        font-size: 0.72rem;
        font-weight: 600;
        background: var(--bg-elevated);
        border: 1px solid var(--border-light);
        color: var(--text-dim);
        cursor: pointer;
        transition: all 0.2s;
    }
    .btn-action:hover { background: var(--accent-glow); border-color: var(--accent); color: var(--accent-light); }

    .result-item {
        background: var(--bg-elevated);
        border: 1px solid var(--border);
        border-radius: var(--radius-xs);
        padding: 12px 14px;
        margin-bottom: 8px;
        font-family: 'SF Mono', Monaco, Consolas, monospace;
        font-size: 0.75rem;
        word-break: break-all;
        line-height: 1.5;
        animation: itemSlide 0.3s ease;
    }
    @keyframes itemSlide {
        from { opacity: 0; transform: translateX(-12px); }
        to { opacity: 1; transform: translateX(0); }
    }
    .result-success { border-left: 3px solid var(--green); background: var(--green-dim); }
    .result-error { border-left: 3px solid var(--red); background: var(--red-dim); }
    .result-warning { border-left: 3px solid var(--yellow); background: var(--yellow-dim); }
    .result-cc { color: var(--text-bright); font-weight: 700; }

    .loading-dot {
        width: 18px; height: 18px;
        border: 2px solid var(--border-light);
        border-top-color: var(--accent);
        border-radius: 50%;
        animation: spin 0.6s linear infinite;
        display: inline-block;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    @media (max-width: 768px) {
        .header-title { font-size: 1.5rem; }
        .main-container { padding: 12px; }
        .controls-row { gap: 6px; }
        .btn-ctrl { padding: 8px 16px; font-size: 0.72rem; }
        .cookie-toolbar {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            align-items: stretch;
            gap: 8px;
        }
        .cookie-toolbar .convert-select {
            grid-column: 1 / -1;
            width: 100%;
        }
        .cookie-toolbar .btn-tool {
            width: 100%;
            min-width: 0;
            justify-content: center;
        }
        .cookie-toolbar #btn-add-cookie,
        .cookie-toolbar .toggle-wrap {
            margin-left: 0 !important;
        }
        .cookie-toolbar .toggle-wrap {
            justify-content: center;
            min-height: 34px;
        }
        .extra-cookie-slot { min-width: 0; }
        .cookie-slot-actions {
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            width: 100%;
            gap: 8px !important;
        }
        .cookie-slot-actions .btn-tool {
            width: 100%;
            min-width: 0;
            justify-content: center;
            padding-left: 8px !important;
            padding-right: 8px !important;
        }
        .cookie-slot-actions .slot-validate-status {
            grid-column: 1 / -1;
            margin-left: 0;
        }
    }
    </style>
</head>

<body>
    <div class="main-container">

        <!-- HEADER -->
        <div class="header-card">
            <p class="header-subtitle">Amazon Multi-Region Card Checker</p>

            <div class="controls-row">
                <button class="btn-ctrl btn-start" id="chk-start">
                    <i class="fas fa-play"></i> Start
                </button>
                <button class="btn-ctrl btn-pause" id="chk-pause" disabled>
                    <i class="fas fa-pause"></i> Pause
                </button>
                <button class="btn-ctrl btn-stop" id="chk-stop" disabled>
                    <i class="fas fa-stop"></i> Stop
                </button>
                <button class="btn-ctrl btn-clean-main" id="chk-clean">
                    <i class="fas fa-rotate-right"></i> Reset
                </button>
            </div>

            <div class="text-center">
                <span class="status-pill badge bg-warning bg-opacity-25 text-warning" id="estatus">
                    <i class="fas fa-clock"></i> Waiting...
                </span>
            </div>
        </div>

        <!-- STATS -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-num" style="color:var(--green)"><span class="val-lives">0</span></div>
                <div class="stat-lbl">Approved</div>
            </div>
            <div class="stat-card">
                <div class="stat-num" style="color:var(--red)"><span class="val-dies">0</span></div>
                <div class="stat-lbl">Declined</div>
            </div>
            <div class="stat-card">
                <div class="stat-num" style="color:var(--yellow)"><span class="val-errors">0</span></div>
                <div class="stat-lbl">Errors</div>
            </div>
            <div class="stat-card">
                <div class="stat-num" style="color:var(--blue)"><span class="val-tested">0</span></div>
                <div class="stat-lbl">Tested</div>
            </div>
            <div class="stat-card">
                <div class="stat-num" style="color:var(--accent-light)"><span class="val-total">0</span></div>
                <div class="stat-lbl">Total</div>
            </div>
            <div class="stat-card">
                <div class="stat-num" style="color:var(--cyan)" id="progress-percent">0%</div>
                <div class="stat-lbl">Progress</div>
            </div>
        </div>

        <!-- CONFIG + COOKIE -->
        <div class="panel">
            <div class="api-row">
                <div class="toggle-wrap ms-auto" style="gap:16px">
                    <div class="form-check form-switch mb-0">
                        <input class="form-check-input" type="checkbox" role="switch" id="autosave-toggle" checked>
                        <label class="form-check-label" for="autosave-toggle">
                            <i class="fas fa-floppy-disk"></i> Auto-save
                        </label>
                    </div>
                    <div class="form-check form-switch mb-0">
                        <input class="form-check-input" type="checkbox" role="switch" id="removecard-toggle">
                        <label class="form-check-label" for="removecard-toggle">
                            <i class="fas fa-trash-alt"></i> Remove card
                        </label>
                    </div>
                </div>
            </div>

            <div class="panel-label"><i class="fas fa-cookie-bite"></i> Cookie</div>

            <div class="cookie-input-wrap">
                <input type="text" id="cookie-input" class="cookie-input" placeholder="Paste your Amazon cookie (any region)...">
            </div>

            <div class="cookie-toolbar">
                <button id="btn-validate-cookie" class="btn-tool btn-tool-success">
                    <i class="fas fa-shield-check"></i> Validate
                </button>
            </div>

            <div id="cookie-status" class="cookie-status"></div>
        </div>

        <!-- CARD LIST -->
        <div class="panel">
            <div class="panel-label" style="display:flex;align-items:center;justify-content:space-between">
                <span><i class="fas fa-credit-card"></i> Card List &mdash; CC|MM|YYYY|CVV</span>
                <button class="btn-ctrl btn-generate" id="btn-open-gen" style="padding:6px 14px;font-size:0.75rem;border-radius:8px">
                    <i class="fas fa-dice"></i> Generate
                </button>
            </div>
            <textarea id="lista_Cartoes" class="card-textarea" placeholder="4111111111111111|12|2027|123&#10;5200000000000007|06|2028|456"></textarea>
        </div>

        <!-- CARD GENERATOR MODAL -->
        <div class="gen-overlay" id="gen-overlay">
            <div class="gen-modal">
                <div class="gen-header">
                    <h3><i class="fas fa-credit-card"></i> Card Generator</h3>
                    <button class="gen-close" id="gen-close">&times;</button>
                </div>
                <div class="gen-body">
                    <div class="gen-group">
                        <label class="gen-label">BIN</label>
                        <input type="text" class="gen-input" id="gen-bin" placeholder="e.g. 424242 or 424242xxxxxx" maxlength="19"
                               oninput="this.value=this.value.replace(/[^0-9xX]/g,'')">
                    </div>
                    <div class="gen-row">
                        <div class="gen-group">
                            <label class="gen-label">Month</label>
                            <select class="gen-select" id="gen-month">
                                <option value="rnd">Random</option>
                                <option value="01">01 - January</option>
                                <option value="02">02 - February</option>
                                <option value="03">03 - March</option>
                                <option value="04">04 - April</option>
                                <option value="05">05 - May</option>
                                <option value="06">06 - June</option>
                                <option value="07">07 - July</option>
                                <option value="08">08 - August</option>
                                <option value="09">09 - September</option>
                                <option value="10">10 - October</option>
                                <option value="11">11 - November</option>
                                <option value="12">12 - December</option>
                            </select>
                        </div>
                        <div class="gen-group">
                            <label class="gen-label">Year</label>
                            <select class="gen-select" id="gen-year">
                                <option value="rnd">Random</option>
                                <?php for ($y = 2025; $y <= 2050; $y++) echo "<option value=\"$y\">$y</option>\n"; ?>
                            </select>
                        </div>
                    </div>
                    <div class="gen-row">
                        <div class="gen-group">
                            <label class="gen-label">CVV</label>
                            <input type="text" class="gen-input" id="gen-cvv" placeholder="Random" maxlength="4">
                        </div>
                        <div class="gen-group">
                            <label class="gen-label">Quantity</label>
                            <input type="number" class="gen-input" id="gen-qty" value="10" min="1" max="1000">
                        </div>
                    </div>
                    <div class="gen-tips">
                        Use <strong>x</strong> for random digits in BIN &bull; e.g. <code style="color:var(--accent-light)">424242xxxxxx</code><br>
                        Leave CVV empty or use <strong>x</strong> for random &bull; Max 1000 cards<br>
                        All generated cards pass Luhn validation
                    </div>
                    <div class="gen-actions">
                        <button class="btn-ctrl btn-generate" id="gen-submit">
                            <i class="fas fa-dice"></i> Generate
                        </button>
                        <button class="gen-cancel" id="gen-cancel">
                            <i class="fas fa-xmark"></i> Cancel
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- RESULTS -->
        <div class="results-wrap">
            <div class="tab-bar">
                <button class="tab-btn active" data-tab="lives">
                    <i class="fas fa-check-circle" style="color:var(--green)"></i>
                    Approved <span class="tab-count-badge val-lives">0</span>
                </button>
                <button class="tab-btn" data-tab="dies">
                    <i class="fas fa-times-circle" style="color:var(--red)"></i>
                    Declined <span class="tab-count-badge val-dies">0</span>
                </button>
                <button class="tab-btn" data-tab="errors">
                    <i class="fas fa-triangle-exclamation" style="color:var(--yellow)"></i>
                    Errors <span class="tab-count-badge val-errors">0</span>
                </button>
            </div>

            <div class="tab-panel active" id="panel-lives">
                <div class="action-bar">
                    <button class="btn-action" id="copy-lives"><i class="fas fa-copy"></i> Copy</button>
                    <button class="btn-action" id="clear-lives"><i class="fas fa-trash"></i> Clear</button>
                    <button class="btn-action" id="download-lives"><i class="fas fa-download"></i> Download</button>
                </div>
                <div id="lives-results"></div>
            </div>
            <div class="tab-panel" id="panel-dies">
                <div class="action-bar">
                    <button class="btn-action" id="clear-dies"><i class="fas fa-trash"></i> Clear</button>
                </div>
                <div id="dies-results"></div>
            </div>
            <div class="tab-panel" id="panel-errors">
                <div class="action-bar">
                    <button class="btn-action" id="clear-errors"><i class="fas fa-trash"></i> Clear</button>
                </div>
                <div id="errors-results"></div>
            </div>
        </div>

    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.0/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/js/toastr.min.js"></script>

    <script>
    toastr.options = {
        closeButton: true, newestOnTop: true, progressBar: true,
        positionClass: "toast-top-right", timeOut: "4000",
        showEasing: "swing", hideEasing: "linear",
        showMethod: "fadeIn", hideMethod: "fadeOut"
    };

    // ── Tabs ──
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('panel-' + btn.dataset.tab).classList.add('active');
        });
    });

    $(document).ready(function() {
        // ── Auto-save toggle ──
        const savedAutoSave = localStorage.getItem('jp_amz_autosave');
        const autoSaveOn = savedAutoSave !== '0';
        $('#autosave-toggle').prop('checked', autoSaveOn);

        function isAutoSave() { return $('#autosave-toggle').is(':checked'); }

        $('#autosave-toggle').on('change', function() {
            const on = $(this).is(':checked');
            localStorage.setItem('jp_amz_autosave', on ? '1' : '0');
            if (!on) {
                localStorage.removeItem('jp_amz_cookie');
                localStorage.removeItem('jp_amz_lista');
                toastr.info('Auto-save disabled — saved data cleared');
            } else {
                localStorage.setItem('jp_amz_cookie', $('#cookie-input').val().trim());
                localStorage.setItem('jp_amz_lista', $('#lista_Cartoes').val().trim());
                toastr.info('Auto-save enabled');
            }
        });

        // ── Restore saved state ──
        if (autoSaveOn) {
            const _ck = localStorage.getItem('jp_amz_cookie');
            if (_ck) $('#cookie-input').val(_ck);
            const _ls = localStorage.getItem('jp_amz_lista');
            if (_ls) $('#lista_Cartoes').val(_ls);
        }
        const _rm = localStorage.getItem('jp_amz_removecard');
        if (_rm === '1') $('#removecard-toggle').prop('checked', true);

        $('#removecard-toggle').on('change', function() {
            localStorage.setItem('jp_amz_removecard', $(this).is(':checked') ? '1' : '0');
        });
        $('#cookie-input').on('input', function() {
            if (!isAutoSave()) return;
            const v = $(this).val().trim();
            if (v) localStorage.setItem('jp_amz_cookie', v);
            else localStorage.removeItem('jp_amz_cookie');
        });
        $('#lista_Cartoes').on('input', function() {
            if (!isAutoSave()) return;
            const v = $(this).val().trim();
            if (v) localStorage.setItem('jp_amz_lista', v);
            else localStorage.removeItem('jp_amz_lista');
        });

        // ── Validate Cookie ──
        $('#btn-validate-cookie').on('click', function() {
            const ck = $('#cookie-input').val().trim();
            if (!ck) { toastr.warning('Paste a cookie first'); return; }
            const $btn = $(this);
            $btn.prop('disabled', true).html('<span class="loading-dot" style="width:14px;height:14px;border-width:1.5px"></span> Validating...');
            $('#cookie-status').html('<span class="cookie-badge badge-info"><span class="loading-dot" style="width:14px;height:14px;border-width:1.5px"></span> Validating session...</span>');

            const api = 'cookietools.php';
            $.ajax({
                url: api,
                method: 'GET',
                data: { action: 'validate', cookie: ck },
                dataType: 'json',
                success: function(res) {
                    const map = {
                        active:  { cls: 'badge-active',  icon: 'fa-check-circle',        label: 'ACTIVE' },
                        expired: { cls: 'badge-expired', icon: 'fa-circle-xmark',         label: 'EXPIRED' },
                        blocked: { cls: 'badge-warn',    icon: 'fa-robot',                label: 'BLOCKED' },
                        ratelimit:{ cls:'badge-warn',    icon: 'fa-clock',                label: 'RATE LIMITED' },
                        error:   { cls: 'badge-expired', icon: 'fa-circle-exclamation',   label: 'ERROR' },
                        unknown: { cls: 'badge-warn',    icon: 'fa-question',             label: 'UNKNOWN' },
                    };
                    const s = map[res.status] || map.unknown;
                    let html = '<span class="cookie-badge ' + s.cls + '"><i class="fas ' + s.icon + '"></i> ' + s.label + ' &mdash; ' + res.msg + '</span>';
                    if (res.domain) html += ' <span class="cookie-badge badge-neutral">' + res.domain + '</span>';
                    $('#cookie-status').html(html);

                    if (res.status === 'active') toastr.success(res.msg);
                    else if (res.status === 'expired' || res.status === 'error') toastr.error(res.msg);
                    else toastr.warning(res.msg);
                },
                error: function() {
                    $('#cookie-status').html('<span class="cookie-badge badge-expired"><i class="fas fa-xmark"></i> Request failed</span>');
                    toastr.error('Validation failed');
                },
                complete: function() {
                    $btn.prop('disabled', false).html('<i class="fas fa-shield-check"></i> Validate');
                }
            });
        });

        // ── Card Generator ──
        function isValidLuhn(num) {
            const digits = num.replace(/\D/g, '').split('').map(Number);
            let sum = 0, alt = false;
            for (let i = digits.length - 1; i >= 0; i--) {
                let d = digits[i];
                if (alt) { d *= 2; if (d > 9) d -= 9; }
                sum += d;
                alt = !alt;
            }
            return sum % 10 === 0;
        }

        function luhnCheckDigit(partial) {
            const digits = (partial + '0').split('').map(Number);
            let sum = 0;
            for (let i = digits.length - 1; i >= 0; i--) {
                let d = digits[i];
                const posFromRight = digits.length - 1 - i;
                if (posFromRight % 2 === 1) { d *= 2; if (d > 9) d -= 9; }
                sum += d;
            }
            return (10 - (sum % 10)) % 10;
        }

        function generateCards() {
            const bin = $('#gen-bin').val().trim().replace(/[^0-9xX]/g, '');
            if (!bin) { toastr.error('Enter a BIN'); return; }

            const monthVal  = $('#gen-month').val();
            const yearVal   = $('#gen-year').val();
            const cvvInput  = $('#gen-cvv').val().trim();
            let qty = parseInt($('#gen-qty').val()) || 10;
            if (qty < 1) qty = 1;
            if (qty > 1000) qty = 1000;

            const binPrefix = bin.replace(/[xX]/g, '0');
            const isAmex   = /^3[47]/.test(binPrefix);
            const cardLen  = isAmex ? 15 : 16;
            const cvvLen   = isAmex ? 4  : 3;

            let binFmt = bin.toLowerCase();
            if (binFmt.length < cardLen) binFmt += 'x'.repeat(cardLen - binFmt.length);
            else if (binFmt.length > cardLen) binFmt = binFmt.slice(0, cardLen);

            const template = binFmt.slice(0, cardLen - 1);

            const cards    = [];
            const seen     = new Set();
            const curYear  = new Date().getFullYear();
            const maxYear  = 2050;
            let attempts   = 0;

            while (cards.length < qty && attempts < qty * 30) {
                attempts++;
                const partial    = template.replace(/x/g, () => Math.floor(Math.random() * 10));
                const checkDigit = luhnCheckDigit(partial);
                const cc         = partial + checkDigit;

                const mm = monthVal === 'rnd'
                    ? String(Math.floor(Math.random() * 12) + 1).padStart(2, '0')
                    : monthVal;

                const yy = yearVal === 'rnd'
                    ? String(Math.floor(Math.random() * (maxYear - curYear + 1)) + curYear)
                    : yearVal;

                let cvv;
                if (!cvvInput || /x/i.test(cvvInput)) {
                    cvv = String(Math.floor(Math.random() * Math.pow(10, cvvLen))).padStart(cvvLen, '0');
                } else {
                    cvv = cvvInput.replace(/\D/g, '').slice(0, cvvLen).padEnd(cvvLen, '0');
                }

                const line = cc + '|' + mm + '|' + yy + '|' + cvv;
                if (!seen.has(line)) { seen.add(line); cards.push(line); }
            }

            const ta  = $('#lista_Cartoes');
            const cur = ta.val().trim();
            ta.val(cur ? cur + '\n' + cards.join('\n') : cards.join('\n')).trigger('input');
            $('#gen-overlay').removeClass('active');
            toastr.success('Generated ' + cards.length + ' Luhn-valid cards');
        }

        $('#btn-open-gen').on('click', function() {
            $('#gen-overlay').addClass('active');
            $('#gen-bin').focus();
        });
        $('#gen-close, #gen-cancel').on('click', function() {
            $('#gen-overlay').removeClass('active');
        });
        $('#gen-overlay').on('click', function(e) {
            if (e.target === this) $(this).removeClass('active');
        });
        $('#gen-submit').on('click', generateCards);
        $('#gen-bin').on('keypress', function(e) { if (e.key === 'Enter') { e.preventDefault(); generateCards(); } });

        // ── Generator field persistence (always on, ignores auto-save toggle) ──
        const GEN_STORE_KEY = 'gen_last_inputs';
        function saveGenInputs() {
            try { localStorage.setItem(GEN_STORE_KEY, JSON.stringify({ bin:$('#gen-bin').val(), month:$('#gen-month').val(), year:$('#gen-year').val(), cvv:$('#gen-cvv').val(), qty:$('#gen-qty').val() })); } catch(e) {}
        }
        function restoreGenInputs() {
            try { const d = JSON.parse(localStorage.getItem(GEN_STORE_KEY)); if (!d) return; if (d.bin) $('#gen-bin').val(d.bin); if (d.month) $('#gen-month').val(d.month); if (d.year) $('#gen-year').val(d.year); if (d.cvv) $('#gen-cvv').val(d.cvv); if (d.qty) $('#gen-qty').val(d.qty); } catch(e) {}
        }
        $('#gen-bin, #gen-cvv, #gen-qty').on('input', saveGenInputs);
        $('#gen-month, #gen-year').on('change', saveGenInputs);
        restoreGenInputs();

        // ── Checker logic ──
        let total = 0, tested = 0, dispatched = 0, lives = 0, dies = 0, errors = 0;
        let stopped = true, paused = false;
        let livesData = [], diesData = [], errorsData = [];
        const audio = new Audio('live.wav');

        let _remainingLines = [];
        function removeLinha() {
            _remainingLines.shift();
            // batch-update the textarea every 5 results instead of every card (O(n) → O(1) per card)
            if (tested % 5 === 0 || _remainingLines.length === 0) {
                $("#lista_Cartoes").val(_remainingLines.join('\n'));
            }
        }

        function atualizarStats() {
            $(".val-total").text(total);
            $(".val-lives").text(lives);
            $(".val-dies").text(dies);
            $(".val-errors").text(errors);
            $(".val-tested").text(tested);
            const pct = total > 0 ? Math.round((tested / total) * 100) : 0;
            $("#progress-percent").text(pct + "%");
            $("#header-progress-bar").css('width', pct + '%');
        }

        function adicionarResultado(tipo, conteudo, resposta) {
            const ccPart = conteudo ? '<span class="result-cc">' + conteudo + '</span> ' : '';
            const full = ccPart + resposta;
            if (tipo === 'success') {
                consecutiveErrors = 0;
                $("#lives-results .result-empty").remove();
                $("#lives-results").prepend('<div class="result-item result-success">' + full + '</div>');
                livesData.unshift(conteudo + " -> " + resposta);
                lives++;
            } else if (tipo === 'error') {
                consecutiveErrors = 0;
                $("#dies-results .result-empty").remove();
                $("#dies-results").prepend('<div class="result-item result-error">' + full + '</div>');
                diesData.unshift(conteudo + " -> " + resposta);
                dies++;
            } else {
                consecutiveErrors++;
                $("#errors-results .result-empty").remove();
                $("#errors-results").prepend('<div class="result-item result-warning">' + full + '</div>');
                errorsData.unshift(conteudo + " -> " + resposta);
                errors++;
            }
            atualizarStats();
        }

        // ── Auto-stop ──
        const MAX_ERRORS = 5;
        let consecutiveErrors = 0;
        let inFlight = [];
        function abortInFlight() { inFlight.forEach(function(x){ try{x.abort();}catch(e){} }); inFlight = []; }
        function autoStopIfTooManyErrors() {
            // only hard-stop when consecutive errors exceed threshold AND no more cookies to try
            if (consecutiveErrors < MAX_ERRORS) return false;
            const slots = getAllCookieSlots();
            if (activeCookieIdx < slots.length - 1) return false; // more cookies available — let rotation handle it
            stopped = true; abortInFlight();
            $("#chk-start, #chk-clean").removeAttr('disabled');
            $("#chk-stop, #chk-pause").attr("disabled", true);
            $("#estatus").attr("class", "status-pill badge bg-danger bg-opacity-25 text-danger")
                .html('<i class="fas fa-stop"></i> Stopped — too many errors (' + consecutiveErrors + ')');
            toastr.warning('Auto-stopped after ' + consecutiveErrors + ' consecutive errors');
            return true;
        }

        // ── Multi-cookie slot management ──
        let activeCookieIdx = 0, cookieRotating = false;
        function getAllCookieSlots() {
            const slots = [$('#cookie-input').val().trim()];
            $('#extra-cookie-slots .extra-slot-input').each(function(){ const v=$(this).val().trim(); if(v) slots.push(v); });
            return slots.filter(Boolean);
        }
        function getActiveCookie() { const s=getAllCookieSlots(); return s[activeCookieIdx]||s[0]||''; }
        function updateCookieActiveUI() {
            const total = getAllCookieSlots().length;
            if (total > 1) {
                $('#slot0-header').css('display','flex');
                $('#slot0-active-pill').toggle(activeCookieIdx===0);
            } else { $('#slot0-header').hide(); }
            $('#extra-cookie-slots .extra-cookie-slot').each(function(i){
                const isA=(i+1)===activeCookieIdx;
                $(this).toggleClass('slot-is-active',isA);
                $(this).find('.slot-active-pill').toggle(isA);
            });
        }
        // Cookie error patterns → trigger rotation check
        function maybeRotateCookie(){
            if (cookieRotating) return;
            cookieRotating=true;
            const slots=getAllCookieSlots();
            const ck=slots[activeCookieIdx];
            $.ajax({url:'cookietools.php',method:'GET',data:{action:'validate',cookie:ck},dataType:'json',
                success:function(res){
                    if (!res||res.status!=='active'){
                        const oldNum=activeCookieIdx+1;
                        if (activeCookieIdx<slots.length-1){
                            activeCookieIdx++;
                            consecutiveErrors=0; // fresh cookie — reset error streak
                            updateCookieActiveUI();
                            adicionarResultado('warning','','⟳ Cookie '+oldNum+' expired — rotated to Cookie '+(activeCookieIdx+1));
                            toastr.warning('Cookie rotated → Cookie '+(activeCookieIdx+1),'',{timeOut:4000});
                        } else {
                            stopped=true;
                            abortInFlight();
                            adicionarResultado('warning','','⛔ Cookie '+oldNum+' expired — no more cookies, checker stopped');
                            toastr.error('All cookies expired — checker stopped','',{timeOut:6000});
                            $("#estatus").attr("class","status-pill badge bg-danger bg-opacity-25 text-danger")
                                .html('<i class="fas fa-circle-xmark"></i> All cookies expired');
                            $("#chk-start,#chk-clean").removeAttr('disabled');
                            $("#chk-stop,#chk-pause").attr("disabled",true);
                        }
                    }
                    // if cookie is still active — just continue, false alarm
                },
                complete:function(){cookieRotating=false;}
            });
        }

        // ── Parallel worker-pool engine ──
        let activeWorkers = 0, lista_ref = [];
        function getSelectedApis() {
            return ['api.php'];
        }
        function finishRun() {
            $("#estatus").attr("class","status-pill badge bg-success bg-opacity-25 text-success").html('<i class="fas fa-check"></i> Complete!');
            toastr.success('All '+total+' cards tested');
            $("#chk-start, #chk-clean").removeAttr('disabled');
            $("#chk-stop, #chk-pause").attr("disabled",true);
        }
        function runWorker(apiUrl) {
            if (stopped||paused){activeWorkers--;return;}
            if (dispatched>=total){
                activeWorkers--;
                if (activeWorkers<=0&&tested>=total) finishRun();
                return;
            }
            const conteudo=lista_ref[dispatched]; dispatched++;
            const cookie=getActiveCookie();
            const removeCardFlag=$('#removecard-toggle').is(':checked')?'1':'0';
            const apiLabel='['+apiUrl.replace('.php','').toUpperCase()+']';
            const jqx=$.ajax({
                url:apiUrl,
                type:'POST',
                contentType:'application/json',
                dataType:'json',
                data:JSON.stringify({card:conteudo,cookie:cookie})
            })
            .done(function(res){
                if (stopped) return;
                res = res || {};
                if (res.success === true){
                    const info = res.card_info ? (' • '+res.card_info) : '';
                    adicionarResultado('success',conteudo,apiLabel+' Aprovada ✓ '+((res.response||'')+info));
                    audio.play().catch(()=>{});
                    $("#estatus").attr("class","status-pill badge bg-success bg-opacity-25 text-success").html('<i class="fas fa-check"></i> Approved: '+conteudo);
                } else if (res.status === true && res.success === false){
                    adicionarResultado('error',conteudo,apiLabel+' Reprovada ✗ '+(res.response||''));
                } else {
                    const msg = res.message || res.response || 'Unknown error';
                    adicionarResultado('warning',conteudo,apiLabel+' Erros: '+msg);
                    maybeRotateCookie();
                }
            })
            .fail(function(xhr,status){
                if (stopped||status==='abort') return;
                let detail = status;
                if (xhr && xhr.responseText) {
                    try {
                        const j = JSON.parse(xhr.responseText);
                        detail = j.message || j.error || detail;
                    } catch (e) {
                        detail = detail + (xhr.responseText ? ' :: ' + xhr.responseText.slice(0, 160) : '');
                    }
                }
                adicionarResultado('warning',conteudo,apiLabel+' Connection error: '+detail);
                maybeRotateCookie();
            })
            .always(function(){
                const idx=inFlight.indexOf(jqx); if (idx!==-1) inFlight.splice(idx,1);
                if (stopped||paused){activeWorkers--;return;}
                tested++; removeLinha();
                if (autoStopIfTooManyErrors()) return;
                if (tested>=total&&dispatched>=total){activeWorkers--;if(activeWorkers<=0)finishRun();return;}
                runWorker(apiUrl);
            });
            inFlight.push(jqx);
        }
        const CONCURRENCY = 3; // workers per API for true parallelism
        function testar(lista) {
            lista_ref=lista;
            _remainingLines=lista.slice();
            if (stopped||paused) return;
            if (tested>=total){finishRun();return;}
            const apis=getSelectedApis();
            const workerApis=apis.length>1?apis:[apis[0]];
            const totalWorkers=workerApis.length*CONCURRENCY;
            $("#estatus").attr("class","status-pill badge bg-info bg-opacity-25 text-info")
                .html('<span class="loading-dot" style="width:14px;height:14px;border-width:1.5px"></span> Running '+workerApis.length+(workerApis.length>1?' APIs':'  API')+' × '+CONCURRENCY+' workers…');
            activeWorkers=totalWorkers;
            workerApis.forEach(function(apiUrl){
                for(var c=0;c<CONCURRENCY;c++) runWorker(apiUrl);
            });
        }

        $("#chk-start").click(function() {
            const lista = $("#lista_Cartoes").val().trim().split('\n').filter(line => line.trim());
            const cookie = getActiveCookie();
            if (!lista.length) { $("#lista_Cartoes").focus(); toastr.warning("Add at least one card"); return; }
            if (!cookie) { $("#cookie-input").focus(); toastr.warning("Paste a cookie"); return; }

            const invalid = lista.filter(line => !line.includes('|') || line.split('|').length !== 4);
            if (invalid.length) { toastr.error('Invalid format: "' + invalid[0] + '"'); return; }

            total = lista.length; tested = 0; dispatched = 0; lives = 0; dies = 0; errors = 0; consecutiveErrors = 0;
            activeCookieIdx = 0; cookieRotating = false; updateCookieActiveUI();
            stopped = false; paused = false;
            atualizarStats();
            toastr.success('Started with ' + total + ' cards');
            $("#chk-start, #chk-clean").attr("disabled", true);
            $("#chk-stop, #chk-pause").removeAttr('disabled');
            testar(lista);
        });

        $("#chk-pause").click(function() {
            paused = true;
            $("#chk-start").removeAttr('disabled');
            $("#chk-pause").attr("disabled", true);
            $("#estatus").attr("class", "status-pill badge bg-warning bg-opacity-25 text-warning")
                .html('<i class="fas fa-pause"></i> Paused');
            toastr.info("Paused");
        });

        $("#chk-stop").click(function() {
            stopped = true;
            $("#chk-start, #chk-clean").removeAttr('disabled');
            $("#chk-stop, #chk-pause").attr("disabled", true);
            $("#estatus").attr("class", "status-pill badge bg-secondary bg-opacity-50 text-light")
                .html('<i class="fas fa-stop"></i> Stopped');
            toastr.info("Stopped");
        });

        $("#chk-clean").click(function() {
            total = tested = lives = dies = errors = 0;
            stopped = true; paused = false;
            livesData = []; diesData = []; errorsData = [];
            atualizarStats();
            $("#lista_Cartoes").val("");
            $("#cookie-input").val("");
            if (isAutoSave()) {
                localStorage.removeItem('jp_amz_cookie');
                localStorage.removeItem('jp_amz_lista');
            }
            $("#lives-results, #dies-results, #errors-results").empty();
            $("#cookie-status").empty();
            $("#estatus").attr("class", "status-pill badge bg-warning bg-opacity-25 text-warning")
                .html('<i class="fas fa-clock"></i> Waiting...');
            toastr.info("Reset complete");
        });

        $("#copy-lives").click(function() {
            if (!livesData.length) { toastr.warning("Nothing to copy"); return; }
            navigator.clipboard.writeText(livesData.join('\n')).then(() => toastr.success("Copied!"));
        });

        $("#download-lives").click(function() {
            if (!livesData.length) { toastr.warning("Nothing to download"); return; }
            const blob = new Blob([livesData.join('\n')], { type: 'text/plain' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'lives_' + new Date().toISOString().slice(0, 10) + '.txt';
            a.click();
            URL.revokeObjectURL(a.href);
            toastr.success("Download started");
        });

        $("#clear-lives").click(() => { $("#lives-results").empty(); lives = 0; livesData = []; atualizarStats(); });
        $("#clear-dies").click(() => { $("#dies-results").empty(); dies = 0; diesData = []; atualizarStats(); });
        $("#clear-errors").click(() => { $("#errors-results").empty(); errors = 0; errorsData = []; atualizarStats(); });
    });
    </script>
</body>
</html>
