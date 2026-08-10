import React from 'react';
import { WorkOrderStatus } from '../../types';

interface StatusBadgeProps {
    status: WorkOrderStatus
}

const statusLabels: Record<WorkOrderStatus, string> = {
    open: 'Aberta',
    in_progress: 'Em Andamento',
    done: 'Concluída',
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
    return (
        <span className={`badge badge-${status}`}>
            { statusLabels[status] || status}
        </span>
    );
};