import type { components } from './schema';

export type UserRole = components['schemas']['UsuarioRole'];
export type WorkOrderStatus = components['schemas']['Status'];
export type WorkOrderPriority = components['schemas']['Priority'];

export type ChecklistItem = components['schemas']['ChecklistItemResponse'];
export type WorkOrder = components['schemas']['WorkOrderResponse'];
export type WorkOrderEvent = components['schemas']['WorkOrderEventResponse'];

export type WorkOrderCreate = components['schemas']['WorkOrderCreate'];
export type WorkOrderUpdate = components['schemas']['WorkOrderUpdate'];

export interface User {
    id: number;
    email: string;
    name: string;
    role: UserRole;
    teamId?: string | null;
}


export interface ApiError {
    code: string;
    message: string;
    flxTraceId: string;
    statusCode: number;
}