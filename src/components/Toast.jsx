import React, { createContext, useContext, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const ToastContext = createContext();

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info', duration = 4000) => {
    const id = Date.now() + Math.random();
    const toast = { id, message, type, duration };

    setToasts(prev => [...prev, toast]);

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }

    return id;
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const success = useCallback((message, duration) => {
    return addToast(message, 'success', duration);
  }, [addToast]);

  const error = useCallback((message, duration) => {
    return addToast(message, 'error', duration);
  }, [addToast]);

  const warning = useCallback((message, duration) => {
    return addToast(message, 'warning', duration);
  }, [addToast]);

  const info = useCallback((message, duration) => {
    return addToast(message, 'info', duration);
  }, [addToast]);

  const value = {
    success,
    error,
    warning,
    info,
    addToast,
    removeToast
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

function ToastContainer({ toasts, onRemove }) {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 pointer-events-none">
      <AnimatePresence>
        {toasts.map(toast => (
          <Toast
            key={toast.id}
            toast={toast}
            onRemove={() => onRemove(toast.id)}
          />
        ))}
      </AnimatePresence>
    </div>
  );
}

function Toast({ toast, onRemove }) {
  const { type, message } = toast;

  const config = {
    success: {
      icon: CheckCircleIcon,
      bgClass: 'bg-green-50 dark:bg-green-900/20',
      borderClass: 'border-green-200 dark:border-green-800',
      iconClass: 'text-green-500',
      textClass: 'text-green-800 dark:text-green-200'
    },
    error: {
      icon: XCircleIcon,
      bgClass: 'bg-red-50 dark:bg-red-900/20',
      borderClass: 'border-red-200 dark:border-red-800',
      iconClass: 'text-red-500',
      textClass: 'text-red-800 dark:text-red-200'
    },
    warning: {
      icon: ExclamationTriangleIcon,
      bgClass: 'bg-yellow-50 dark:bg-yellow-900/20',
      borderClass: 'border-yellow-200 dark:border-yellow-800',
      iconClass: 'text-yellow-500',
      textClass: 'text-yellow-800 dark:text-yellow-200'
    },
    info: {
      icon: InformationCircleIcon,
      bgClass: 'bg-blue-50 dark:bg-blue-900/20',
      borderClass: 'border-blue-200 dark:border-blue-800',
      iconClass: 'text-blue-500',
      textClass: 'text-blue-800 dark:text-blue-200'
    }
  };

  const typeConfig = config[type] || config.info;
  const Icon = typeConfig.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
      className={`pointer-events-auto flex items-start gap-3 p-4 rounded-lg shadow-lg border ${typeConfig.bgClass} ${typeConfig.borderClass} max-w-md`}
    >
      <Icon className={`h-5 w-5 flex-shrink-0 ${typeConfig.iconClass}`} />
      <p className={`text-sm font-medium flex-1 ${typeConfig.textClass}`}>
        {message}
      </p>
      <button
        onClick={onRemove}
        className={`flex-shrink-0 ${typeConfig.iconClass} hover:opacity-70 transition-opacity`}
      >
        <XMarkIcon className="h-4 w-4" />
      </button>
    </motion.div>
  );
}
