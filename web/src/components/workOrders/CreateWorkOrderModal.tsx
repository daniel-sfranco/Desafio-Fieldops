import React, { useState, useEffect } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { createWorkOrder } from "../../api/workOrders";
import { WorkOrderPriority, ApiError } from "../../types";
import { ErrorAlert } from "../common/ErrorAlert";
import { Plus, Trash2, X, CheckSquare } from "lucide-react";

interface CreateWorkOrderModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

export const CreateWorkOrderModal: React.FC<CreateWorkOrderModalProps> = ({
    isOpen,
    onClose,
    onSuccess,
}) => {
    const { user } = useAuth();

    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [priority, setPriority] = useState<WorkOrderPriority>('low');
    const [teamId, setTeamId] = useState('');
    const [assigneeId, setAssigneeId] = useState<string>('');
    const [checklistItems, setChecklistItems] = useState<string[]>(['Verificação inicial']);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<ApiError | null>(null);

    useEffect(() => {
        if (isOpen) {
            if (user?.role === 'supervisor' && user.teamId) {
                setTeamId(user.teamId);
            } else {
                setTeamId('team-alpha');
            }
            setError(null);
        }
    }, [isOpen, user]);

    if (!isOpen) return null;

    const handleAddChecklistItem = () => {
        setChecklistItems([...checklistItems, '']);
    };

    const handleUpdateChecklistItem = (index: number, value: string) => {
        const updated = [...checklistItems];
        updated[index] = value;
        setChecklistItems(updated);
    };

    const handleRemoveChecklistItem = (index: number) => {
        if (checklistItems.length <= 1) return; // Mínimo 1 item
        setChecklistItems(checklistItems.filter((_, i) => i !== index));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        const validItems = checklistItems
                            .map(item => item.trim())    
                            .filter(item => item.length > 0);
        if (validItems.length === 0) {
            setError({
                code: 'FLX_VALIDATION_ERROR',
                message: 'A ordem de serviço deve conter pelo menos 1 item no checklist.',
                flxTraceId: '',
                statusCode: 422
            });
            return;
        }

        setIsLoading(true);

        try {
            await createWorkOrder({
                title: title.trim(),
                description: description.trim() || undefined,
                priority,
                teamId: teamId.trim(),
                assigneeId: assigneeId ? Number(assigneeId) : null,
                initialChecklist: validItems.map(label => ({ label })),
            });

            setTitle('');
            setDescription('');
            setPriority('low');
            setAssigneeId('');
            setChecklistItems(['Verificação inicial']);

            onSuccess();
            onClose();
        } catch (err: any) {
            setError(err as ApiError);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                {/* Cabeçalho */}
                <div className="modal-header">
                    <h3 style={{ margin: 0 }}>Nova Ordem de Serviço</h3>
                    <button className="btn btn-outline btn-sm" onClick={onClose}>
                        <X size={16} />
                    </button>
                </div>
                {/* Formulário */}
                <form onSubmit={handleSubmit}>
                    <div className="modal-body">
                        <ErrorAlert error={error} onDismiss={() => setError(null)} />
                        {/* Título */}
                        <div className="form-group">
                            <label className="label">Título da OS *</label>
                            <input
                                type="text"
                                className="input"
                                placeholder="Ex: Manutenção preventiva no gerador"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                required
                            />
                        </div>
                        {/* Descrição */}
                        <div className="form-group">
                            <label className="label">Descrição detalhada</label>
                            <textarea
                                className="textarea"
                                placeholder="Descreva o problema ou o serviço a ser realizado..."
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                            />
                        </div>

                        {/* Grid: Prioridade + Equipe */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div className="form-group">
                                <label className="label">Prioridade</label>
                                <select
                                    className="select"
                                    value={priority}
                                    onChange={(e) => setPriority(e.target.value as WorkOrderPriority)}
                                >
                                <option value="low">Baixa</option>
                                <option value="high">Alta</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="label">Equipe (teamId) *</label>
                                <input
                                    type="text"
                                    className="input"
                                    value={teamId}
                                    onChange={(e) => setTeamId(e.target.value)}
                                    disabled={user?.role === 'supervisor'}
                                    required
                                />
                            </div>
                        </div>
                        {/* ID do Técnico (Opcional) */}
                        <div className="form-group">
                            <label className="label">ID do Técnico Designado (Opcional)</label>
                            <input
                                type="number"
                                className="input"
                                placeholder="Ex: 1 (tech-a) ou 2 (tech-b)"
                                value={assigneeId}
                                onChange={(e) => setAssigneeId(e.target.value)}
                            />
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                                Dica: ID 1 para tech-a (team-alpha) ou ID 2 para tech-b (team-beta).
                            </span>
                        </div>
                        {/* Checklist Inicial */}
                        <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                                <label className="label" style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', margin: 0 }}>
                                    <CheckSquare size={16} color="var(--primary)" /> Checklist Inicial (Mínimo 1 item) *
                                </label>
                                <button
                                    type="button"
                                    className="btn btn-outline btn-sm"
                                    onClick={handleAddChecklistItem}
                                >
                                    <Plus size={14} /> Adicionar Item
                                </button>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                {checklistItems.map((item, index) => (
                                    <div key={index} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                        <input
                                            type="text"
                                            className="input"
                                            placeholder={`Tarefa ${index + 1}`}
                                            value={item}
                                            onChange={(e) => handleUpdateChecklistItem(index, e.target.value)}
                                            required
                                        />
                                        {checklistItems.length > 1 && (
                                        <button
                                            type="button"
                                            className="btn btn-outline btn-sm"
                                            style={{ color: 'var(--danger)', borderColor: 'transparent' }}
                                            onClick={() => handleRemoveChecklistItem(index)}
                                            title="Remover item">
                                            <Trash2 size={16} />
                                        </button>
                                    )}
                                </div>
                                ))}
                            </div>
                        </div>
                    </div>
                    {/* Rodapé */}
                    <div className="modal-footer">
                        <button type="button" className="btn btn-secondary" onClick={onClose} disabled={isLoading}>
                            Cancelar
                        </button>
                        <button type="submit" className="btn btn-primary" disabled={isLoading}>
                            {isLoading ? 'Criando...' : 'Criar Ordem de Serviço'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}