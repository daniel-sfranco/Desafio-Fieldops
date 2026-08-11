import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthContext";
import { getWorkOrders, PaginatedWorkOrders } from "../api/workOrders";
import { WorkOrder, WorkOrderStatus, WorkOrderPriority, ApiError } from "../types";
import { StatusBadge } from "../components/common/StatusBadge";
import { PriorityBadge } from "../components/common/PriorityBadge";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { 
    Plus,
    RotateCw,
    ChevronLeft,
    ChevronRight,
    CheckSquare,
    History,
    FileText,
    Clock
 } from "lucide-react";

interface WorkOrdersListProps {
    onOpenCreate?: () => void;
    onOpenStatus?: (workOrder: WorkOrder) => void;
    onOpenHistory?: (workOrderId: number) => void;
}

export const WorkOrdersList: React.FC<WorkOrdersListProps> = ({
    onOpenCreate,
    onOpenStatus,
    onOpenHistory,
}) => {
    const { user } = useAuth();

    const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
    const [meta, setMeta] = useState<PaginatedWorkOrders['meta']>({
        page: 1,
        limit: 10,
        total: 0,
        totalPages: 0
    });
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<ApiError | null>(null);
    const [statusFilter, setStatusFilter] = useState<WorkOrderStatus | ''>('');
    const [priorityFilter, setPriorityFilter] = useState<WorkOrderPriority | ''>('');
    const [sortBy, setSortBy] = useState<string>('createdAt:desc');
    const [perPage, setPerPage] = useState<number>(10);
    const [currentPage, setCurrentPage] = useState<number>(1);

    const fetchWorkOrders = useCallback(async () => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await getWorkOrders({
                page: currentPage,
                perPage: perPage,
                status: statusFilter || undefined,
                priority: priorityFilter || undefined,
                sort: sortBy
            });

            setWorkOrders(response.data);
            setMeta(response.meta);
        } catch (err: any) {
            setError(err as ApiError);
        } finally {
            setIsLoading(false);
        }
    }, [currentPage, perPage, statusFilter, priorityFilter, sortBy]);

    useEffect(() => {
        fetchWorkOrders();
    }, [fetchWorkOrders]);

    const handleFilterChange = (setter: React.Dispatch<React.SetStateAction<any>>, value: any) => {
        setter(value);
        setCurrentPage(1);
    };

    const canCreate = user?.role === 'admin' || user?.role === 'supervisor';

      return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Topo: Título + Botão de Nova OS */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2>Ordens de Serviço</h2>
          <p style={{ fontSize: '0.875rem' }}>
            {user?.role === 'technician' 
              ? 'Exibindo as ordens de serviço atribuídas a você' 
              : `Gerenciamento de ordens de serviço ${user?.teamId ? `• Equipe: ${user.teamId}` : '• Visão Global'}`}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button 
            className="btn btn-secondary" 
            onClick={fetchWorkOrders} 
            disabled={isLoading}
            title="Atualizar lista"
          >
            <RotateCw size={16} className={isLoading ? 'spin' : ''} /> Atualizar
          </button>
          {canCreate && (
            <button className="btn btn-primary" onClick={onOpenCreate}>
              <Plus size={16} /> Nova Ordem de Serviço
            </button>
          )}
        </div>
      </div>
      {/* Alerta de Erro */}
      <ErrorAlert error={error} onDismiss={() => setError(null)} />

      {/* Barra de Filtros */}
      <div className="card" style={{ padding: '1rem', display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
        {/* Filtro Status */}
        <div style={{ flex: '1 1 180px' }}>
          <label className="label" style={{ fontSize: '0.75rem', marginBottom: '0.25rem', display: 'block' }}>Status</label>
          <select 
            className="select" 
            value={statusFilter} 
            onChange={(e) => handleFilterChange(setStatusFilter, e.target.value)}
          >
            <option value="">Todos os Status</option>
            <option value="open">Aberta</option>
            <option value="in_progress">Em Andamento</option>
            <option value="done">Concluída</option>
          </select>
        </div>
        {/* Filtro Prioridade */}
        <div style={{ flex: '1 1 180px' }}>
          <label className="label" style={{ fontSize: '0.75rem', marginBottom: '0.25rem', display: 'block' }}>Prioridade</label>
          <select 
            className="select" 
            value={priorityFilter} 
            onChange={(e) => handleFilterChange(setPriorityFilter, e.target.value)}
          >
            <option value="">Todas as Prioridades</option>
            <option value="low">Baixa</option>
            <option value="high">Alta</option>
          </select>
        </div>
        {/* Ordenação */}
        <div style={{ flex: '1 1 180px' }}>
          <label className="label" style={{ fontSize: '0.75rem', marginBottom: '0.25rem', display: 'block' }}>Ordenação</label>
          <select 
            className="select" 
            value={sortBy} 
            onChange={(e) => handleFilterChange(setSortBy, e.target.value)}
          >
            <option value="createdAt:desc">Mais recentes primeiro</option>
            <option value="createdAt:asc">Mais antigas primeiro</option>
            <option value="priority:asc">Maior prioridade</option>
            <option value="priority:desc">Menor prioridade</option>
          </select>
        </div>

        {/* Itens por página */}
        <div style={{ flex: '0 1 140px' }}>
          <label className="label" style={{ fontSize: '0.75rem', marginBottom: '0.25rem', display: 'block' }}>Por página</label>
          <select 
            className="select" 
            value={perPage} 
            onChange={(e) => handleFilterChange(setPerPage, Number(e.target.value))}
          >
            <option value={10}>10 por página</option>
            <option value={20}>20 por página</option>
            <option value={50}>50 por página</option>
          </select>
        </div>
      </div>
      {/* Conteúdo: Lista de Ordens ou Estados Visuais */}
      {isLoading ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <RotateCw size={32} color="var(--primary)" style={{ animation: 'spin 1s linear infinite' }} />
          <p style={{ marginTop: '1rem' }}>Carregando ordens de serviço...</p>
        </div>
      ) : workOrders.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <FileText size={48} color="var(--text-dim)" style={{ marginBottom: '1rem' }} />
          <h3>Nenhuma ordem de serviço encontrada</h3>
          <p style={{ marginTop: '0.5rem' }}>
            Tente ajustar os filtros acima ou crie uma nova ordem de serviço.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {workOrders.map((wo) => {
            const completedTasks = wo.checkList?.filter((c) => c.completed).length || 0;
            const totalTasks = wo.checkList?.length || 0;
            return (
              <div key={wo.id} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                      <span style={{ fontSize: '0.8125rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                        #{wo.id}
                      </span>
                      <h3 style={{ fontSize: '1.125rem', margin: 0 }}>{wo.title}</h3>
                    </div>
                    {wo.description && (
                      <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                        {wo.description}
                      </p>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <StatusBadge status={wo.status} />
                    <PriorityBadge priority={wo.priority} />
                  </div>
                </div>

                {/* Metadados e Ações */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-color)', fontSize: '0.8125rem', color: 'var(--text-dim)' }}>
                  <div style={{ display: 'flex', gap: '1.25rem', flexWrap: 'wrap' }}>
                    <span>Equipe: <strong style={{ color: 'var(--text-main)' }}>{wo.teamId}</strong></span>
                    <span>Técnico: <strong style={{ color: 'var(--text-main)' }}>{wo.assigneeId ? `ID #${wo.assigneeId}` : 'Não atribuído'}</strong></span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Clock size={14} /> {new Date(wo.createdAt).toLocaleDateString('pt-BR')}
                    </span>
                    {totalTasks > 0 && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: completedTasks === totalTasks ? '#34d399' : 'inherit' }}>
                        <CheckSquare size={14} /> Checklist: {completedTasks}/{totalTasks}
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button 
                      className="btn btn-outline btn-sm" 
                      onClick={() => onOpenHistory?.(wo.id)}
                      title="Ver histórico de auditoria"
                    >
                      <History size={14} /> Histórico
                    </button>
                    <button 
                      className="btn btn-primary btn-sm" 
                      onClick={() => onOpenStatus?.(wo)}
                    >
                      Detalhes / Alterar
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Paginação */}
      {!isLoading && meta.totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
          <span style={{ fontSize: '0.875rem', color: 'var(--text-dim)' }}>
            Página <strong>{meta.page}</strong> de <strong>{meta.totalPages}</strong> ({meta.total} ordens no total)
          </span>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              className="btn btn-secondary btn-sm"
              disabled={meta.page <= 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            >
              <ChevronLeft size={16} /> Anterior
            </button>
            <button
              className="btn btn-secondary btn-sm"
              disabled={meta.page >= meta.totalPages}
              onClick={() => setCurrentPage((p) => p + 1)}
            >
              Próxima <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
