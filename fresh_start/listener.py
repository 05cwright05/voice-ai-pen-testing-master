"""
Call Listener - join LiveKit rooms to hear calls and see live transcription.

Run:
    python listener.py
Then open http://localhost:8082
"""

import os
import secrets

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from livekit import api

load_dotenv()

LIVEKIT_URL = os.environ["LIVEKIT_URL"]
LIVEKIT_API_KEY = os.environ["LIVEKIT_API_KEY"]
LIVEKIT_API_SECRET = os.environ["LIVEKIT_API_SECRET"]

app = FastAPI()


@app.get("/api/rooms")
async def list_rooms():
    lk = api.LiveKitAPI()
    res = await lk.room.list_rooms(api.ListRoomsRequest())
    await lk.aclose()
    return [
        {"name": r.name, "num_participants": r.num_participants}
        for r in res.rooms
    ]


@app.get("/api/token")
async def get_token(room: str = Query(...)):
    identity = f"listener-{secrets.token_hex(3)}"
    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room,
                can_publish=False,
                can_publish_data=False,
                can_subscribe=True,
            )
        )
    )
    return {"token": token.to_jwt(), "url": LIVEKIT_URL}


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Call Listener</title>
<script src="https://cdn.jsdelivr.net/npm/livekit-client@2/dist/livekit-client.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0b0d17;color:#e0e0e8;height:100vh;display:flex;flex-direction:column}

header{display:flex;align-items:center;justify-content:space-between;padding:16px 24px;background:#12152299;border-bottom:1px solid #1e2235;backdrop-filter:blur(12px);position:sticky;top:0;z-index:10}
header h1{font-size:18px;font-weight:600;letter-spacing:-.3px}
header h1 span{color:#6c7aff;margin-right:6px}
.status{display:flex;align-items:center;gap:8px;font-size:13px;color:#888}
.status .dot{width:8px;height:8px;border-radius:50%;background:#444;transition:background .3s}
.status .dot.live{background:#34d399;box-shadow:0 0 8px #34d39966;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}

.container{flex:1;display:flex;flex-direction:column;max-width:720px;width:100%;margin:0 auto;padding:20px 16px;overflow:hidden}

/* Rooms view */
#rooms-view h2{font-size:15px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:16px}
.room-card{background:#161929;border:1px solid #1e2235;border-radius:12px;padding:16px 20px;margin-bottom:10px;display:flex;align-items:center;justify-content:space-between;transition:border-color .2s,background .2s}
.room-card:hover{border-color:#6c7aff44;background:#1a1e32}
.room-info{display:flex;flex-direction:column;gap:4px}
.room-name{font-size:15px;font-weight:500;color:#e0e0e8}
.room-meta{font-size:12px;color:#666}
.join-btn{background:#6c7aff;color:#fff;border:none;padding:8px 20px;border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;transition:background .2s}
.join-btn:hover{background:#5a68e6}
.empty-state{text-align:center;padding:60px 20px;color:#555;font-size:14px}
.empty-state .icon{font-size:40px;margin-bottom:12px;opacity:.4}
.spinner{display:inline-block;width:16px;height:16px;border:2px solid #333;border-top-color:#6c7aff;border-radius:50%;animation:spin .8s linear infinite;margin-right:8px;vertical-align:middle}
@keyframes spin{to{transform:rotate(360deg)}}

/* Chat view */
#chat-view{display:none;flex-direction:column;flex:1;overflow:hidden}
.chat-header{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.back-btn{background:none;border:1px solid #2a2d45;color:#888;padding:6px 14px;border-radius:8px;font-size:13px;cursor:pointer;transition:all .2s}
.back-btn:hover{border-color:#6c7aff;color:#e0e0e8}
.chat-room-name{font-size:15px;font-weight:500;flex:1}
.live-badge{background:#34d39922;color:#34d399;font-size:11px;padding:3px 10px;border-radius:12px;font-weight:500}

.participants{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.participant-tag{background:#161929;border:1px solid #1e2235;padding:4px 12px;border-radius:16px;font-size:12px;color:#aaa;display:flex;align-items:center;gap:6px}
.participant-tag .p-dot{width:6px;height:6px;border-radius:50%;background:#34d399}

#messages{flex:1;overflow-y:auto;padding:8px 0;display:flex;flex-direction:column;gap:6px;scroll-behavior:smooth}
#messages::-webkit-scrollbar{width:4px}
#messages::-webkit-scrollbar-track{background:transparent}
#messages::-webkit-scrollbar-thumb{background:#2a2d45;border-radius:4px}

.message{max-width:80%;padding:10px 14px;border-radius:16px;font-size:14px;line-height:1.5;animation:fadeIn .25s ease-out;word-wrap:break-word}
@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}

.message.agent{align-self:flex-end;background:#6c7aff22;border:1px solid #6c7aff33;border-bottom-right-radius:4px}
.message.target{align-self:flex-start;background:#1e2235;border:1px solid #2a2d45;border-bottom-left-radius:4px}
.message .sender{font-size:11px;font-weight:600;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px}
.message.agent .sender{color:#6c7aff}
.message.target .sender{color:#34d399}
.message .bubble-text{color:#d0d0d8}
.message.interim .bubble-text{color:#888;font-style:italic}

.audio-bar{display:flex;align-items:center;gap:10px;padding:12px 16px;background:#161929;border:1px solid #1e2235;border-radius:12px;margin-top:12px;font-size:13px;color:#888}
.audio-bar .vol-icon{font-size:18px}
.audio-bar .track-count{color:#aaa}

#audio-container{position:absolute;top:-9999px;left:-9999px}
</style>
</head>
<body>

<header>
  <h1><span>&#9879;</span> Call Listener</h1>
  <div class="status">
    <div class="dot" id="hdr-dot"></div>
    <span id="hdr-status">Idle</span>
  </div>
</header>

<div class="container">
  <div id="rooms-view">
    <h2>Active Rooms</h2>
    <div id="rooms-list">
      <div class="empty-state"><div class="icon">&#128222;</div>No active rooms yet.<br>Start a call and it will appear here.</div>
    </div>
  </div>

  <div id="chat-view">
    <div class="chat-header">
      <button class="back-btn" onclick="leaveRoom()">&#8592; Back</button>
      <span class="chat-room-name" id="chat-room-name"></span>
      <span class="live-badge" id="live-badge">&#9679; LIVE</span>
    </div>
    <div class="participants" id="participants"></div>
    <div id="messages"></div>
    <div class="audio-bar">
      <span class="vol-icon">&#128266;</span>
      <span>Audio playing through speakers</span>
      <span class="track-count" id="track-count">0 tracks</span>
    </div>
  </div>
</div>

<div id="audio-container"></div>

<script>
const { Room, RoomEvent } = LivekitClient;

let room = null;
let refreshTimer = null;
const segmentBubbles = new Map();
let audioTrackCount = 0;

async function loadRooms() {
  try {
    const res = await fetch('/api/rooms');
    const rooms = await res.json();
    renderRooms(rooms);
  } catch (e) {
    console.error('Failed to load rooms', e);
  }
}

function renderRooms(rooms) {
  const el = document.getElementById('rooms-list');
  if (!rooms.length) {
    el.innerHTML = '<div class="empty-state"><div class="icon">&#128222;</div>No active rooms yet.<br>Start a call and it will appear here.</div>';
    return;
  }
  el.innerHTML = rooms.map(r => `
    <div class="room-card">
      <div class="room-info">
        <div class="room-name">&#128222; ${escHtml(r.name)}</div>
        <div class="room-meta">${r.num_participants} participant${r.num_participants !== 1 ? 's' : ''}</div>
      </div>
      <button class="join-btn" onclick="joinRoom('${escAttr(r.name)}')">Join</button>
    </div>
  `).join('');
}

async function joinRoom(roomName) {
  stopRefresh();
  setStatus('Connecting...', false);

  try {
    const res = await fetch(`/api/token?room=${encodeURIComponent(roomName)}`);
    const { token, url } = await res.json();

    room = new Room({ adaptiveStream: true, dynacast: true });

    room.on(RoomEvent.TrackSubscribed, (track, pub, participant) => {
      if (track.kind === 'audio') {
        const el = track.attach();
        el.volume = 1.0;
        document.getElementById('audio-container').appendChild(el);
        audioTrackCount++;
        updateTrackCount();
      }
    });

    room.on(RoomEvent.TrackUnsubscribed, (track) => {
      track.detach().forEach(el => el.remove());
      audioTrackCount = Math.max(0, audioTrackCount - 1);
      updateTrackCount();
    });

    room.on(RoomEvent.TranscriptionReceived, (segments, participant, pub) => {
      for (const seg of segments) {
        handleSegment(seg, participant);
      }
    });

    room.on(RoomEvent.ParticipantConnected, (p) => renderParticipants());
    room.on(RoomEvent.ParticipantDisconnected, (p) => renderParticipants());

    room.on(RoomEvent.Disconnected, () => {
      setStatus('Disconnected', false);
      document.getElementById('live-badge').textContent = '\u25cf ENDED';
      document.getElementById('live-badge').style.background = '#ff4d4f22';
      document.getElementById('live-badge').style.color = '#ff4d4f';
    });

    await room.connect(url, token);
    setStatus('Connected', true);
    showChatView(roomName);
    renderParticipants();

  } catch (e) {
    console.error('Join failed', e);
    setStatus('Error: ' + e.message, false);
    startRefresh();
  }
}

function leaveRoom() {
  if (room) {
    room.disconnect();
    room = null;
  }
  audioTrackCount = 0;
  segmentBubbles.clear();
  document.getElementById('audio-container').innerHTML = '';
  document.getElementById('messages').innerHTML = '';
  document.getElementById('participants').innerHTML = '';
  showRoomsView();
  setStatus('Idle', false);
  startRefresh();
}

function handleSegment(seg, participant) {
  const msgs = document.getElementById('messages');
  const identity = participant?.identity || 'unknown';
  const isAgent = !identity.startsWith('+') && !/^\d{10,}$/.test(identity);

  if (segmentBubbles.has(seg.id)) {
    const bubble = segmentBubbles.get(seg.id);
    bubble.querySelector('.bubble-text').textContent = seg.text;
    if (seg.final) {
      bubble.classList.remove('interim');
      bubble.classList.add('final');
    }
  } else {
    const bubble = document.createElement('div');
    const senderLabel = isAgent ? '\uD83E\uDD16 AI Agent' : '\uD83D\uDCDE ' + identity;
    bubble.className = `message ${isAgent ? 'agent' : 'target'} ${seg.final ? 'final' : 'interim'}`;
    bubble.innerHTML = `<div class="sender">${escHtml(senderLabel)}</div><div class="bubble-text">${escHtml(seg.text)}</div>`;
    segmentBubbles.set(seg.id, bubble);
    msgs.appendChild(bubble);
  }
  msgs.scrollTop = msgs.scrollHeight;
}

function renderParticipants() {
  if (!room) return;
  const el = document.getElementById('participants');
  const parts = [room.localParticipant, ...room.remoteParticipants.values()];
  el.innerHTML = parts.map(p => {
    const id = p.identity || 'unknown';
    const isListener = id.startsWith('listener-');
    const label = isListener ? 'You (listener)' : id;
    return `<span class="participant-tag"><span class="p-dot"></span>${escHtml(label)}</span>`;
  }).join('');
}

function updateTrackCount() {
  document.getElementById('track-count').textContent = `${audioTrackCount} track${audioTrackCount !== 1 ? 's' : ''}`;
}

function showChatView(roomName) {
  document.getElementById('rooms-view').style.display = 'none';
  document.getElementById('chat-view').style.display = 'flex';
  document.getElementById('chat-room-name').textContent = roomName;
  document.getElementById('live-badge').textContent = '\u25cf LIVE';
  document.getElementById('live-badge').style.background = '#34d39922';
  document.getElementById('live-badge').style.color = '#34d399';
}

function showRoomsView() {
  document.getElementById('rooms-view').style.display = 'block';
  document.getElementById('chat-view').style.display = 'none';
}

function setStatus(text, live) {
  document.getElementById('hdr-status').textContent = text;
  const dot = document.getElementById('hdr-dot');
  dot.classList.toggle('live', live);
}

function startRefresh() { refreshTimer = setInterval(loadRooms, 3000); }
function stopRefresh() { clearInterval(refreshTimer); }

function escHtml(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
function escAttr(s) { return s.replace(/'/g, "\\'").replace(/"/g, '&quot;'); }

startRefresh();
loadRooms();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8082)
