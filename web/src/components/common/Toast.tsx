import React, { useEffect } from "react";
import { CheckCircle, X } from "lucide-react";

interface ToastProps {
    message: string | null;
    onClose: () => void;
    duration?: number;
}

export const Toast: React.FC<ToastProps> = ({message, onClose, duration = 4000 }) => {
    useEffect(() => {
        if (message) {
            const timer = setTimeout(() => {
                onClose();
            }, duration);
            return () => clearTimeout(timer);
        }
    }, [message, duration, onClose]);

    if (!message) return null;

      return (
    <div
      style={{
        position: 'fixed',
        bottom: '2rem',
        right: '2rem',
        backgroundColor: '#10b981',
        color: '#ffffff',
        padding: '0.875rem 1.25rem',
        borderRadius: 'var(--radius-md)',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        zIndex: 9999,
        fontSize: '0.875rem',
        fontWeight: 500,
      }}
    >
      <CheckCircle size={18} />
      <span>{message}</span>
      <button
        onClick={onClose}
        style={{
          background: 'none',
          border: 'none',
          color: '#ffffff',
          cursor: 'pointer',
          padding: 0,
          marginLeft: '0.5rem',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        <X size={16} />
      </button>
    </div>
  );
}