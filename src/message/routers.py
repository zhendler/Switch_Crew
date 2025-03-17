from fastapi import APIRouter, Depends, Query, WebSocket, status
from fastapi.websockets import WebSocketDisconnect
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession

from config.db import get_db
from src.auth.utils import get_current_user
from src.message.repos import MessageRepository, ChatRepository
from src.message.schemas import ChatSchema, MessageSchema


router = APIRouter()
active_connections: Dict[int, List[WebSocket]] = {}
