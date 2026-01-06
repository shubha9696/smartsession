import { useParams } from 'react-router-dom'
import { useState, useRef, useEffect } from 'react'
import './StudentPortal.css'

const BACKEND_URL = 'ws://localhost:8000'

export default function StudentPortal() {
    const { studentId } = useParams()
    const [status, setStatus] = useState('disconnected')
    const [analysis, setAnalysis] = useState(null)
    const [isStreaming, setIsStreaming] = useState(false)

    const videoRef = useRef(null)
    const canvasRef = useRef(null)
    const wsRef = useRef(null)
    const streamRef = useRef(null)
    const intervalRef = useRef(null)

    useEffect(() => {
        return () => {
            stopStreaming()
        }
    }, [])

    const startStreaming = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480 }
            })

            streamRef.current = stream
            if (videoRef.current) {
                videoRef.current.srcObject = stream
            }

            const ws = new WebSocket(`${BACKEND_URL}/ws/student/${studentId}`)
            wsRef.current = ws

            ws.onopen = () => {
                setStatus('connected')
                setIsStreaming(true)
                startSendingFrames()
            }

            ws.onmessage = (event) => {
                const message = JSON.parse(event.data)
                if (message.type === 'analysis_result') {
                    setAnalysis(message.data)
                }
            }

            ws.onerror = () => {
                setStatus('error')
            }

            ws.onclose = () => {
                setStatus('disconnected')
                setIsStreaming(false)
            }

        } catch (err) {
            console.error('Camera access denied:', err)
            setStatus('error')
        }
    }

    const startSendingFrames = () => {
        intervalRef.current = setInterval(() => {
            if (videoRef.current && canvasRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
                const canvas = canvasRef.current
                const video = videoRef.current

                canvas.width = video.videoWidth
                canvas.height = video.videoHeight

                const ctx = canvas.getContext('2d')
                ctx.drawImage(video, 0, 0)

                canvas.toBlob((blob) => {
                    const reader = new FileReader()
                    reader.onloadend = () => {
                        wsRef.current.send(JSON.stringify({
                            type: 'video_frame',
                            frame: reader.result
                        }))
                    }
                    reader.readAsDataURL(blob)
                }, 'image/jpeg', 0.8)
            }
        }, 200)
    }

    const stopStreaming = () => {
        if (intervalRef.current) {
            clearInterval(intervalRef.current)
        }

        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop())
        }

        if (wsRef.current) {
            wsRef.current.close()
        }

        setIsStreaming(false)
        setStatus('disconnected')
    }

    const getStatusColor = () => {
        if (!analysis) return 'var(--color-text-tertiary)'

        switch (analysis.status) {
            case 'good': return 'var(--color-success)'
            case 'warning': return 'var(--color-warning)'
            case 'alert': return 'var(--color-danger)'
            default: return 'var(--color-text-tertiary)'
        }
    }

    return (
        <div className="student-portal">
            <div className="container">
                <div className="portal-header">
                    <h1>Student Portal</h1>
                    <div className="student-info">
                        <span className="student-id">ID: {studentId}</span>
                        <div className="connection-status">
                            <div className={`status-dot ${status}`}></div>
                            <span>{status}</span>
                        </div>
                    </div>
                </div>

                <div className="portal-content">
                    <div className="video-section card">
                        <video
                            ref={videoRef}
                            autoPlay
                            playsInline
                            muted
                            className="video-feed"
                        />
                        <canvas ref={canvasRef} style={{ display: 'none' }} />

                        <div className="video-controls">
                            {!isStreaming ? (
                                <button onClick={startStreaming} className="btn btn-primary">
                                    Start Session
                                </button>
                            ) : (
                                <button onClick={stopStreaming} className="btn btn-danger">
                                    End Session
                                </button>
                            )}
                        </div>
                    </div>

                    {analysis && (
                        <div className="analysis-panel card">
                            <h3>Live Analysis</h3>

                            <div className="status-display">
                                <div
                                    className="status-indicator"
                                    style={{ backgroundColor: getStatusColor() }}
                                >
                                    {analysis.emotion?.toUpperCase() || 'ANALYZING'}
                                </div>
                            </div>

                            <div className="metrics-grid">
                                <div className="metric">
                                    <span className="metric-label">Engagement</span>
                                    <span className="metric-value">{analysis.engagement_level || 'Unknown'}</span>
                                </div>
                                <div className="metric">
                                    <span className="metric-label">Gaze</span>
                                    <span className="metric-value">{analysis.gaze_direction || 'Center'}</span>
                                </div>
                                <div className="metric">
                                    <span className="metric-label">Confidence</span>
                                    <span className="metric-value">{(analysis.confidence * 100).toFixed(0)}%</span>
                                </div>
                            </div>

                            {analysis.message && (
                                <div className={`alert alert-${analysis.status}`}>
                                    {analysis.message}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
