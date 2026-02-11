'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';

export default function LoginPage() {
  const t = useTranslations('auth');
  const common = useTranslations('common');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        setError(t('loginError'));
        return;
      }

      const data = await res.json();
      localStorage.setItem('naruu_token', data.access_token);
      localStorage.setItem('naruu_user', JSON.stringify(data.user));
      window.location.href = '/';
    } catch {
      setError(t('loginError'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-naruu-700">{common('appName')}</h1>
          <p className="text-sm text-gray-500 mt-2">{common('tagline')}</p>
        </div>

        <h2 className="text-xl font-semibold text-gray-900 mb-6">{t('loginTitle')}</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('email')}</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-naruu-500 focus:border-naruu-500 outline-none"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('password')}</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-naruu-500 focus:border-naruu-500 outline-none"
              required
            />
          </div>

          {error && (
            <p className="text-red-600 text-sm">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 px-4 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 disabled:opacity-50 transition-colors font-medium"
          >
            {loading ? common('loading') : t('loginButton')}
          </button>
        </form>
      </div>
    </div>
  );
}
