import React, { useState } from 'react';
import { api, type UserProfile } from '../api';
import { ShieldCheck, Lock, Mail, ArrowRight } from 'lucide-react';
import { uiCopy } from '../uiCopy';

interface AuthModalProps {
  onSuccess: (user: UserProfile) => void;
  onClose: () => void;
  uiLanguage: UserProfile['language'];
  initialLanguage: UserProfile['language'];
  initialKnowledgeLevel: UserProfile['knowledge_level'];
}

export const AuthModal: React.FC<AuthModalProps> = ({ onSuccess, onClose, uiLanguage, initialLanguage, initialKnowledgeLevel }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [language, setLanguage] = useState<UserProfile['language']>(initialLanguage);
  const [knowledgeLevel, setKnowledgeLevel] = useState<UserProfile['knowledge_level']>(initialKnowledgeLevel);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const copy = uiCopy(uiLanguage);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isRegister) {
        await api.register({
          email,
          password,
          language,
          knowledge_level: knowledgeLevel
        });
      }
      const tokenRes = await api.login({ email, password });
      api.setToken(tokenRes.access_token);
      const user = await api.getProfile();
      onSuccess(user);
    } catch (err: any) {
      api.clearToken();
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-2xl bg-[#11181c] border border-emerald-950/40 p-6 shadow-2xl relative text-left">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white"
        >
          ✕
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white tracking-wide">
              {isRegister ? copy.authRegisterTitle : copy.authSignInTitle}
            </h2>
            <p className="text-xs text-slate-400">
              {copy.authSubtitle}
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-950/40 border border-red-800/40 text-red-300 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">{copy.email}</label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="investor@example.com"
                className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">{copy.password}</label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="password"
                required
                minLength={10}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
          </div>

          {isRegister && (
            <div className="grid grid-cols-2 gap-3 pt-1">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">{copy.language}</label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value as any)}
                  className="w-full py-2 px-3 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="EN">English</option>
                  <option value="HI">हिन्दी (Hindi)</option>
                  <option value="HINGLISH">Hinglish</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">{copy.experience}</label>
                <select
                  value={knowledgeLevel}
                  onChange={(e) => setKnowledgeLevel(e.target.value as any)}
                  className="w-full py-2 px-3 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="BEGINNER">{copy.beginner}</option>
                  <option value="INTERMEDIATE">{copy.intermediate}</option>
                  <option value="ADVANCED">{copy.advanced}</option>
                </select>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-2.5 px-4 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold rounded-lg text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 disabled:opacity-50"
          >
            {loading ? copy.processing : (isRegister ? copy.registerAndVerify : copy.signIn)}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={() => {
              setIsRegister(!isRegister);
              setError(null);
            }}
            className="text-xs text-emerald-400 hover:underline"
          >
            {isRegister ? copy.alreadyAccount : copy.noAccount}
          </button>
        </div>
      </div>
    </div>
  );
};
