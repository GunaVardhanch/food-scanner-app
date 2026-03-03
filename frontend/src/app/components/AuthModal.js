"use client";
import { useState } from 'react';

const API_BASE_URL = typeof process.env.NEXT_PUBLIC_API_URL === 'string'
    ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, '')
    : 'http://127.0.0.1:7860';

export default function AuthModal({ onClose, onAuth }) {
    const [mode, setMode] = useState('login'); // 'login' | 'register'
    const [form, setForm] = useState({ name: '', email: '', password: '' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const update = (k, v) => setForm(f => ({ ...f, [k]: v }));

    const submit = async () => {
        setError('');
        if (!form.email || !form.password) { setError('Email and password required.'); return; }
        if (mode === 'register' && !form.name) { setError('Name required.'); return; }
        setLoading(true);
        try {
            const url = `${API_BASE_URL}/auth/${mode}`;
            const body = mode === 'register'
                ? { name: form.name, email: form.email, password: form.password }
                : { email: form.email, password: form.password };
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const data = await res.json();
            if (!res.ok) { setError(data.error || 'Something went wrong.'); return; }
            localStorage.setItem('ns_token', data.token);
            localStorage.setItem('ns_user', JSON.stringify(data.user));
            onAuth(data.user, data.token);
            onClose();
        } catch (e) {
            setError('Network error. Is the backend running?');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-xl z-[100] flex items-center justify-center p-6">
            <div className="w-full max-w-sm bg-white rounded-[32px] shadow-2xl overflow-hidden">
                {/* Header */}
                <div className="bg-gradient-to-br from-[#3a3f85] to-[#6c63ff] p-8 text-white text-center">
                    <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center text-3xl mx-auto mb-4">🍎</div>
                    <h2 className="text-2xl font-black tracking-tight">NutriScanner</h2>
                    <p className="text-white/70 text-xs mt-1 font-medium">Your personal food intelligence</p>
                </div>

                {/* Tab toggle */}
                <div className="flex bg-slate-100 m-5 rounded-2xl p-1">
                    {['login', 'register'].map(m => (
                        <button key={m} onClick={() => { setMode(m); setError(''); }}
                            className={`flex-1 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all ${mode === m ? 'bg-[#3a3f85] text-white shadow' : 'text-slate-400'}`}>
                            {m === 'login' ? '🔑 Sign In' : '✨ Register'}
                        </button>
                    ))}
                </div>

                <div className="px-5 pb-6 space-y-3">
                    {mode === 'register' && (
                        <input type="text" placeholder="Your name" value={form.name}
                            onChange={e => update('name', e.target.value)}
                            className="w-full px-4 py-3.5 rounded-2xl border-2 border-slate-100 bg-slate-50 text-sm font-medium text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-[#6c63ff]/50 focus:bg-white transition-all" />
                    )}
                    <input type="email" placeholder="Email address" value={form.email}
                        onChange={e => update('email', e.target.value)}
                        className="w-full px-4 py-3.5 rounded-2xl border-2 border-slate-100 bg-slate-50 text-sm font-medium text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-[#6c63ff]/50 focus:bg-white transition-all" />
                    <input type="password" placeholder="Password" value={form.password}
                        onChange={e => update('password', e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && submit()}
                        className="w-full px-4 py-3.5 rounded-2xl border-2 border-slate-100 bg-slate-50 text-sm font-medium text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-[#6c63ff]/50 focus:bg-white transition-all" />

                    {error && (
                        <div className="bg-red-50 border border-red-100 rounded-2xl px-4 py-3 text-xs text-red-600 font-bold">{error}</div>
                    )}

                    <button onClick={submit} disabled={loading}
                        className="w-full h-14 bg-gradient-to-r from-[#3a3f85] to-[#6c63ff] text-white rounded-2xl font-black text-sm uppercase tracking-widest shadow-lg shadow-blue-500/20 active:scale-98 transition-all disabled:opacity-60 flex items-center justify-center gap-2">
                        {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : mode === 'login' ? 'Sign In' : 'Create Account'}
                    </button>

                    <button onClick={onClose}
                        className="w-full py-3 text-slate-400 text-xs font-black uppercase tracking-widest hover:text-slate-600 transition-colors">
                        Continue as Guest
                    </button>
                </div>
            </div>
        </div>
    );
}
