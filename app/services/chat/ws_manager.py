from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import DefaultDict

from fastapi import WebSocket


class ChatWebSocketManager:
	def __init__(self) -> None:
		self._lock = asyncio.Lock()
		# chat_id -> { websocket -> user_id }
		self._connections: DefaultDict[int, dict[WebSocket, int]] = defaultdict(dict)

	async def connect(self, *, chat_id: int, user_id: int, websocket: WebSocket) -> None:
		await websocket.accept()
		async with self._lock:
			self._connections[chat_id][websocket] = user_id

	async def disconnect(self, *, chat_id: int, user_id: int, websocket: WebSocket) -> bool:
		"""Remove a connection.

		Returns True if the user still has any active connections in this chat.
		"""
		async with self._lock:
			room = self._connections.get(chat_id)
			if not room:
				return False
			room.pop(websocket, None)
			user_still_online = user_id in room.values()
			if not room:
				self._connections.pop(chat_id, None)
			return user_still_online

	async def get_online_user_ids(self, *, chat_id: int) -> list[int]:
		async with self._lock:
			room = self._connections.get(chat_id, {})
			return sorted(set(room.values()))

	async def broadcast(self, *, chat_id: int, message: dict, exclude_user_id: int | None = None) -> set[int]:
		async with self._lock:
			room = self._connections.get(chat_id, {})
			connections = list(room.items())

		if not connections:
			return set()

		delivered_user_ids: set[int] = set()
		dead: list[WebSocket] = []
		for ws, user_id in connections:
			if exclude_user_id is not None and user_id == exclude_user_id:
				continue
			try:
				await ws.send_json(message)
				delivered_user_ids.add(user_id)
			except Exception:
				dead.append(ws)

		if dead:
			async with self._lock:
				room = self._connections.get(chat_id)
				if not room:
					return delivered_user_ids
				for ws in dead:
					room.pop(ws, None)
				if not room:
					self._connections.pop(chat_id, None)

		return delivered_user_ids


chat_ws_manager = ChatWebSocketManager()
