from fastapi import WebSocket
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    
    def __init__(self):
        self.student_connections: Dict[str, WebSocket] = {}
        self.teacher_connections: Dict[str, WebSocket] = {}
        
    async def connect_student(self, websocket: WebSocket, student_id: str):
        await websocket.accept()
        self.student_connections[student_id] = websocket
        logger.info(f"Student {student_id} connected. Total students: {len(self.student_connections)}")
        
    def disconnect_student(self, student_id: str):
        if student_id in self.student_connections:
            del self.student_connections[student_id]
            logger.info(f"Student {student_id} disconnected. Total students: {len(self.student_connections)}")
            
    async def connect_teacher(self, websocket: WebSocket, teacher_id: str):
        await websocket.accept()
        self.teacher_connections[teacher_id] = websocket
        logger.info(f"Teacher {teacher_id} connected. Total teachers: {len(self.teacher_connections)}")
        
    def disconnect_teacher(self, teacher_id: str):
        if teacher_id in self.teacher_connections:
            del self.teacher_connections[teacher_id]
            logger.info(f"Teacher {teacher_id} disconnected. Total teachers: {len(self.teacher_connections)}")
            
    async def broadcast_to_teachers(self, message: dict):
        disconnected = []
        
        for teacher_id, connection in self.teacher_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to teacher {teacher_id}: {str(e)}")
                disconnected.append(teacher_id)
                
        # Clean up disconnected teachers
        for teacher_id in disconnected:
            self.disconnect_teacher(teacher_id)
            
    async def send_to_student(self, student_id: str, message: dict):
        if student_id in self.student_connections:
            try:
                await self.student_connections[student_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending to student {student_id}: {str(e)}")
                self.disconnect_student(student_id)
                
    def get_student_count(self) -> int:
        return len(self.student_connections)
    
    def get_teacher_count(self) -> int:
        return len(self.teacher_connections)
    
    def get_student_ids(self) -> List[str]:
        return list(self.student_connections.keys())
