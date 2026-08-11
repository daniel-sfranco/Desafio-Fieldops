import React, { useState, useEffect } from "react";
import { getWorkOrderHistory } from "../../api/workOrders";
import { WorkOrderEvent, ApiError } from "../../types";
import { StatusBadge } from "../common/StatusBadge";
import { ErrorAlert } from "../common/ErrorAlert";
import { X, History, RotateCw, Clock, User, ArrowRight, FileText } from "lucide-react";

interface WorkOrderHistoryModalProps {
    workOrderId: number | null;
    isOpen: boolean;
    onClose: () => void;
}

export const WorkOrderHistoryModal: React.FC<WorkOrderHistoryModalProps> = ({
    workOrderId,
    isOpen,
    onClose,
}) => {
    const [events, setEvents] = useState<WorkOrderEvent[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<ApiError | null>(null);

    useEffect(() => {
        if (isOpen && workOrderId) {
            setIsLoading(true);
            setError(null);
            getWorkOrderHistory(workOrderId)
                .then((data) => setEvents(data))
                .catch((err) => setError(err as ApiError))
                .finally(() => setIsLoading(false));
        }
    }, [isOpen, workOrderId]);

    if (!isOpen || !workOrderId) return null;

    return (
        <div className="modal-backdrop" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '520px' }}>
            {/* Cabeçalho */}
            <div className="modal-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <History size={20} color="var(--primary)" />
                <div>
                <span style={{ fontSize: '0.8125rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                    Auditoria de Eventos
                </span>
                <h3 style={{ margin: 0 }}>Histórico da OS #{workOrderId}</h3>
                </div>
            </div>
            <button className="btn btn-outline btn-sm" onClick={onClose}>
                <X size={16} />
            </button>
            </div>

            {/* Corpo com Linha do Tempo */}
            <div className="modal-body">
            <ErrorAlert error={error} onDismiss={() => setError(null)} />

            {isLoading ? (
                <div style={{ textAlign: 'center', padding: '2.5rem 0' }}>
                <RotateCw size={28} color="var(--primary)" style={{ animation: 'spin 1s linear infinite' }} />
                <p style={{ marginTop: '0.75rem', fontSize: '0.875rem', color: 'var(--text-dim)' }}>
                    Carregando histórico...
                </p>
                </div>
            ) : events.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '2.5rem 0' }}>
                <FileText size={36} color="var(--text-dim)" style={{ marginBottom: '0.5rem' }} />
                <p style={{ margin: 0, color: 'var(--text-muted)' }}>Nenhum evento registrado para esta OS.</p>
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', position: 'relative' }}>
                {events.map((event, _) => (
                    <div 
                    key={event.id}
                    style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.5rem',
                        padding: '0.875rem 1rem',
                        backgroundColor: 'var(--bg-subtle)',
                        borderRadius: 'var(--radius-md)',
                        borderLeft: `4px solid ${
                        event.toStatus === 'done' 
                            ? '#10b981' 
                            : event.toStatus === 'in_progress' 
                            ? '#f59e0b' 
                            : 'var(--primary)'
                        }`,
                        position: 'relative'
                    }}
                    >
                    {/* Transição de Status */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                        {event.fromStatus ? (
                        <>
                            <StatusBadge status={event.fromStatus} />
                            <ArrowRight size={14} color="var(--text-dim)" />
                            <StatusBadge status={event.toStatus} />
                        </>
                        ) : (
                        <>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Criação inicial:</span>
                            <StatusBadge status={event.toStatus} />
                        </>
                        )}
                    </div>

                    {/* Metadados: Ator e Horário */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <User size={13} /> Modificado por ID #{event.actorId}
                        </span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <Clock size={13} /> {new Date(event.createdAt).toLocaleString('pt-BR')}
                        </span>
                    </div>
                    </div>
                ))}
                </div>
            )}
            </div>

            {/* Rodapé */}
            <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={onClose}>
                    Fechar
                </button>
            </div>
        </div>
        </div>
    );
}