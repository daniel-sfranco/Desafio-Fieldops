import './App.css'
import { Navbar } from './components/layout/navbar'
import { useAuth } from './contexts/AuthContext';
import { Login } from './pages/Login';
import { WorkOrdersList } from './pages/WorkOrdersList';

function App() {
  const { user } = useAuth();

  if (!user) {
    return <Login />
  }

  return (
    <div className="app-container">
      <Navbar />
      <main className="main-content">
        <WorkOrdersList 
          onOpenCreate={() => alert('Modal de criação será aberto aqui')}
          onOpenStatus={(wo) => alert(`Alterar status da OS #${wo.id} (${wo.title})`)}
          onOpenHistory={(id) => alert(`Ver histórico da OS #${id}`)}
        />
      </main>
    </div>
  )
}

export default App
