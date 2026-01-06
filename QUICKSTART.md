# Quick Start Guide

## Prerequisites

- Python 3.8+
- Node.js 16+
- Webcam for student portal
- Modern browser (Chrome/Edge recommended)

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/shubha9696/smartsession.git
cd smartsession
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python main.py
```

Backend will start on `http://localhost:8000`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Frontend will start on `http://localhost:3000`

## Usage

### For Students
1. Navigate to `http://localhost:3000`
2. Click "Student Portal"
3. Enter your student ID (e.g., "student1")
4. Click "Start Session" and allow camera access
5. Your engagement will be monitored in real-time

### For Teachers
1. Navigate to `http://localhost:3000`
2. Click "Teacher Dashboard"
3. Enter your teacher ID (e.g., "teacher1")
4. View all connected students and their engagement metrics

## Testing the System

1. Open two browser windows
2. Window 1: Student portal (student1)
3. Window 2: Teacher dashboard (teacher1)
4. Try different expressions to see real-time detection:
   - **Confused**: Furrow brows + squint eyes + no smile
   - **Focused**: Look at camera, neutral expression
   - **Happy**: Smile while looking at camera
   - **Alert (Gaze Away)**: Look away for >4 seconds

## API Health Check

```bash
curl http://localhost:8000/
curl http://localhost:8000/api/health
```

## Troubleshooting

**Camera not working?**
- Ensure HTTPS or localhost
- Check browser permissions
- Try different browser

**WebSocket not connecting?**
- Verify backend is running on port 8000
- Check firewall settings
- Look at browser console for errors

**High CPU usage?**
- Normal - MediaPipe is computationally intensive
- Reduce frame rate in StudentPortal.jsx (line 82)

## Configuration

### Adjust Detection Sensitivity
Edit `backend/video_analyzer.py`:
```python
Line 31: self.GAZE_AWAY_THRESHOLD = 4.0  # seconds before alert
Line 32: self.HISTORY_SIZE = 30  # frames to track
Line 33: self.CONFUSION_THRESHOLD = 0.6  # 0-1 sensitivity
```

### Change WebSocket URL
Edit frontend files:
```javascript
const BACKEND_URL = 'ws://your-server:8000'
```

## Demo Video Script

For recording your submission video:

1. Show homepage and explain architecture
2. Open Student Portal, start session
3. Demonstrate confusion detection:
   - Show code in `video_analyzer.py` lines 127-203
   - Explain the 5 indicators
   - Make confused face → show yellow warning
4. Open Teacher Dashboard
5. Show real-time updates as you change expressions
6. Explain WebSocket architecture choice

---

**GitHub**: https://github.com/shubha9696/smartsession  
**Documentation**: See README.md and CONFUSION_DETECTION.md
