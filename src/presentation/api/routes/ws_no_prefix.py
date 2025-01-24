import socketio
from src.core.socket_io import sio

class RootNamespace(socketio.AsyncNamespace):
    async def on_connect(self, sid, environ):
        print(f"Client connected: {sid}")

    async def on_disconnect(self, sid):
        print(f"Client disconnected: {sid}")

    async def on_message(self, sid, data):
        print(f"Message from {sid}: {data}")
        await self.emit('response', f'Server received: {data}')