import { useEffect, useState } from 'react';
import './Toast.css';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

interface ToastProps {
  message: string;
  type?: ToastType;
  duration?: number;
  onClose: () => void;
}

export function Toast({ message, type = 'info', duration = 3000, onClose }: ToastProps) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(onClose, 300); // 等待动画完成
    }, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  return (
    <div className={`toast toast-${type} ${visible ? 'toast-visible' : 'toast-hidden'}`}>
      <span className={`toast-icon toast-icon-${type}`}>
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
          {type === 'success' && <path d="M10 0C4.477 0 0 4.477 0 10s4.477 10 10 10 10-4.477 10-10S15.523 0 10 0zm4.707 7.293a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0l-2-2a1 1 0 111.414-1.414L9 11.586l4.293-4.293a1 1 0 011.414 0z" />}
          {type === 'error' && <path d="M10 0C4.477 0 0 4.477 0 10s4.477 10 10 10 10-4.477 10-10S15.523 0 10 0zm3.707 12.293a1 1 0 11-1.414 1.414L10 11.414l-2.293 2.293a1 1 0 11-1.414-1.414L8.586 10 6.293 7.707a1 1 0 111.414-1.414L10 8.586l2.293-2.293a1 1 0 111.414 1.414L11.414 10l2.293 2.293z" />}
          {type === 'warning' && <path d="M10 0L0 18h20L10 0zm0 14a1 1 0 100-2 1 1 0 000 2zm0-4a1 1 0 100-2 1 1 0 000 2z" />}
          {type === 'info' && <path d="M10 0C4.477 0 0 4.477 0 10s4.477 10 10 10 10-4.477 10-10S15.523 0 10 0zm1 14a1 1 0 11-2 0 1 1 0 012 0zm0-6a1 1 0 11-2 0V6a1 1 0 012 0v2z" />}
        </svg>
      </span>
      <span className="toast-message">{message}</span>
    </div>
  );
}

// Toast 容器组件
interface ToastItem {
  id: number;
  message: string;
  type: ToastType;
}

let toastId = 0;
let addToastFn: ((message: string, type: ToastType) => void) | null = null;

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  useEffect(() => {
    addToastFn = (message: string, type: ToastType) => {
      setToasts(prev => [...prev, { id: ++toastId, message, type }]);
    };
    return () => { addToastFn = null; };
  }, []);

  const removeToast = (id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  return (
    <div className="toast-container">
      {toasts.map(toast => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </div>
  );
}

// 便捷函数
export function showToast(message: string, type: ToastType = 'info') {
  if (addToastFn) {
    addToastFn(message, type);
  }
}

export const toast = {
  success: (message: string) => showToast(message, 'success'),
  error: (message: string) => showToast(message, 'error'),
  warning: (message: string) => showToast(message, 'warning'),
  info: (message: string) => showToast(message, 'info'),
};
