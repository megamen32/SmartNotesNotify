from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.services.board_service import BoardService

router = APIRouter()
svc = BoardService()

@router.get("/api/board/{user}")
async def board_json(user: str, db: AsyncSession = Depends(get_session)):
    _, lists, notes = await svc.get_board(db, user)
    return {
        "user": user,
        "lists": [
            {
                "id": x.id,
                "title": x.title,
                "pos_x": x.pos_x,
                "pos_y": x.pos_y,
                "width": x.width,
                "height": x.height,
            }
            for x in lists
        ],
        "notes": [
            {
                "id": n.id,
                "text": n.text,
                "pos_x": n.pos_x,
                "pos_y": n.pos_y,
                "todo_list_id": n.todo_list_id,
                "severity": n.severity,
                "tag": n.tag,
                "is_processed_by_llm": n.is_processed_by_llm,
            }
            for n in notes
        ],
    }

@router.get("/board/{user}", response_class=HTMLResponse, name="board_page")
async def board_page(user: str):
    html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Board — {user}</title>
  <style>
    html, body {{ margin:0; height:100%; overflow:hidden; font-family:-apple-system,system-ui,sans-serif; }}
    #viewport {{ position:relative; width:100%; height:100%; background: #f6f6f6; touch-action:none; }}
    #world {{ position:absolute; left:0; top:0; transform-origin: 0 0; }}
    .frame {{
      position:absolute; border:2px solid #cfcfcf; border-radius:16px; background:#ffffffcc;
      box-sizing:border-box; padding:10px;
    }}
    .frame .title {{ font-weight:600; margin-bottom:8px; }}
    .note {{
      position:absolute; width:260px; min-height:80px; border-radius:14px; padding:10px;
      background:#fff; border:1px solid #ddd; box-shadow:0 6px 18px rgba(0,0,0,.08);
      box-sizing:border-box; cursor:grab;
    }}
    .note[data-sev="high"] {{ border-color:#d66; }}
    .note[data-sev="low"] {{ opacity:.85; }}
    .note .meta {{ margin-top:8px; font-size:12px; color:#666; display:flex; gap:8px; flex-wrap:wrap; }}
    .chip {{ padding:2px 8px; border:1px solid #ddd; border-radius:999px; }}
    #hud {{
      position:fixed; left:12px; top:12px; background:#fff; border:1px solid #ddd;
      border-radius:12px; padding:10px; box-shadow:0 8px 22px rgba(0,0,0,.08); z-index:10;
      display:flex; gap:10px; align-items:center;
    }}
    button {{ border:1px solid #ddd; background:#fff; border-radius:10px; padding:8px 10px; }}
  </style>
</head>
<body>
  <div id="hud">
    <div><b>{user}</b></div>
    <button id="btnProcess">Process by LLM</button>
    <button id="btnReset">Reset view</button>
  </div>
  <div id="viewport">
    <div id="world"></div>
  </div>

<script>
const user = {user!r};
const viewport = document.getElementById('viewport');
const world = document.getElementById('world');

let scale = 1;
let panX = 0, panY = 0;

function applyTransform() {{
  world.style.transform = `translate(${{panX}}px, ${{panY}}px) scale(${{scale}})`;
}}

function worldToScreen(x,y) {{
  return {{ x: x*scale + panX, y: y*scale + panY }};
}}
function screenToWorld(x,y) {{
  return {{ x: (x - panX)/scale, y: (y - panY)/scale }};
}}

let data = null;
let frames = new Map();
let notes = new Map();

async function loadBoard() {{
  const res = await fetch(`/api/board/${{encodeURIComponent(user)}}`);
  data = await res.json();
  render();
}}

function render() {{
  world.innerHTML = '';
  frames.clear();
  notes.clear();

  for (const fr of data.lists) {{
    const el = document.createElement('div');
    el.className = 'frame';
    el.style.left = fr.pos_x + 'px';
    el.style.top = fr.pos_y + 'px';
    el.style.width = fr.width + 'px';
    el.style.height = fr.height + 'px';
    el.dataset.id = fr.id;
    el.innerHTML = `<div class="title">${{escapeHtml(fr.title)}}</div>`;
    world.appendChild(el);
    frames.set(fr.id, el);
  }}

  for (const n of data.notes) {{
    const el = document.createElement('div');
    el.className = 'note';
    el.style.left = n.pos_x + 'px';
    el.style.top = n.pos_y + 'px';
    el.dataset.id = n.id;
    el.dataset.sev = n.severity;
    el.dataset.todoListId = (n.todo_list_id ?? '');
    el.innerHTML = `
      <div>${{escapeHtml(n.text)}}</div>
      <div class="meta">
        <span class="chip">#${{n.id}}</span>
        <span class="chip">${{n.severity}}</span>
        <span class="chip">${{n.tag ?? 'no-tag'}}</span>
        <span class="chip">${{n.is_processed_by_llm ? 'llm:yes' : 'llm:no'}}</span>
      </div>
    `;
    world.appendChild(el);
    notes.set(n.id, el);
    makeDraggable(el);
  }}
}}

function escapeHtml(s) {{
  return (s ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
}}

async function patchNote(id, patch) {{
  await fetch(`/api/notes/${{id}}`, {{
    method:'PATCH',
    headers:{{'Content-Type':'application/json'}},
    body: JSON.stringify(patch)
  }});
}}

function rect(el) {{
  return el.getBoundingClientRect();
}}

function intersect(a,b) {{
  return !(a.right < b.left || a.left > b.right || a.bottom < b.top || a.top > b.bottom);
}}

function findFrameUnderNote(noteEl) {{
  const nr = rect(noteEl);
  for (const [id, frEl] of frames.entries()) {{
    const fr = rect(frEl);
    if (intersect(nr, fr)) return id;
  }}
  return null;
}}

function makeDraggable(el) {{
  let dragging = false;
  let start = null;

  el.addEventListener('pointerdown', (e) => {{
    e.preventDefault();
    dragging = true;
    el.setPointerCapture(e.pointerId);
    el.style.cursor = 'grabbing';
    const p = screenToWorld(e.clientX, e.clientY);
    start = {{
      mouseX: p.x, mouseY: p.y,
      left: parseFloat(el.style.left || '0'),
      top: parseFloat(el.style.top || '0'),
    }};
  }});

  el.addEventListener('pointermove', (e) => {{
    if (!dragging) return;
    const p = screenToWorld(e.clientX, e.clientY);
    const dx = p.x - start.mouseX;
    const dy = p.y - start.mouseY;
    el.style.left = (start.left + dx) + 'px';
    el.style.top = (start.top + dy) + 'px';
  }});

  el.addEventListener('pointerup', async () => {{
    if (!dragging) return;
    dragging = false;
    el.style.cursor = 'grab';

    const id = parseInt(el.dataset.id, 10);
    const pos_x = parseFloat(el.style.left);
    const pos_y = parseFloat(el.style.top);

    const frameId = findFrameUnderNote(el);
    const patch = {{ pos_x, pos_y, todo_list_id: frameId }};
    await patchNote(id, patch);
    await loadBoard();
  }});
}}

let panning = false;
let panStart = null;

viewport.addEventListener('pointerdown', (e) => {{
  if (e.target !== viewport) return;
  panning = true;
  viewport.setPointerCapture(e.pointerId);
  panStart = {{ x: e.clientX, y: e.clientY, panX, panY }};
}});

viewport.addEventListener('pointermove', (e) => {{
  if (!panning) return;
  panX = panStart.panX + (e.clientX - panStart.x);
  panY = panStart.panY + (e.clientY - panStart.y);
  applyTransform();
}});

viewport.addEventListener('pointerup', () => {{
  panning = false;
}});

viewport.addEventListener('wheel', (e) => {{
  e.preventDefault();
  const delta = Math.sign(e.deltaY);
  const factor = (delta > 0) ? 0.9 : 1.1;

  const before = screenToWorld(e.clientX, e.clientY);
  scale = Math.min(2.5, Math.max(0.35, scale * factor));
  const after = screenToWorld(e.clientX, e.clientY);

  panX += (after.x - before.x) * scale;
  panY += (after.y - before.y) * scale;

  applyTransform();
}}, {{ passive:false }});

document.getElementById('btnReset').onclick = () => {{
  scale = 1; panX = 0; panY = 0; applyTransform();
}};

document.getElementById('btnProcess').onclick = async () => {{
  await fetch(`/api/users/${{encodeURIComponent(user)}}/process_notes_by_llm`, {{ method:'POST' }});
  await loadBoard();
}};

applyTransform();
loadBoard();
</script>
</body>
</html>
"""
    return HTMLResponse(html)


@router.get("/", response_class=HTMLResponse)
async def root_page():
    html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Smart Notes Notify</title>
  <style>
    body { margin:0; font-family:-apple-system,system-ui,sans-serif; display:flex; align-items:center; justify-content:center; min-height:100vh; background:#f0f2f5; }
    .card { background:#fff; border-radius:16px; padding:32px; box-shadow:0 20px 50px rgba(0,0,0,.05); width:min(420px,90vw); }
    h1 { margin-top:0; font-size:26px; }
    p { color:#555; }
    form { display:flex; flex-direction:column; gap:12px; }
    input, button { font-size:16px; border-radius:10px; border:1px solid #ccc; padding:12px; }
    button { background:#1d4ed8; color:#fff; border-color:#1e40af; cursor:pointer; }
    button:hover { background:#1e40af; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Smart Notes</h1>
    <p>Введи уникальный ключ пользователя — мы создадим его профиль и фреймы прямо сейчас.</p>
    <form>
      <input type="text" name="user" maxlength="200" placeholder="user key (например, alice)" required autofocus>
      <button type="submit">Создать пользователя и открыть доску</button>
    </form>
  </div>
  <script>
    const form = document.querySelector("form");
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const user = form.user.value.trim();
      if (!user) {
        form.user.focus();
        return;
      }
      window.location.href = `/board/${encodeURIComponent(user)}`;
    });
  </script>
</body>
</html>
"""
    return HTMLResponse(html)
