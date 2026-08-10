import React from 'react';
import { WorkOrderPriority } from '../../types';

interface PriorityBadgeProps {
    priority: WorkOrderPriority
}

const priorityLabels: Record<WorkOrderPriority, string> = {
    low: 'Baixa',
    medium: 'Média',
    high: 'Alta',
}

export const priorityBadge: React.FC<PriorityBadgeProps> = ({ priority }) => {
    return (
        <span className={`badge badge-${priority}`}>
            { priorityLabels[priority] || priority}
        </span>
    );
};