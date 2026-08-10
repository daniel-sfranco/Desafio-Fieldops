import React from 'react';
import { ApiError } from '../../types';

interface ErrorAlertProps {
    error: ApiError | null;
    onDismiss?: () => void;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({ error, onDismiss }) => {
  if (!error) return null;
  return (
    <div className="alert alert-error">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <strong>{error.message}</strong>
        {onDismiss && (
          <button className="btn btn-outline btn-sm" onClick={onDismiss}>✕</button>
        )}
      </div>
      <div>
        <span className="alert-code">Código: {error.code}</span>
      </div>
      {error.flxTraceId && (
        <span className="alert-trace">Trace ID: {error.flxTraceId} | Status Code: {error.statusCode}</span>
      )}
    </div>
  );
};