import { apiClient } from "./client";
import { 
    WorkOrder,
    WorkOrderEvent,
    ChecklistItem,
    WorkOrderStatus,
    WorkOrderPriority
} from "../types";

export interface WorkOrderFilters {
    page?: number;
    perPage?: number;
    status?: WorkOrderStatus;
    priority?: WorkOrderPriority;
    sort?: string;
}

export interface PaginatedWorkOrders {
    data: WorkOrder[];
    meta: {
        page: number;
        limit: number;
        total: number;
        totalPages: number;
    };
}

export interface CreateWorkOrderData {
    title: string;
    description?: string;
    priority: WorkOrderPriority;
    teamId: string;
    assigneeId: number | null;
    initialChecklist: { label: string }[];
}

export interface UpdateWorkOrderData {
    title?: string;
    description?: string;
    status?: WorkOrderStatus;
    priority?: WorkOrderPriority;
    assigneeId?: number | null;
    resolutionNotes?: string;
    version?: number;
}

export async function getWorkOrders(filters: WorkOrderFilters = {}): Promise<PaginatedWorkOrders> {
    const queryParams = new URLSearchParams();

    if (filters.page) queryParams.append('page', String(filters.page));
    if (filters.perPage) queryParams.append('perPage', String(filters.perPage));
    if (filters.status) queryParams.append('status', String(filters.status));
    if (filters.priority) queryParams.append('priority', String(filters.priority));
    if (filters.sort) queryParams.append('sort', String(filters.sort));

    const queryString = queryParams.toString();
    const endpoint = `/work-orders${queryString ?  `?${queryString}` : ''}`

    return apiClient<PaginatedWorkOrders>(endpoint, {
        method: 'GET',
    });
}

export async function getWorkOrderById(id: number): Promise<WorkOrder> {
    return apiClient<WorkOrder>(`/work-orders/${id}`, {
        method: 'GET'
    });
}

export async function createWorkOrder(data: CreateWorkOrderData): Promise<WorkOrder> {
    return apiClient<WorkOrder>(`/work-orders`, {
        method: 'POST',
        data,
    });
}

export async function updateWorkOrder(id: number, data: UpdateWorkOrderData): Promise<WorkOrder> {
    return apiClient<WorkOrder>(`/work-orders/${id}`, {
        method: 'PATCH',
        data,
    });
}

export async function deleteWorkOrder(id: number): Promise<void> {
    return apiClient<void>(`/work-orders/${id}`, {
        method: 'DELETE'
    });
}

export async function getWorkOrderHistory(id: number): Promise<WorkOrderEvent[]> {
    return apiClient<WorkOrderEvent[]>(`/work-orders/${id}/history`, {
        method: 'GET'
    });
}

export async function updateChecklistItem (
    workOrderId: number,
    checklistId: number,
    data: {label?: string; completed?: boolean }
): Promise<ChecklistItem> {
    return apiClient<ChecklistItem>(`/work-orders/${workOrderId}/checklist/${checklistId}`, {
        method: 'PATCH',
        data,
    });
}
