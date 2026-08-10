import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { ApiError } from "../types";
import { Wrench, Shield, UserCheck, HardHat } from "lucide-react";

export const Login: React.FC = () => {
    const { login } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<ApiError | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);

        try {
            await login(email, password);
        } catch (err: any) {
            setError(err as ApiError);
        } finally {
            setIsLoading(false);
        }
    };

    const handleQuickLogin = async (quickEmail: string) => {
        setEmail(quickEmail);
        setPassword('password123');
        setError(null);
        setIsLoading(true);

        try {
            await login(quickEmail, 'password123');
        } catch (err: any) {
            setError(err as ApiError);
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
            <div className="card" style={{ maxWidth: '440px', width: '100%' }}>
                {/* Cabeçalho */}
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <div style={{ display: 'inline-flex', padding: '0.75rem', borderRadius: 'var(--radius-lg)', backgroundColor: 'var(--primary-subtle)', marginBottom: '1rem' }}>
                    <Wrench size={36} color="var(--primary)" />
                </div>
                <h2>FieldOps</h2>
                <p style={{ fontSize: '0.875rem', marginTop: '0.25rem' }}>
                    Gestão inteligente de ordens de serviço
                </p>
                </div>
                {/* Alerta de Erro */}
                <ErrorAlert error={error} onDismiss={() => setError(null)} />
                {/* Formulário */}
                <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label className="label">E-mail</label>
                    <input
                    type="email"
                    className="input"
                    placeholder="seu.email@fieldops.eval"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    />
                </div>
                <div className="form-group">
                    <label className="label">Senha</label>
                    <input
                    type="password"
                    className="input"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    />
                </div>
                <button
                    type="submit"
                    className="btn btn-primary"
                    style={{ width: '100%', marginTop: '0.5rem' }}
                    disabled={isLoading}
                >
                    {isLoading ? 'Entrando...' : 'Entrar no Sistema'}
                </button>
                </form>
                {/* Seção de Atalhos (Seed Users) */}
                <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)' }}>
                    <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)', textAlign: 'center', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Acesso Rápido (Usuários de Teste)
                    </p>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                        <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleQuickLogin('tech-a@fieldops.eval')}
                        >
                        <HardHat size={14} color="#6ee7b7" /> Técnico A
                        </button>
                        <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleQuickLogin('tech-b@fieldops.eval')}
                        >
                        <HardHat size={14} color="#6ee7b7" /> Técnico B
                        </button>
                        <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleQuickLogin('supervisor-a@fieldops.eval')}
                        >
                        <UserCheck size={14} color="#93c5fd" /> Supervisor
                        </button>
                        <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleQuickLogin('admin@fieldops.eval')}
                        >
                        <Shield size={14} color="#d8b4fe" /> Admin
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}