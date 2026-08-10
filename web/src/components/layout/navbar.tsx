import React from "react";
import { useAuth } from '../../contexts/AuthContext';
import { LogOut, Wrench } from "lucide-react";

export const Navbar: React.FC = () => {
    const { user, logout } = useAuth();

    if (!user) return null;

    const roleNames = {
        admin: 'Administrador',
        supervisor: 'Supervisor',
        technician: 'Técnico'
    }

    return (
          <header style={{ borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--bg-card)' }}>
            <div className="main-content" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <Wrench color="var(--primary)" size={24} />
                    <h2 style={{ fontSize: '1.25rem', margin: 0 }}>FieldOps</h2>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>{user.name}</div>
                            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                                <span className={`badge badge-role-${user.role}`}>
                                    {
                                        // roleNames[user.role]
                                    }
                                </span>
                                {user.teamId && (
                                    <span className="badge badge-low" style={{ fontSize: '0.7rem' }}>
                                        {user.teamId}
                                    </span>
                                )}
                            </div>
                        </div>
                        <button className="btn btn-secondary btn-sm" onClick={logout} title="Sair da conta">
                            <LogOut size={16} /> Sair
                        </button>
                    </div>
                </div>
            </header>
    )
}