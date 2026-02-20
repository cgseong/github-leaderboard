import React from 'react';
import { useAuth } from '../context/AuthContext';
import { FaGithub } from 'react-icons/fa';

export const Login: React.FC = () => {
    const { login } = useAuth();

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white">
            <div className="bg-gray-800 p-8 rounded-xl shadow-2xl border border-gray-700 w-full max-w-md text-center">
                <h1 className="text-3xl font-bold mb-2">GitHub Leaderboard</h1>
                <p className="text-gray-400 mb-8">Track your coding journey and compare with peers.</p>

                <button
                    onClick={login}
                    className="w-full px-6 py-3 bg-[#24292e] hover:bg-[#2f363d] text-white rounded-lg font-semibold text-lg transition-colors border border-gray-600 flex items-center justify-center gap-3 shadow-lg"
                >
                    <FaGithub className="text-2xl" />
                    <span>Sign in with GitHub</span>
                </button>

                <div className="mt-8 text-sm text-gray-500">
                    <p>By signing in, you agree to share your GitHub public activity data.</p>
                </div>
            </div>
        </div>
    );
};
