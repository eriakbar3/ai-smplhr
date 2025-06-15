import socketio
from aiohttp import web
from ai import generate
from recruiter import recruiter_agent
# Inisialisasi server socket
sio = socketio.AsyncServer(cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

# Event ketika user connect
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit('message', {'sender': 'server', 'text': 'Selamat datang!'}, to=sid)

# Event ketika menerima pesan
@sio.event
async def message(sid, data):
    print(f"Message from {sid}: {data}")
    ans = generate(data['text'])
    # Kirim balik pesan
    await sio.emit('message', {'sender': 'server', 'text': ans}, to=sid)
    if ans['agent'] == 'recruiter':
        await recruiter_agent(sio,data['text'],sid)

# Event disconnect
@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

# Jalankan server
if __name__ == '__main__':
    web.run_app(app, port=5000)
