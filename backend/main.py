from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import base64
import json
import asyncio
from datetime import datetime
from typing import Dict, List
import logging

from video_analyzer import VideoAnalyzer
from connection_manager import ConnectionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SmartSession API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()
video_analyzer = VideoAnalyzer()


@app.get("/")
async def root():
    return {
        "status": "active",
        "service": "SmartSession API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "active_students": manager.get_student_count(),
        "active_teachers": manager.get_teacher_count(),
        "analyzer_ready": video_analyzer.is_ready(),
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/ws/student/{student_id}")
async def student_websocket(websocket: WebSocket, student_id: str):
    await manager.connect_student(websocket, student_id)
    logger.info(f"Student {student_id} connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "video_frame":
                frame_data = message["frame"]
                frame_bytes = base64.b64decode(frame_data.split(",")[1] if "," in frame_data else frame_data)
                nparr = np.frombuffer(frame_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    analysis_result = video_analyzer.analyze_frame(frame, student_id)
                    analysis_result["student_id"] = student_id
                    analysis_result["timestamp"] = datetime.now().isoformat()
                    
                    await websocket.send_json({
                        "type": "analysis_result",
                        "data": analysis_result
                    })
                    
                    await manager.broadcast_to_teachers({
                        "type": "student_update",
                        "data": analysis_result
                    })
                    
                    logger.debug(f"Analyzed frame for student {student_id}: {analysis_result['status']}")
                
            elif message["type"] == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect_student(student_id)
        logger.info(f"Student {student_id} disconnected")
        
        await manager.broadcast_to_teachers({
            "type": "student_disconnected",
            "data": {
                "student_id": student_id,
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in student websocket {student_id}: {str(e)}")
        manager.disconnect_student(student_id)

@app.websocket("/ws/teacher/{teacher_id}")
async def teacher_websocket(websocket: WebSocket, teacher_id: str):
    await manager.connect_teacher(websocket, teacher_id)
    logger.info(f"Teacher {teacher_id} connected")
    
    current_state = video_analyzer.get_all_students_state()
    await websocket.send_json({
        "type": "initial_state",
        "data": current_state
    })
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "ping":
                await websocket.send_json({"type": "pong"})
            elif message["type"] == "request_state":
                current_state = video_analyzer.get_all_students_state()
                await websocket.send_json({
                    "type": "state_update",
                    "data": current_state
                })
                
    except WebSocketDisconnect:
        manager.disconnect_teacher(teacher_id)
        logger.info(f"Teacher {teacher_id} disconnected")
        
    except Exception as e:
        logger.error(f"Error in teacher websocket {teacher_id}: {str(e)}")
        manager.disconnect_teacher(teacher_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
