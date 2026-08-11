import { api } from "./client";
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
    const { data, error } = await api.GET('/work-orders/', {
        params: {
            query: {
                page: filters.page,
                perPage: filters.perPage,
                status: filters.status,
                priority: filters.priority,
                sort: filters.sort,
            }
        }
    })

    if (error) throw error;
    return data;
}

export async function getWorkOrderById(id: number): Promise<WorkOrder> {
    const { data, error } = await api.GET(`/work-orders/{item_id}`, {
        params:{
            path: { item_id: id }
        }
    });

    if (error) throw error;
    return data;
}

export async function createWorkOrder(create_data: CreateWorkOrderData): Promise<WorkOrder> {
    const { data, error } = await api.POST(`/work-orders/`, {
        body: create_data
    });

    if (error) throw error;
    return data;
}

export async function updateWorkOrder(id: number, update_data: UpdateWorkOrderData): Promise<WorkOrder> {
    const { data, error } = await api.PATCH(`/work-orders/{item_id}`, {
        params: {
            path: { item_id: id }
        },
        body: update_data
    });

    if (error) throw error;
    return data;
}

export async function deleteWorkOrder(id: number): Promise<void> {
    const { data, error } = await api.DELETE(`/work-orders/{item_id}`, {
        params: {
            path: { item_id: id }
        },
    });

    if (error) throw error;
    return data;
}

export async function getWorkOrderHistory(id: number): Promise<WorkOrderEvent[]> {
    const { data, error } = await api.GET(`/work-orders/{item_id}/history`, {
        params: {
            path: { item_id: id }
        },
    });

    if (error) throw error;
    return data;
}

export async function updateChecklistItem (
    workOrderId: number,
    checklistId: number,
    update_data: {label?: string; completed?: boolean }
): Promise<ChecklistItem> {
    const { data, error } = await api.PATCH(`/work-orders/{item_id}/checklist/{checklist_id}`, {
        params: {
            path: { 
                item_id: workOrderId,
                checklist_id: checklistId
             }
        },
        body: update_data
    });

    if (error) throw error;
    return data;
}
