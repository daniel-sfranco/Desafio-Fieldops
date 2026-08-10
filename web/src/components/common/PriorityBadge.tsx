import React from 'react';
import { WorkOrderPriority } from '../../types';

interface PriorityBadgeProps {
    priority: WorkOrderPriority
}

const priorityLabels: Record<WorkOrderPriority, string> = {
    low: 'Baixa',
    high: 'Alta',
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority }) => {
    return (
        <span className={`badge badge-${priority}`}>
            { priorityLabels[priority] || priority}
        </span>
    );
};