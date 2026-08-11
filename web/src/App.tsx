import { useState } from 'react';
import './App.css'
import { Navbar } from './components/layout/navbar'
import { useAuth } from './contexts/AuthContext';
import { Login } from './pages/Login';
import { WorkOrdersList } from './pages/WorkOrdersList';
import { CreateWorkOrderModal } from './components/workOrders/CreateWorkOrderModal';
import { StatusChangeModal } from './components/workOrders/StatusChangeModal';
import { WorkOrderHistoryModal } from './components/workOrders/WorkOrderHistoryModal';
import { Toast } from './components/common/Toast';
import { WorkOrder } from './types';

function App() {
  const { user } = useAuth();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedWO, setSelectedWO] = useState<WorkOrder | null>(null);
  const [historyWOId, setHistoryWOId] = useState<number | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  if (!user) {
    return <Login />
  }

  const handleCreateSuccess = () => {
    setRefreshKey((k) => k + 1);
    setToastMessage('Ordem de serviço criada com sucesso!');
  }

  const handleStatusSuccess = () => {
    setSelectedWO(null);
    setRefreshKey((k) => k + 1);
    setToastMessage('Alterações salvas com sucesso!');
  }

  return (
    <div className="app-container">
      <Navbar />
      <main className="main-content">
        <WorkOrdersList 
          key={refreshKey}
          onOpenCreate={() => setIsCreateOpen(true)}
          onOpenStatus={(wo) => setSelectedWO(wo)}
          onOpenHistory={(id) => setHistoryWOId(id)}
        />
      </main>

      <CreateWorkOrderModal 
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSuccess={handleCreateSuccess}
      />

      <StatusChangeModal
        workOrder={selectedWO}
        isOpen={!!selectedWO}
        onClose={() => setSelectedWO(null)}
        onSuccess={handleStatusSuccess}
      />

      <WorkOrderHistoryModal
        workOrderId={historyWOId}
        isOpen={!!historyWOId}
        onClose={() => setHistoryWOId(null)}
      />

      <Toast 
        message={toastMessage}
        onClose={() => setToastMessage(null)}
      />
    </div>
  )
}

export default App
