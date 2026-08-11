import { useState } from 'react';
import './App.css'
import { Navbar } from './components/layout/navbar'
import { useAuth } from './contexts/AuthContext';
import { Login } from './pages/Login';
import { WorkOrdersList } from './pages/WorkOrdersList';
import { CreateWorkOrderModal } from './components/workOrders/CreateWorkOrderModal';
import { StatusChangeModal } from './components/workOrders/StatusChangeModal';
import { WorkOrder } from './types';

function App() {
  const { user } = useAuth();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedWO, setSelectedWO] = useState<WorkOrder | null>(null);
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
          onOpenStatus={(wo) => setSelectedWO(wo)}
          onOpenHistory={(id) => alert(`Ver histórico da OS #${id}`)}
        />
      </main>

      <CreateWorkOrderModal 
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSuccess={() => setRefreshKey((k) => k + 1)}
      />

      <StatusChangeModal
        workOrder={selectedWO}
        isOpen={!!selectedWO}
        onClose={() => setSelectedWO(null)}
        onSuccess={() => {
          setSelectedWO(null);
          setRefreshKey((k) => k + 1);
        }}
      />
    </div>
  )
}

export default App
