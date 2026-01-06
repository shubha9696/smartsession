import { Link } from 'react-router-dom'
import { useState } from 'react'
import './HomePage.css'

export default function HomePage() {
    const [studentId, setStudentId] = useState('student1')
    const [teacherId, setTeacherId] = useState('teacher1')

    return (
        <div className="home-page">
            <div className="hero-section">
                <div className="container">
                    <div className="hero-content">
                        <h1 className="hero-title">
                            <span className="gradient-text">SmartSession</span>
                        </h1>
                        <p className="hero-subtitle">
                            AI-Powered Student Monitoring & Engagement Platform
                        </p>
                        <p className="hero-description">
                            Real-time proctoring and confusion detection using advanced computer vision
                        </p>

                        <div className="portal-cards">
                            <div className="card portal-card animate-slide-in">
                                <div className="portal-icon student-icon">📹</div>
                                <h3>Student Portal</h3>
                                <p>Join a monitored session with real-time engagement tracking</p>
                                <input
                                    type="text"
                                    className="input-field"
                                    placeholder="Enter Student ID"
                                    value={studentId}
                                    onChange={(e) => setStudentId(e.target.value)}
                                />
                                <Link to={`/student/${studentId}`} className="btn btn-primary">
                                    Enter Session
                                </Link>
                            </div>

                            <div className="card portal-card animate-slide-in" style={{ animationDelay: '0.1s' }}>
                                <div className="portal-icon teacher-icon">📊</div>
                                <h3>Teacher Dashboard</h3>
                                <p>Monitor all students in real-time with actionable insights</p>
                                <input
                                    type="text"
                                    className="input-field"
                                    placeholder="Enter Teacher ID"
                                    value={teacherId}
                                    onChange={(e) => setTeacherId(e.target.value)}
                                />
                                <Link to={`/teacher/${teacherId}`} className="btn btn-primary">
                                    Open Dashboard
                                </Link>
                            </div>
                        </div>

                        <div className="features-grid">
                            <div className="feature-item">
                                <div className="feature-icon">👁️</div>
                                <h4>Gaze Tracking</h4>
                                <p>Detect when students look away</p>
                            </div>
                            <div className="feature-item">
                                <div className="feature-icon">😕</div>
                                <h4>Confusion Detection</h4>
                                <p>Custom AI identifies struggling students</p>
                            </div>
                            <div className="feature-item">
                                <div className="feature-icon">🎯</div>
                                <h4>Engagement Metrics</h4>
                                <p>Live emotion and focus analysis</p>
                            </div>
                            <div className="feature-item">
                                <div className="feature-icon">🔒</div>
                                <h4>Proctoring</h4>
                                <p>Multi-person and absence alerts</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
