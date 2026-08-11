import React, { useState, useEffect } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { updateWorkOrder, updateChecklistItem, deleteWorkOrder } from "../../api/workOrders";
import { WorkOrder, WorkOrderStatus, ChecklistItem, ApiError } from "../../types";
import { StatusBadge } from "../common/StatusBadge";
import { PriorityBadge } from "../common/PriorityBadge";
import { ErrorAlert } from "../common/ErrorAlert";
import { X, CheckSquare, Square, AlertTriangle, Trash2, Check } from "lucide-react";

interface StatusChangeModalProps {
  workOrder: WorkOrder | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const StatusChangeModal: React.FC<StatusChangeModalProps> = ({
  workOrder,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { user } = useAuth();

  const [currentWO, setCurrentWO] = useState<WorkOrder | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<WorkOrderStatus>('open');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [initialChecklist, setInitialChecklist] = useState<ChecklistItem[]>([]);
  const [assigneeId, setAssigneeId] = useState<string>('');
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (workOrder && isOpen) {
      setCurrentWO(workOrder);
      setSelectedStatus(workOrder.status);
      setResolutionNotes(workOrder.resolutionNotes || '');
      const list = workOrder.checkList || [];
      setChecklist(list.map(item => ({ ...item })));
      setInitialChecklist(list.map(item => ({ ...item })));
      setAssigneeId(workOrder.assigneeId ? String(workOrder.assigneeId) : '');
      setError(null);
      setIsDeleting(false);
    }
  }, [workOrder, isOpen]);

  if (!isOpen || !currentWO) return null;

  // Toggle do checklist apenas no estado local do formulário
  const handleToggleChecklist = (item: ChecklistItem) => {
    setChecklist((prev) =>
      prev.map((c) => (c.id === item.id ? { ...c, completed: !c.completed } : c))
    );
  };

  // Verifica se houve alguma alteração (status, assignee, notas ou checklist)
  const isStatusChanged = selectedStatus !== currentWO.status;
  const isAssigneeChanged = user?.role !== 'technician' && assigneeId !== (currentWO.assigneeId ? String(currentWO.assigneeId) : '');
  const isNotesChanged = selectedStatus === 'done' && resolutionNotes.trim() !== (currentWO.resolutionNotes || '').trim();
  const isChecklistChanged = checklist.some((item) => {
    const original = initialChecklist.find((c) => c.id === item.id);
    return original ? original.completed !== item.completed : false;
  });

  const hasChanges = isStatusChanged || isAssigneeChanged || isNotesChanged || isChecklistChanged;

  const handleApplyChanges = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validação de notas para conclusão
    if (selectedStatus === 'done' && resolutionNotes.trim().length < 10) {
      setError({
        code: 'FLX_VALIDATION_ERROR',
        message: 'Notas de resolução são obrigatórias para concluir a OS (mínimo 10 caracteres).',
        flxTraceId: '',
        statusCode: 422,
      });
      return;
    }

    setIsLoading(true);

    try {
      // 1. Salva alterações no checklist no banco
      const changedChecklistItems = checklist.filter((item) => {
        const original = initialChecklist.find((c) => c.id === item.id);
        return original ? original.completed !== item.completed : false;
      });

      for (const item of changedChecklistItems) {
        await updateChecklistItem(currentWO.id, item.id, {
          completed: item.completed,
        });
      }

      // 2. Salva status, assignee e notas de resolução (se alterados)
      if (isStatusChanged || isAssigneeChanged || isNotesChanged) {
        await updateWorkOrder(currentWO.id, {
          status: selectedStatus,
          version: currentWO.version,
          assigneeId: user?.role !== 'technician' ? (assigneeId ? Number(assigneeId) : null) : undefined,
          resolutionNotes: selectedStatus === 'done' ? resolutionNotes.trim() : undefined,
        });
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err as ApiError);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Tem certeza que deseja excluir a OS #${currentWO.id}?`)) {
      return;
    }
    setIsDeleting(true);
    setError(null);
    try {
      await deleteWorkOrder(currentWO.id);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err as ApiError);
      setIsDeleting(false);
    }
  };

  const isTechnician = user?.role === 'technician';
  const isHighPriority = currentWO.priority === 'high';
  const canDelete = user?.role === 'admin' || user?.role === 'supervisor';

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Cabeçalho */}
        <div className="modal-header">
          <div>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
              OS #{currentWO.id} • Versão: {currentWO.version}
            </span>
            <h3 style={{ margin: '0.25rem 0 0 0' }}>{currentWO.title}</h3>
          </div>
          <button className="btn btn-outline btn-sm" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        {/* Corpo */}
        <div className="modal-body">
          <ErrorAlert error={error} onDismiss={() => setError(null)} />

          {/* Conflito de Concorrência Otimista 409 */}
          {error?.code === 'FLX_CONCURRENT_UPDATE' && (
            <div className="alert" style={{ backgroundColor: 'rgba(245, 158, 11, 0.15)', borderColor: 'rgba(245, 158, 11, 0.4)', color: '#fbbf24' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertTriangle size={18} />
                <strong>Conflito de Concorrência Otimista</strong>
              </div>
              <p style={{ fontSize: '0.875rem', marginTop: '0.25rem', color: 'var(--text-main)' }}>
                Esta ordem de serviço foi modificada por outro usuário. Por favor, feche e recarregue a lista.
              </p>
            </div>
          )}

          {/* Badges e Metadados */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
            <StatusBadge status={currentWO.status} />
            <PriorityBadge priority={currentWO.priority} />
            <span className="badge badge-low">Equipe: {currentWO.teamId}</span>
          </div>

          {currentWO.description && (
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              {currentWO.description}
            </p>
          )}

          {/* Checklist Interativo */}
          <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
            <h4 style={{ fontSize: '0.875rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CheckSquare size={16} color="var(--primary)" /> Checklist de Tarefas (Clique para marcar)
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {checklist.length === 0 ? (
                <span style={{ fontSize: '0.8125rem', color: 'var(--text-dim)' }}>Nenhum item cadastrado.</span>
              ) : (
                checklist.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => handleToggleChecklist(item)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                      color: item.completed ? 'var(--text-dim)' : 'var(--text-main)',
                      textDecoration: item.completed ? 'line-through' : 'none',
                      padding: '0.25rem 0',
                    }}
                  >
                    {item.completed ? (
                      <CheckSquare size={16} color="#34d399" />
                    ) : (
                      <Square size={16} color="var(--text-dim)" />
                    )}
                    <span>{item.label}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Formulário de Alterações */}
          <form onSubmit={handleApplyChanges}>
            <div className="form-group">
              <label className="label">Status</label>
              <select
                className="select"
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value as WorkOrderStatus)}
              >
                <option value="open">Aberta (open)</option>
                <option value="in_progress">Em Andamento (in_progress)</option>
                <option 
                  value="done" 
                  disabled={isTechnician && isHighPriority}
                >
                  Concluída (done) {isTechnician && isHighPriority ? '— (Bloqueado p/ Alta Prioridade)' : ''}
                </option>
              </select>
              {isTechnician && isHighPriority && (
                <span style={{ fontSize: '0.75rem', color: '#f87171', marginTop: '0.25rem', display: 'block' }}>
                  ⚠️ Ordens de alta prioridade só podem ser concluídas por Supervisores ou Administradores.
                </span>
              )}
            </div>

            {/* Atribuição de Técnico para Supervisor e Admin */}
            {user?.role !== 'technician' && (
              <div className="form-group">
                <label className="label">
                  Técnico Designado (ID do Técnico) {selectedStatus === 'in_progress' && !currentWO.assigneeId ? '*' : ''}
                </label>
                <input
                  type="number"
                  className="input"
                  placeholder="Ex: 1 (tech-a da team-alpha) ou 2 (tech-b da team-beta)"
                  value={assigneeId}
                  onChange={(e) => setAssigneeId(e.target.value)}
                  required={selectedStatus === 'in_progress' && !currentWO.assigneeId}
                />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                  {selectedStatus === 'in_progress' && !currentWO.assigneeId
                    ? '⚠️ Obrigatório informar um técnico para mover para Em Andamento.'
                    : 'Deixe em branco ou altere para reatribuir a outro técnico da equipe.'}
                </span>
              </div>
            )}

            {/* Campo de Notas de Resolução (Exibido quando "done" é selecionado) */}
            {selectedStatus === 'done' && (
              <div className="form-group">
                <label className="label">Notas de Resolução * (Mínimo 10 caracteres)</label>
                <textarea
                  className="textarea"
                  placeholder="Descreva a solução aplicada e os procedimentos realizados..."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  required
                />
                <span style={{ fontSize: '0.75rem', color: resolutionNotes.trim().length >= 10 ? '#34d399' : 'var(--text-dim)' }}>
                  Caracteres: {resolutionNotes.trim().length}/10
                </span>
              </div>
            )}

            {/* Rodapé de Ações */}
            <div className="modal-footer" style={{ marginTop: '1.5rem', padding: '1rem 0 0 0', backgroundColor: 'transparent', display: 'flex', justifyContent: 'space-between' }}>
              <div>
                {canDelete && (
                  <button
                    type="button"
                    className="btn btn-danger btn-sm"
                    onClick={handleDelete}
                    disabled={isDeleting || isLoading}
                  >
                    <Trash2 size={14} /> Excluir OS
                  </button>
                )}
              </div>

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={onClose} disabled={isLoading}>
                  Cancelar
                </button>
                <button 
                  type="submit" 
                  className="btn btn-primary" 
                  disabled={isLoading || !hasChanges}
                >
                  <Check size={16} /> {isLoading ? 'Salvando...' : 'Aplicar alterações'}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};