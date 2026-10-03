import { useState, useEffect, useRef } from 'react';
import { api, ApiError, type UserProfile, type AnalysisDetail, type AnalysisSummary, type SourceHealth } from './api';
import { AuthModal } from './components/AuthModal';
import { ResultCard } from './components/ResultCard';
import {
  ShieldCheck,
  TrendingUp,
  Search,
  Link as LinkIcon,
  Image as ImageIcon,
  Mic,
  Clock,
  LogOut,
  User as UserIcon,
  Activity,
  AlertCircle,
  BookOpen,
  LifeBuoy,
  Info,
  Trash2
} from 'lucide-react';
import { LearnPage } from './pages/LearnPage';
import { RightsPage } from './pages/RightsPage';
import { uiCopy } from './uiCopy';

export function App() {
  const [activePage, setActivePage] = useState<'check' | 'checks' | 'learn' | 'rights' | 'about'>('check');
  const [user, setUser] = useState<UserProfile | null>(null);
  const [language, setLanguage] = useState<UserProfile['language']>('EN');
  const [knowledgeLevel, setKnowledgeLevel] = useState<UserProfile['knowledge_level']>('BEGINNER');
  const [preferencesSaving, setPreferencesSaving] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'text' | 'url' | 'image' | 'audio'>('text');
  const [inputText, setInputText] = useState('');
  const [inputUrl, setInputUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisDetail | null>(null);
  const [history, setHistory] = useState<AnalysisSummary[]>([]);
  const [sources, setSources] = useState<SourceHealth[]>([]);
  const [sourceError, setSourceError] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const copy = uiCopy(language);

  // Restore existing session
  useEffect(() => {
    const token = api.getToken();
    if (token) {
      api.getProfile()
        .then((profile) => {
          setUser(profile);
          setLanguage(profile.language);
          setKnowledgeLevel(profile.knowledge_level);
        })
        .catch((error: unknown) => {
          if (error instanceof ApiError && error.status === 401) {
            api.clearToken();
            setErrorMessage('Your session has expired. Sign in again to continue.');
            return;
          }
          setErrorMessage(error instanceof Error ? error.message : 'Could not restore your session.');
        });
    }
    // Fetch source health
    api.getSourceHealth()
      .then(setSources)
      .catch(() => setSourceError('Source status is unavailable right now. Use the official links below; no claim verification was performed.'));
  }, []);

  const loadHistory = async () => {
    try {
      const items = await api.getHistory();
      setHistory(items);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Could not load your saved checks.');
    }
  };

  // Fetch history when user logged in
  useEffect(() => {
    let isMounted = true;
    if (user) {
      api.getHistory()
        .then((items) => {
          if (isMounted) setHistory(items);
        })
        .catch((error: unknown) => {
          if (isMounted) {
            setErrorMessage(error instanceof Error ? error.message : 'Could not load your saved checks.');
          }
        });
    }
    return () => {
      isMounted = false;
    };
  }, [user]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setShowAuthModal(true);
      return;
    }

    setLoading(true);
    setErrorMessage(null);
    try {
      let res: AnalysisDetail;
      if (activeTab === 'text') {
        if (!inputText.trim()) return;
        res = await api.analyzeText(inputText);
      } else if (activeTab === 'url') {
        if (!inputUrl.trim()) return;
        res = await api.analyzeUrl(inputUrl);
      } else if (activeTab === 'image') {
        if (!selectedFile) { setErrorMessage('Please select an image file.'); return; }
        res = await api.analyzeImage(selectedFile);
        setSelectedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
      } else {
        if (!selectedFile) { setErrorMessage('Please select an audio file.'); return; }
        res = await api.analyzeAudio(selectedFile);
        setSelectedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
      }
      setCurrentAnalysis(res);
      void loadHistory();
    } catch (err: any) {
      setErrorMessage(err.message || 'Verification analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectHistory = async (id: number) => {
    try {
      setLoading(true);
      const detail = await api.getDetail(id);
      setCurrentAnalysis(detail);
    } catch (err: any) {
      setErrorMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteHistory = async (id: number) => {
    if (!window.confirm('Permanently delete this saved check and its evidence?')) return;
    try {
      await api.deleteAnalysis(id);
      setHistory((items) => items.filter((item) => item.id !== id));
      setCurrentAnalysis((current) => current?.id === id ? null : current);
    } catch (err: any) {
      setErrorMessage(err.message || 'Could not delete this check');
    }
  };

  const handleLogout = () => {
    api.clearToken();
    setUser(null);
    setHistory([]);
    setCurrentAnalysis(null);
  };

  const updatePreferences = async (
    nextLanguage: UserProfile['language'],
    nextKnowledgeLevel: UserProfile['knowledge_level'],
  ) => {
    if (!user) {
      setLanguage(nextLanguage);
      setKnowledgeLevel(nextKnowledgeLevel);
      return;
    }
    setPreferencesSaving(true);
    try {
      const updated = await api.updatePreferences(nextLanguage, nextKnowledgeLevel);
      setUser(updated);
      setLanguage(updated.language);
      setKnowledgeLevel(updated.knowledge_level);
    } catch (err: any) {
      setLanguage(user.language);
      setKnowledgeLevel(user.knowledge_level);
      setErrorMessage(err.message || 'Could not save preferences');
    } finally {
      setPreferencesSaving(false);
    }
  };

  return (
    <div className="nivesh-app min-h-screen bg-[#090d0f] text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="nivesh-navbar sticky top-0 z-40 border-b backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-y-3 md:flex-nowrap">
          <div className="flex items-center gap-3">
            <div className="nivesh-brand-mark">
              <ShieldCheck aria-hidden="true" className="h-7 w-7" />
              <TrendingUp aria-hidden="true" className="nivesh-brand-trend h-3.5 w-3.5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg tracking-tight text-white">NiveshShakti</span>
              </div>
              <p className="text-[11px] text-slate-400">
                {copy.tagline}
              </p>
            </div>
          </div>

          <nav className="order-3 flex w-full flex-wrap items-center justify-start gap-1 md:order-none md:w-auto" aria-label="Main navigation">
            {([
              ['check', copy.navCheck, Search],
              ['checks', copy.navChecks, Clock],
              ['learn', copy.navLearn, BookOpen],
              ['rights', copy.navRights, LifeBuoy],
              ['about', copy.navAbout, Info],
            ] as const).map(([page, label, Icon]) => (
              <button
                key={page}
                type="button"
                onClick={() => {
                  setActivePage(page);
                  if (page === 'checks') {
                    window.setTimeout(() => document.getElementById('my-checks')?.scrollIntoView({ behavior: 'smooth' }), 0);
                  }
                }}
                aria-current={activePage === page ? 'page' : undefined}
                className={`inline-flex items-center gap-2 px-3 py-2 text-xs font-semibold transition-colors ${activePage === page ? 'border-b-2 border-emerald-400 text-emerald-300' : 'text-slate-400 hover:text-white'}`}
              >
                <Icon aria-hidden="true" className="h-4 w-4" />{label}
              </button>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <label className="sr-only" htmlFor="language-select">{copy.language}</label>
              <select
                id="language-select"
                aria-label={copy.language}
                disabled={preferencesSaving}
                value={language}
                onChange={(event) => void updatePreferences(event.target.value as UserProfile['language'], knowledgeLevel)}
                className="max-w-28 rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-200"
              >
                <option value="EN">English</option>
                <option value="HI">हिन्दी</option>
                <option value="HINGLISH">Hinglish</option>
              </select>
              <label className="sr-only" htmlFor="knowledge-select">{copy.experience}</label>
              <select
                id="knowledge-select"
                aria-label={copy.experience}
                disabled={preferencesSaving}
                value={knowledgeLevel}
                onChange={(event) => void updatePreferences(language, event.target.value as UserProfile['knowledge_level'])}
                className="max-w-32 rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-200"
              >
                <option value="BEGINNER">{copy.beginner}</option>
                <option value="INTERMEDIATE">{copy.intermediate}</option>
                <option value="ADVANCED">{copy.advanced}</option>
              </select>
            </div>
            {user ? (
              <div className="flex items-center gap-3">
                <div className="text-right hidden sm:block">
                  <div className="text-xs font-semibold text-white">{user.email}</div>
                  <div className="text-[10px] text-emerald-400 font-mono">
                    {user.language} • {user.knowledge_level}
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                  title={copy.signOut}
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowAuthModal(true)}
                className="py-1.5 px-4 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs flex items-center gap-2 transition-all shadow-md shadow-emerald-500/20"
              >
                <UserIcon className="w-4 h-4" />
                {copy.signIn}
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-6xl mx-auto px-4 py-8 flex-1 w-full space-y-8">
        {activePage === 'learn' ? (
          <LearnPage language={language} />
        ) : activePage === 'rights' ? (
          <RightsPage language={language} />
        ) : activePage === 'about' ? (
          <section className="mx-auto max-w-3xl space-y-4 text-left" aria-labelledby="about-title">
            <p className="text-xs font-bold uppercase tracking-wider text-emerald-400">{copy.navAbout}</p>
            <h1 id="about-title" className="text-3xl font-bold text-white">NiveshShakti</h1>
            <p className="text-sm leading-relaxed text-slate-300">{copy.heroDescription}</p>
            <p className="text-sm leading-relaxed text-slate-300">Automated source checks are reported as unavailable unless a documented, authoritative result is actually retrieved. A missing record or unavailable source is not proof of fraud or safety.</p>
            <p className="text-sm leading-relaxed text-slate-300">NiveshShakti is not a regulator and does not provide buy, sell, hold, or return recommendations.</p>
          </section>
        ) : (
          <>
        {/* Hero Section */}
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            {copy.heroTitle}
          </h1>
          <p className="text-sm text-slate-400">
            {copy.heroDescription}
          </p>
        </div>

        {/* Verification Form Card */}
        <div className="nivesh-panel mx-auto max-w-3xl p-6">
          <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-4 mb-4">
            <button
              onClick={() => { setActiveTab('text'); setSelectedFile(null); }}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'text'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Search className="w-3.5 h-3.5" />
              {copy.tabText}
            </button>
            <button
              onClick={() => { setActiveTab('url'); setSelectedFile(null); }}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'url'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <LinkIcon className="w-3.5 h-3.5" />
              {copy.tabUrl}
            </button>
            <button
              onClick={() => { setActiveTab('image'); setSelectedFile(null); }}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'image'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <ImageIcon className="w-3.5 h-3.5" />
              {copy.tabImage}
            </button>
            <button
              onClick={() => { setActiveTab('audio'); setSelectedFile(null); }}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'audio'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Mic className="w-3.5 h-3.5" />
              {copy.tabAudio}
            </button>
          </div>

          <form onSubmit={handleVerify} className="space-y-4">
            {activeTab === 'text' && (
              <div>
                <textarea
                  rows={4}
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder={copy.textPlaceholder}
                  className="w-full p-3.5 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
                />
              </div>
            )}
            {activeTab === 'url' && (
              <div>
                <input
                  type="url"
                  value={inputUrl}
                  onChange={(e) => setInputUrl(e.target.value)}
                  placeholder={copy.urlPlaceholder}
                  className="w-full p-3.5 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
                />
              </div>
            )}
            {activeTab === 'image' && (
              <div className="space-y-3">
                <p className="text-xs text-slate-400">{copy.imageHelp}</p>
                <label className="flex flex-col items-center justify-center gap-2 w-full h-32 border-2 border-dashed border-slate-700 rounded-xl cursor-pointer bg-slate-900/60 hover:border-emerald-500/50 transition-colors">
                  <ImageIcon className="w-6 h-6 text-slate-500" />
                  <span className="text-xs text-slate-400">
                    {selectedFile ? selectedFile.name : copy.chooseImage}
                  </span>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp,image/tiff"
                    className="hidden"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
                  />
                </label>
              </div>
            )}
            {activeTab === 'audio' && (
              <div className="space-y-3">
                <p className="text-xs text-slate-400">{copy.audioHelp}</p>
                <label className="flex flex-col items-center justify-center gap-2 w-full h-32 border-2 border-dashed border-slate-700 rounded-xl cursor-pointer bg-slate-900/60 hover:border-emerald-500/50 transition-colors">
                  <Mic className="w-6 h-6 text-slate-500" />
                  <span className="text-xs text-slate-400">
                    {selectedFile ? selectedFile.name : copy.chooseAudio}
                  </span>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="audio/mpeg,audio/wav,audio/x-wav,audio/mp4,audio/x-m4a,audio/ogg,audio/flac,audio/x-flac"
                    className="hidden"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
                  />
                </label>
              </div>
            )}

            {errorMessage && (
              <div className="p-3 rounded-lg bg-red-950/40 border border-red-800/40 text-red-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {errorMessage}
              </div>
            )}

            <div className="flex flex-wrap items-center justify-between gap-4 pt-1">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span>{copy.journeyLabel}:</span>
                <span className="font-mono text-[11px] text-emerald-400">
                  {copy.journey}
                </span>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="py-2.5 px-6 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm flex items-center gap-2 shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50"
              >
                {loading ? copy.processing : copy.verify}
              </button>
            </div>
          </form>
        </div>

        {/* Current Analysis Result */}
        {currentAnalysis && (
          <div className="max-w-3xl mx-auto">
            <ResultCard analysis={currentAnalysis} language={language} knowledgeLevel={knowledgeLevel} />
          </div>
        )}

        {/* User Check History & Authoritative Sources Health */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {/* History */}
          <div id="my-checks" className="nivesh-panel md:col-span-2 p-5 text-left">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Clock className="w-4 h-4 text-emerald-400" />
                {copy.history}
              </h3>
              {user && (
                <span className="text-xs text-slate-400">
                  {history.length} {copy.historyCount}
                </span>
              )}
            </div>

            {!user ? (
              <div className="p-6 text-center text-xs text-slate-500">
                {copy.signInHistory}
              </div>
            ) : history.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500">
                {copy.noHistory}
              </div>
            ) : (
              <div className="space-y-2">
                {history.map((item) => (
                    <div key={item.id} className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/60 p-2">
                      <button
                        type="button"
                        onClick={() => handleSelectHistory(item.id)}
                        className="flex min-w-0 flex-1 items-center justify-between gap-3 p-1 text-left hover:text-white"
                        aria-label={`Open check ${item.raw_input}`}
                      >
                        <span className="min-w-0">
                          <span className="block truncate text-xs font-medium text-slate-200">{item.raw_input}</span>
                          <span className="text-[10px] text-slate-400">{new Date(item.created_at).toLocaleDateString()}</span>
                        </span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded whitespace-nowrap ${
                          item.status === 'FAILED' ? 'bg-amber-950 text-amber-300' :
                          item.overall_risk_level === 'CRITICAL' ? 'bg-red-950 text-red-300' :
                          item.overall_risk_level === 'HIGH' ? 'bg-orange-950 text-orange-300' :
                          item.overall_risk_level === 'MEDIUM' ? 'bg-yellow-950 text-yellow-300' :
                          'bg-emerald-950 text-emerald-300'
                        }`}>
                          {item.status === 'FAILED' ? 'UNAVAILABLE' : item.overall_risk_level || 'PENDING'}
                        </span>
                      </button>
                      <button
                        type="button"
                        title="Delete check"
                        aria-label={`Delete check ${item.raw_input}`}
                        onClick={() => void handleDeleteHistory(item.id)}
                        className="rounded p-2 text-slate-500 hover:bg-red-950 hover:text-red-300"
                      >
                        <Trash2 aria-hidden="true" className="h-4 w-4" />
                      </button>
                    </div>
                ))}
              </div>
            )}
          </div>

          {/* Authoritative Registry Health Status */}
          <div className="nivesh-panel p-5 text-left">
            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              {copy.sources}
            </h3>
            <div className="space-y-3">
              {sources.length === 0 ? (
                <div className="text-xs text-slate-500" role="status">{sourceError || copy.checkingSources}</div>
              ) : (
                sources.map((src) => (
                  <div key={src.id} className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-slate-200">{src.name}</span>
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        src.health_status === 'AVAILABLE' ? 'bg-emerald-950 text-emerald-400' :
                        src.health_status === 'DEGRADED' ? 'bg-yellow-950 text-yellow-400' :
                        src.health_status === 'UNKNOWN' ? 'bg-slate-100 text-slate-500' :
                        'bg-red-950 text-red-400'
                      }`}>
                        {src.health_status}
                      </span>
                    </div>
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] text-emerald-500 hover:underline block truncate"
                    >
                      {src.url}
                    </a>
                    <p className="mt-2 text-[10px] text-slate-500">Last checked {new Date(src.last_checked_at).toLocaleString()}</p>
                    <p className="text-[10px] text-slate-500">Last successful retrieval {src.last_successful_retrieval_at ? new Date(src.last_successful_retrieval_at).toLocaleString() : 'None recorded'}</p>
                    {src.last_error && <p className="mt-1 text-[10px] text-amber-300">{src.last_error}</p>}
                  </div>
                ))
              )}
            </div>
            <div className="mt-4 p-2.5 rounded-lg bg-slate-900 border border-slate-800/80 text-[11px] text-slate-400 leading-normal">
              <strong>{copy.sources}:</strong> {copy.sourceNote}
            </div>
          </div>
        </div>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="nivesh-footer border-t py-6 text-center text-xs">
        <p className="font-semibold text-slate-700">NiveshShakti</p>
        <p className="text-[11px] mt-1 text-slate-600">
          {copy.footerNote}
        </p>
      </footer>

      {/* Auth Modal */}
      {showAuthModal && (
        <AuthModal
          uiLanguage={language}
          initialLanguage={language}
          initialKnowledgeLevel={knowledgeLevel}
          onSuccess={(u) => {
            setUser(u);
            setLanguage(u.language);
            setKnowledgeLevel(u.knowledge_level);
            setShowAuthModal(false);
          }}
          onClose={() => setShowAuthModal(false)}
        />
      )}
    </div>
  );
}

export default App;
