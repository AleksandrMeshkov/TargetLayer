from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import DefaultDict

from fastapi import WebSocket


class ChatWebSocketManager:
	def __init__(self) -> None:
		self._lock = asyncio.Lock()
		self._connections: DefaultDict[int, dict[WebSocket, int]] = defaultdict(dict)

	async def connect(self, *, chat_id: int, user_id: int, websocket: WebSocket) -> None:
		"""Подключить пользователя к чату"""
		await websocket.accept()
		async with self._lock:
			self._connections[chat_id][websocket] = user_id

	async def disconnect(self, *, chat_id: int, user_id: int, websocket: WebSocket) -> None:
		"""Отключить пользователя от чата"""
		async with self._lock:
			room = self._connections.get(chat_id)
			if room:
				room.pop(websocket, None)
				if not room:
					self._connections.pop(chat_id, None)

	async def broadcast(self, *, chat_id: int, message: dict) -> None:
		"""Отправить сообщение всем пользователям чата"""
		async with self._lock:
			room = self._connections.get(chat_id, {})
			connections = list(room.items())

		if not connections:
			return

		dead: list[WebSocket] = []
		for ws, _ in connections:
			try:
				await ws.send_json(message)
			except Exception:
				dead.append(ws)

		if dead:
			async with self._lock:
				room = self._connections.get(chat_id)
				if room:
					for ws in dead:
						room.pop(ws, None)
					if not room:
						self._connections.pop(chat_id, None)


chat_ws_manager = ChatWebSocketManager()
