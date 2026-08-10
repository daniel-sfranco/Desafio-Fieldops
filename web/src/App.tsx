import './App.css'
import { StatusBadge } from './components/common/StatusBadge'
import { PriorityBadge } from './components/common/PriorityBadge'

function App() {
  return (
    <>
      <StatusBadge status="open"></StatusBadge>
      <PriorityBadge priority="high"></PriorityBadge>
    </>
  )
}

export default App
