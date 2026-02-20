import React, { useEffect, useState } from 'react';
import { useSocket } from '../context/SocketContext';
import { FaBell } from 'react-icons/fa';

interface Toast {
    id: number;
    message: string;
}

export const Toaster: React.FC = () => {
    const socket = useSocket();
    const [toasts, setToasts] = useState<Toast[]>([]);

    useEffect(() => {
        if (!socket) return;

        const handleUpdate = (data: any) => {
            const newToast = { id: Date.now(), message: data.message || 'Leaderboard updated' };
            setToasts((prev) => [...prev, newToast]);

            setTimeout(() => {
                setToasts((prev) => prev.filter((t) => t.id !== newToast.id));
            }, 5000);
        };

        socket.on('leaderboard-update', handleUpdate);

        return () => {
            socket.off('leaderboard-update', handleUpdate);
        };
    }, [socket]);

    if (toasts.length === 0) return null;

    return (
        <div className="fixed bottom-4 right-4 flex flex-col gap-2 z-50">
            {toasts.map((toast) => (
                <div
                    key={toast.id}
                    className="bg-gray-800 border border-blue-500 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 animate-bounce"
                >
                    <FaBell className="text-blue-500" />
                    <span>{toast.message}</span>
                </div>
            ))}
        </div>
    );
};
