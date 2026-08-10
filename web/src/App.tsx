import './App.css'
import { Navbar } from './components/layout/navbar'
import { useAuth } from './contexts/AuthContext';
import { Login } from './pages/Login';

function App() {
  const { user } = useAuth();

  if (!user) {
    return <Login />
  }

  return (
    <div className="app-container">
      <Navbar />
      <main className="main-content">
        <div className="card">
          <h3>Bem vindo, {user.name}!</h3>
          <p>Seu perfil é: <strong>{user.role}</strong> {user.teamId && `(Equipe: ${user.teamId})`}</p>
        </div>
      </main>
    </div>
  )
}

export default App
