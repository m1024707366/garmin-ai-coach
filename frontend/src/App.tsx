import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Analysis from './pages/Analysis'
import History from './pages/History'
import MorningReport from './pages/MorningReport'
import EveningReview from './pages/EveningReview'
import WeeklySummary from './pages/WeeklySummary'
import InjuryLog from './pages/InjuryLog'
import Profile from './pages/Profile'
import Chat from './pages/Chat'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/analysis/:date" element={<Analysis />} />
          <Route path="/history" element={<History />} />
          <Route path="/morning-report" element={<MorningReport />} />
          <Route path="/evening-review" element={<EveningReview />} />
          <Route path="/weekly-summary" element={<WeeklySummary />} />
          <Route path="/injury-log" element={<InjuryLog />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
