import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import StudentPortal from './pages/StudentPortal'
import TeacherDashboard from './pages/TeacherDashboard'

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/student/:studentId" element={<StudentPortal />} />
                <Route path="/teacher/:teacherId" element={<TeacherDashboard />} />
            </Routes>
        </Router>
    )
}

export default App
