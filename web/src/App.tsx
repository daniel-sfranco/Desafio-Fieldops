import './App.css'
import { ErrorAlert } from './components/common/ErrorAlert'
import { ApiError } from './types'

function App() {
  const error: ApiError = {
    code: "Erro de exemplo",
    message: "Esse erro está sendo apresentado na tela",
    flxTraceId: "id de exemplo",
    statusCode: 123
  }
  return (
    <>
      <ErrorAlert error={error}></ErrorAlert>
    </>
  )
}

export default App
