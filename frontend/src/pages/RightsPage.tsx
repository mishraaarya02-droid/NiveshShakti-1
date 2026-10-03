import { useEffect, useState } from 'react';
import { AlertTriangle, ExternalLink, LifeBuoy } from 'lucide-react';
import { api, type GrievanceSituation } from '../api';
import type { UserProfile } from '../types';
import { uiCopy } from '../uiCopy';

export function RightsPage({ language }: { language: UserProfile['language'] }) {
  const copy = uiCopy(language);
  const [situations, setSituations] = useState<GrievanceSituation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api.getGrievanceSituations()
      .then((items) => {
        if (active) setSituations(items);
      })
      .catch(() => {
        if (active) setError('Guidance could not be loaded. Use the official SEBI Investor Support portal directly.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="max-w-5xl mx-auto space-y-6 text-left" aria-labelledby="rights-title">
      <header className="max-w-3xl space-y-3">
        <div className="flex items-center gap-2 text-emerald-400">
          <LifeBuoy aria-hidden="true" className="h-5 w-5" />
          <span className="text-xs font-bold uppercase tracking-wider">Investor support</span>
        </div>
        <h1 id="rights-title" className="text-3xl font-bold text-white">{copy.rightsTitle}</h1>
        <p className="text-sm leading-relaxed text-slate-300">
          {copy.rightsIntro}
        </p>
      </header>

      <aside className="flex gap-3 border border-amber-700/50 bg-amber-950/30 p-4 text-amber-100" role="note">
        <AlertTriangle aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-amber-400" />
        <p className="text-sm">{copy.rightsSafety}</p>
      </aside>
      {language !== 'EN' && <p className="text-xs text-slate-500" role="note">{copy.rightsFallback}</p>}

      {loading && <p className="text-sm text-slate-400" role="status">Loading official guidance…</p>}
      {error && <p className="text-sm text-amber-200" role="alert">{error}</p>}

      <div className="divide-y divide-slate-800 border-y border-slate-800">
        {situations.map((situation) => (
          <details key={situation.id} className="group py-4">
            <summary className="flex cursor-pointer list-none items-start justify-between gap-4 py-1">
              <span>
                <span className="block text-base font-semibold text-white">{language === 'HI' ? situation.title_hindi : situation.title}</span>
                {language === 'EN' && <span className="mt-1 block text-xs text-slate-400">{situation.title_hindi}</span>}
              </span>
              <span className="text-slate-400 group-open:rotate-45" aria-hidden="true">+</span>
            </summary>
            <div className="grid gap-5 pt-4 md:grid-cols-2">
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-slate-200">{language === 'HI' ? situation.description_hindi : situation.description}</p>
                </div>
                <section>
                  <h2 className="text-xs font-bold uppercase text-emerald-300">{copy.rightsActions}</h2>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-300">
                    {situation.immediate_actions.map((action) => <li key={action}>{action}</li>)}
                  </ul>
                </section>
              </div>
              <div className="space-y-4">
                <section>
                  <h2 className="text-xs font-bold uppercase text-emerald-300">{copy.rightsPreserve}</h2>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-300">
                    {situation.evidence_to_preserve.map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </section>
                <section>
                  <h2 className="text-xs font-bold uppercase text-emerald-300">{copy.rightsInformation}</h2>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-300">
                    {situation.required_information.map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </section>
              </div>
              <nav className="space-y-2 md:col-span-2" aria-label={`Official routes for ${situation.title}`}>
                <h2 className="text-xs font-bold uppercase text-emerald-300">{copy.rightsRoutes}</h2>
                <div className="flex flex-wrap gap-x-5 gap-y-2">
                  {situation.official_channels.map((channel) => (
                    <a key={channel.url} href={channel.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-sm text-emerald-300 underline decoration-emerald-700 underline-offset-4 hover:text-emerald-200">
                      {channel.name}<ExternalLink aria-hidden="true" className="h-3 w-3" />
                    </a>
                  ))}
                </div>
                {situation.official_channels.map((channel) => (
                  <p key={`${channel.url}-description`} className="text-xs text-slate-400">{channel.name}: {channel.description}</p>
                ))}
              </nav>
              <p className="text-xs leading-relaxed text-slate-500 md:col-span-2">{situation.important_note}</p>
            </div>
          </details>
        ))}
      </div>
      {!loading && !error && situations.length === 0 && <p className="text-sm text-slate-400">No guidance is available right now.</p>}
    </section>
  );
}
