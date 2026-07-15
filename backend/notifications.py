"""Gerencia conexões WebSocket para avisar o dashboard sobre novas
mudanças em tempo real (PRD.md seção 4.4)."""
import asyncio

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        # referência à event loop do FastAPI, necessária pois o agendador
        # roda em thread síncrona separada (ver scheduler.py)
        self.loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def _broadcast(self, message: dict) -> None:
        conexoes_mortas = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                conexoes_mortas.append(connection)
        for conexao in conexoes_mortas:
            self.disconnect(conexao)

    def notify(self, message: dict) -> None:
        """Chamado a partir da thread síncrona do agendador para agendar
        o broadcast na event loop principal do FastAPI."""
        if self.loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._broadcast(message), self.loop)


manager = ConnectionManager()
