import socketio

sio = socketio.AsyncServer(
    async_mode="asgi", 
    cors_allowed_origins=["http://localhost:3001", "http://localhost:3002"],
    engineio_logger=True, 
    ping_timeout=5,
    ping_interval=5
)