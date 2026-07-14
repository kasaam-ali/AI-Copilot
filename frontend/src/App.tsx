import { Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { HealthPage } from './pages/HealthPage'

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/system" replace />} />
        <Route path="/system" element={<HealthPage />} />
      </Route>
    </Routes>
  )
}
