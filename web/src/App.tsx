import { useState } from 'react';
import './App.css'
import { Navbar } from './components/layout/navbar'
import { useAuth } from './contexts/AuthContext';
import { Login } from './pages/Login';
import { WorkOrdersList } from './pages/WorkOrdersList';
import { CreateWorkOrderModal } from './components/workOrders/CreateWorkOrderModal';

function App() {
  const { user } = useAuth();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  if (!user) {
    return <Login />
  }

  return (
    <div className="app-container">
      <Navbar />
      <main className="main-content">
        <WorkOrdersList 
          key={refreshKey}
          onOpenCreate={() => setIsCreateOpen(true)}
          onOpenStatus={(wo) => alert(`Alterar status da OS #${wo.id} (${wo.title})`)}
          onOpenHistory={(id) => alert(`Ver histórico da OS #${id}`)}
        />
      </main>

      <CreateWorkOrderModal 
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSuccess={() => setRefreshKey((k) => k + 1)}
      />
    </div>
  )
}

export default App
