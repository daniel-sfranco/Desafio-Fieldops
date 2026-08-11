import createClient from 'openapi-fetch';
import type { paths } from '../types/schema';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = createClient<paths>({
    baseUrl: API_BASE_URL
})

api.use({
    onRequest({ request }) {
        const token = localStorage.getItem('fieldops_token');
        if (token) {
            request.headers.set('Authorization', `Bearer ${token}`);
        }
        return request;
    }
});
