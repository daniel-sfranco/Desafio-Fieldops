import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { api } from '../api/client';


function parseJwt(token: string) {
    try {
        const base64url = token.split('.')[1];
        const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/')
        const jsonPayload = decodeURIComponent(
            atob(base64)
                .split('')
                .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join('')
        );
        return JSON.parse(jsonPayload)
    } catch { return null; }
}


interface AuthContextData {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextData>({} as AuthContextData);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);

    useEffect(() => {
        const storedToken = localStorage.getItem('fieldops_token');
        const storedUser = localStorage.getItem('fieldops_user');

        if (storedToken && storedUser) {
            setToken(storedToken);
            setUser(JSON.parse(storedUser));
        }
        setIsLoading(false);
    }, []);

    const login = async (email: string, password: string) => {
        const { data, error } = await api.POST('/auth/login', {
            body: { email, password }
        })

        if (error) throw error;

        const accessToken = data.access_token;
        const payload = parseJwt(accessToken);

        if (!payload) {
            throw new Error('Falha ao decodificar token de autenticação.');
        }

        const loggedUser: User = {
            id: Number(payload.sub),
            email: email,
            name:email.split('@')[0],
            role: payload.role,
            teamId: payload.teamId || null,
        };

        localStorage.setItem('fieldops_token', accessToken);
        localStorage.setItem('fieldops_user', JSON.stringify(loggedUser));

        setToken(accessToken);
        setUser(loggedUser);
    };

    const logout = () => {
        localStorage.removeItem('fieldops_token');
        localStorage.removeItem('fieldops_user');
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, isLoading, login, logout}}>
            { children }
        </AuthContext.Provider>
    );
};


export const useAuth = (): AuthContextData => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth deve ser utilizado dentro de um AuthProvider.');
    };
    return context;
}
