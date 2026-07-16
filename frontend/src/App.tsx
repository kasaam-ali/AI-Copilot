import { Routes, Route } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { LandingPage } from './pages/LandingPage'
import { InspectPage } from './pages/InspectPage'
import { LiveInspectPage } from './pages/LiveInspectPage'
import { LiveMachinesPage } from './pages/LiveMachinesPage'
import { ResultsPage } from './pages/ResultsPage'
import { ReviewQueuePage } from './pages/ReviewQueuePage'
import { InspectionDetailPage } from './pages/InspectionDetailPage'
import { ReportsPage } from './pages/ReportsPage'
import { ModelsPage } from './pages/ModelsPage'
import { HealthPage } from './pages/HealthPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route element={<AppShell />}>
        <Route path="/inspect" element={<InspectPage />} />
        <Route path="/live" element={<LiveInspectPage />} />
        <Route path="/machines" element={<LiveMachinesPage />} />
        <Route path="/results" element={<ResultsPage />} />
        <Route path="/review" element={<ReviewQueuePage />} />
        <Route path="/review/:id" element={<InspectionDetailPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/models" element={<ModelsPage />} />
        <Route path="/system" element={<HealthPage />} />
      </Route>
    </Routes>
  )
}
