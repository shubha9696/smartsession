import { useParams } from 'react-router-dom'
import { useState, useRef, useEffect } from 'react'
import './TeacherDashboard.css'

const BACKEND_URL = 'ws://localhost:8000'

export default function TeacherDashboard() {
    const { teacherId } = useParams()
    const [students, setStudents] = useState({})
    const [status, setStatus] = useState('disconnected')
    const wsRef = useRef(null)

    useEffect(() => {
        connectWebSocket()
        return () => {
            if (wsRef.current) {
                wsRef.current.close()
            }
        }
    }, [teacherId])

    const connectWebSocket = () => {
        const ws = new WebSocket(`${BACKEND_URL}/ws/teacher/${teacherId}`)
        wsRef.current = ws

        ws.onopen = () => {
            setStatus('connected')
        }

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data)

            if (message.type === 'initial_state') {
                setStudents(message.data)
            } else if (message.type === 'student_update') {
                const data = message.data
                setStudents(prev => ({
                    ...prev,
                    [data.student_id]: {
                        student_id: data.student_id,
                        latest_analysis: data,
                        last_update: data.timestamp
                    }
                }))
            } else if (message.type === 'student_disconnected') {
                setStudents(prev => {
                    const updated = { ...prev }
                    delete updated[message.data.student_id]
                    return updated
                })
            }
        }

        ws.onerror = () => {
            setStatus('error')
        }

        ws.onclose = () => {
            setStatus('disconnected')
        }
    }

    const getStatusColor = (status) => {
        switch (status) {
            case 'good': return 'success'
            case 'warning': return 'warning'
            case 'alert': return 'danger'
            default: return 'secondary'
        }
    }

    const getStatusIcon = (status) => {
        switch (status) {
            case 'good': return '✓'
            case 'warning': return '⚠'
            case 'alert': return '✕'
            default: return '?'
        }
    }

    const studentList = Object.values(students)

    return (
        <div className="teacher-dashboard">
            <div className="container">
                <div className="dashboard-header">
                    <div>
                        <h1>Teacher Dashboard</h1>
                        <p className="teacher-id">Teacher ID: {teacherId}</p>
                    </div>

                    <div className="dashboard-stats">
                        <div className="stat-card">
                            <div className="stat-value">{studentList.length}</div>
                            <div className="stat-label">Active Students</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">
                                {studentList.filter(s => s.latest_analysis?.status === 'alert').length}
                            </div>
                            <div className="stat-label">Alerts</div>
                        </div>
                        <div className="connection-status">
                            <div className={`status-dot ${status}`}></div>
                            <span>{status}</span>
                        </div>
                    </div>
                </div>

                {studentList.length === 0 ? (
                    <div className="empty-state card">
                        <div className="empty-icon">👥</div>
                        <h3>No Students Connected</h3>
                        <p>Waiting for students to join the session...</p>
                    </div>
                ) : (
                    <div className="students-grid">
                        {studentList.map(student => {
                            const analysis = student.latest_analysis
                            const statusColor = getStatusColor(analysis?.status)

                            return (
                                <div key={student.student_id} className={`student-card card card-${statusColor}`}>
                                    <div className="student-card-header">
                                        <div className="student-name">
                                            <div className="student-avatar">
                                                {student.student_id.charAt(0).toUpperCase()}
                                            </div>
                                            <div>
                                                <h4>{student.student_id}</h4>
                                                <span className="last-update">
                                                    {student.last_update ? new Date(student.last_update).toLocaleTimeString() : 'Never'}
                                                </span>
                                            </div>
                                        </div>

                                        <div className={`status-badge badge-${statusColor}`}>
                                            <span className="status-icon">{getStatusIcon(analysis?.status)}</span>
                                            <span>{analysis?.status || 'Unknown'}</span>
                                        </div>
                                    </div>

                                    {analysis && (
                                        <>
                                            <div className="emotion-display">
                                                <div className="emotion-icon">
                                                    {analysis.emotion === 'confused' && '😕'}
                                                    {analysis.emotion === 'happy' && '😊'}
                                                    {analysis.emotion === 'focused' && '🎯'}
                                                    {analysis.emotion === 'neutral' && '😐'}
                                                </div>
                                                <div>
                                                    <div className="emotion-label">{analysis.emotion}</div>
                                                    <div className="engagement-label">{analysis.engagement_level}</div>
                                                </div>
                                            </div>

                                            <div className="metrics-row">
                                                <div className="mini-metric">
                                                    <span className="mini-label">Gaze</span>
                                                    <span className="mini-value">{analysis.gaze_direction}</span>
                                                </div>
                                                <div className="mini-metric">
                                                    <span className="mini-label">Confidence</span>
                                                    <span className="mini-value">{(analysis.confidence * 100).toFixed(0)}%</span>
                                                </div>
                                                {analysis.confusion_score > 0 && (
                                                    <div className="mini-metric">
                                                        <span className="mini-label">Confusion</span>
                                                        <span className="mini-value">{(analysis.confusion_score * 100).toFixed(0)}%</span>
                                                    </div>
                                                )}
                                            </div>

                                            {analysis.message && (
                                                <div className={`alert-message alert-${statusColor}`}>
                                                    {analysis.message}
                                                </div>
                                            )}

                                            {analysis.confusion_indicators && analysis.confusion_indicators.length > 0 && (
                                                <div className="indicators">
                                                    <span className="indicators-label">Indicators:</span>
                                                    {analysis.confusion_indicators.map(indicator => (
                                                        <span key={indicator} className="indicator-tag">
                                                            {indicator.replace('_', ' ')}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </>
                                    )}
                                </div>
                            )
                        })}
                    </div>
                )}
            </div>
        </div>
    )
}
