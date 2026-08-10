export type UserRole = 'technician' | 'supervisor' | 'admin';
export type WorkOrderStatus = 'open' | 'in_progress' | 'done';
export type WorkOrderPriority = 'low' | 'medium' | 'high';

export interface User {
    id: number;
    email: string;
    name: string;
    role: UserRole;
    teamId?: string | null;
}

export interface ChecklistItem {
    id: number;
    workOrderId: number;
    label: string;
    completed: boolean;
}

export interface WorkOrder {
    id: number;
    title: string;
    description?: string | null;
    status: WorkOrderStatus;
    priority: WorkOrderPriority;
    resolutionNotes?: string | null;
    assigneeId?: number | null;
    teamId: string;
    version: number;
    createdAt: string;
    updatedAt: string;
    checklist?: ChecklistItem[];
}

export interface WorkOrderEvent {
    id: number;
    workOrderId: number;
    actorId: number;
    fromStatus?: WorkOrderStatus | null;
    toStatus: WorkOrderStatus;
    createdAt: string;
}

export interface ApiError {
    code: string;
    message: string;
    flxTraceId: string;
    statusCode: number;
}