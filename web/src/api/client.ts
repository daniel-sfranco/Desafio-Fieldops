import { ApiError } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface RequestOptions extends RequestInit {
    data?: any;
}

export async function apiClient<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { data, headers, ...customConfig} = options;

    const token = localStorage.getItem('fieldops-token');

    const defaultHeaders: HeadersInit = {
        'Content-Type': 'application/json'
    };

    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    const config: RequestInit = {
        ...customConfig,
        headers: {
            ...defaultHeaders,
            ...headers,
        },
    };

    if (data) {
        config.body = JSON.stringify(data);
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    
    if (!response.ok) {
        let errorData: any;
        try {
            errorData = await response.json();
        } catch {
            errorData = null;
        }

        const apiError: ApiError = {
            code: errorData?.error?.code || 'FLX_UNKNOWN_ERROR',
            message: errorData?.error?.message || response.statusText || 'Erro inesperado na requisição.',
            flxTraceId: errorData?.error?.flxTraceId || '',
            statusCode: response.status,
        };

        if (response.status === 401) {
            localStorage.removeItem('fieldops_token')
            localStorage.removeItem('fieldops_user')
        }

        throw apiError;
    }

    if (response.status === 204) {
        return {} as T;
    }

    return response.json();
}