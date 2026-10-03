import React from 'react';
import type { AnalysisDetail } from '../api';
import type { UserProfile } from '../types';
import { uiCopy } from '../uiCopy';
import { AlertTriangle, CheckCircle, ShieldAlert, FileText, ExternalLink, HelpCircle } from 'lucide-react';

interface ResultCardProps {
  analysis: AnalysisDetail;
  language: UserProfile['language'];
  knowledgeLevel: UserProfile['knowledge_level'];
}

export const ResultCard: React.FC<ResultCardProps> = ({ analysis, language, knowledgeLevel }) => {
  const isFailure = analysis.status === 'FAILED';
  const copy = uiCopy(language);
  const isHighRisk = analysis.overall_risk_level === 'CRITICAL' || analysis.overall_risk_level === 'HIGH';
  const explanationByLanguageAndLevel = {
    EN: {
      BEGINNER: analysis.explanation_beginner,
      INTERMEDIATE: analysis.explanation_intermediate,
      ADVANCED: analysis.explanation_advanced,
    },
    HI: {
      BEGINNER: analysis.explanation_hindi,
      INTERMEDIATE: analysis.explanation_hindi_intermediate,
      ADVANCED: analysis.explanation_hindi_advanced,
    },
    HINGLISH: {
      BEGINNER: analysis.explanation_hinglish,
      INTERMEDIATE: analysis.explanation_hinglish_intermediate,
      ADVANCED: analysis.explanation_hinglish_advanced,
    },
  };
  const selectedExplanation = explanationByLanguageAndLevel[language][knowledgeLevel];
  const explanation = selectedExplanation || analysis.explanation_beginner;
  const localizedPause = language === 'EN'
    ? analysis.pause_recommendation
    : analysis.overall_risk_level === 'CRITICAL'
      ? copy.pauseCritical
      : analysis.overall_risk_level === 'HIGH'
        ? copy.pauseHigh
        : analysis.overall_risk_level === 'MEDIUM'
          ? copy.pauseMedium
          : copy.pauseLow;

  return (
    <div className="nivesh-result-card w-full overflow-hidden text-left">
      {/* Top Header Banner with Risk Status */}
      <div className={`nivesh-risk-banner p-6 border-b flex flex-wrap items-center justify-between gap-4 ${
        isFailure ? 'bg-amber-950/30 border-amber-900/40 text-amber-300' :
        analysis.overall_risk_level === 'CRITICAL' ? 'bg-red-950/30 border-red-900/40 text-red-400' :
        analysis.overall_risk_level === 'HIGH' ? 'bg-orange-950/30 border-orange-900/40 text-orange-400' :
        analysis.overall_risk_level === 'MEDIUM' ? 'bg-yellow-950/30 border-yellow-900/40 text-yellow-400' :
        'bg-emerald-950/30 border-emerald-900/40 text-emerald-400'
      }`} data-risk={isFailure ? 'UNAVAILABLE' : analysis.overall_risk_level ?? 'UNASSESSED'}>
        <div className="flex items-center gap-3">
          {isFailure ? (
            <AlertTriangle className="w-8 h-8 text-amber-400" />
          ) : isHighRisk ? (
            <ShieldAlert className="w-8 h-8 text-red-500 animate-pulse" />
          ) : (
            <CheckCircle className="w-8 h-8 text-emerald-400" />
          )}
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-widest px-2.5 py-0.5 rounded-full bg-slate-900/80 border border-current">
                {isFailure ? copy.resultUnavailable : `${analysis.overall_risk_level ?? 'UNASSESSED'} RISK`}
              </span>
              {!isFailure && analysis.overall_risk_score !== null && <span className="text-xs text-slate-400">Score: {analysis.overall_risk_score}/100</span>}
            </div>
            <h3 className="text-lg font-bold text-white mt-1">
              {isFailure ? copy.noAssessment : copy.assessment}
            </h3>
            {!isFailure && analysis.overall_risk_score !== null && (
              <div className="mt-4 max-w-sm" data-testid="risk-score-meter">
                <div className="mb-1 flex items-center justify-between gap-4 text-[11px]">
                  <span className="font-semibold text-slate-600">{copy.scoreLabel}</span>
                  <span className="font-bold text-slate-700">{analysis.overall_risk_score}/100</span>
                </div>
                <div
                  className="nivesh-risk-meter"
                  role="progressbar"
                  aria-label={`${copy.scoreLabel}: ${analysis.overall_risk_score} out of 100`}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={analysis.overall_risk_score}
                >
                  <div className="nivesh-risk-meter-fill" style={{ width: `${Math.min(100, Math.max(0, analysis.overall_risk_score))}%` }} />
                </div>
                <p className="mt-1 text-[10px] text-slate-500">{copy.scoreNote}</p>
              </div>
            )}
          </div>
        </div>

        <div className="text-right">
          {isFailure ? (
            <span className="text-xs font-semibold">{analysis.extraction_status === 'PROVIDER_UNAVAILABLE' ? copy.providerUnavailable : copy.processingError}</span>
          ) : (
            <>
              <span className="text-xs text-slate-400">{copy.checkedOn}</span>
              <p className="text-xs font-medium text-slate-200">
                {new Date(analysis.created_at).toLocaleString()}
              </p>
            </>
          )}
        </div>
      </div>

      <div className="p-6 space-y-6">
        {analysis.input_type === 'url' && (
          <p role="note" className="rounded-lg border border-amber-700/50 bg-amber-950/20 p-3 text-xs leading-relaxed text-amber-100">
            {copy.urlAnalysisLimit}
          </p>
        )}
        {isFailure ? (
          <div role="alert" className="space-y-3 rounded-lg border border-amber-700/50 bg-amber-950/20 p-4 text-sm text-amber-100">
            <h4 className="font-semibold">{analysis.extraction_status === 'PROVIDER_UNAVAILABLE' ? copy.providerUnavailable : copy.processingError}</h4>
            <p className="text-xs leading-relaxed">{analysis.explanation_beginner || copy.sourceUnavailableDetail}</p>
            <p className="text-xs leading-relaxed">No risk assessment was generated. This result does not indicate that the content is safe.</p>
            <p className="text-xs leading-relaxed"><strong>{copy.pauseTitle}:</strong> Do not send money or share OTPs. Verify claims directly through the relevant official portal.</p>
          </div>
        ) : (
          <>
        {/* Behavioral Pause Recommendation (Track D + Track A) */}
        {analysis.pause_recommendation && (
          <div className="nivesh-review-note flex items-start gap-3 rounded-2xl p-5">
            <AlertTriangle aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-slate-800">{copy.reviewResultTitle}</h4>
              <p className="text-xs leading-relaxed text-slate-700">{copy.reviewResultBody}</p>
              <p className="text-xs leading-relaxed text-slate-700">{copy.reviewResultGuidance}</p>
              <div className="border-t border-amber-900/10 pt-2">
                <h5 className="text-xs font-bold text-amber-900">{copy.pauseTitle}</h5>
                <p className="mt-1 text-xs leading-relaxed text-slate-700">{localizedPause}</p>
                <p className="mt-1 text-xs leading-relaxed text-slate-700">Verify the named entity through an official portal. If you already paid, contact your bank using its official channel.</p>
              </div>
            </div>
          </div>
        )}

        {/* Multi-Tier Educational Explanation (Track C + Track E) */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <FileText className="w-4 h-4 text-emerald-400" />
            {copy.understand}
          </h4>

          <div
            data-testid="analysis-explanation"
            lang={language === 'HI' ? 'hi' : 'en'}
            className="rounded-lg border border-slate-800 bg-slate-900/60 p-4 text-sm leading-relaxed text-slate-300"
          >
            <span className="mb-2 block text-[10px] font-bold uppercase tracking-wider text-emerald-400">
              {language === 'HI' ? 'हिन्दी' : language === 'HINGLISH' ? 'Hinglish' : copy[knowledgeLevel.toLowerCase() as 'beginner' | 'intermediate' | 'advanced']}
            </span>
            {explanation}
            {!selectedExplanation && <p className="mt-2 text-xs text-amber-300">{copy.fallbackEnglish}</p>}
          </div>
        </div>

        {analysis.content_classification && (
          <section aria-label="Content literacy cues" className="border-y border-slate-800 py-4">
            <h4 className="text-sm font-semibold text-slate-200">{copy.contentCues}: {analysis.content_classification.replaceAll('_', ' ').toLowerCase()}</h4>
            <p className="mt-1 text-xs text-slate-400">These wording patterns describe the material only; they do not establish whether it is fraudulent, accurate, or safe.</p>
            {analysis.content_signals && analysis.content_signals.length > 0 && (
              <ul className="mt-2 space-y-1 text-xs text-slate-300">
                {analysis.content_signals.map((signal) => (
                  <li key={signal.code}>{signal.description}: <span className="font-mono text-slate-400">“{signal.matched_text}”</span></li>
                ))}
              </ul>
            )}
          </section>
        )}

        {/* Detected Risk Indicators */}
        {analysis.risk_indicators.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-orange-400" />
              {copy.riskIndicators} ({analysis.risk_indicators.length})
            </h4>
            <p className="mb-3 text-xs text-slate-400">These are rule-matched warning signs, not proof of fraud or a probability estimate.</p>
            {language !== 'EN' && <p className="mb-3 text-xs text-slate-500">{copy.translationNotice}</p>}
            <div className="space-y-2">
              {analysis.risk_indicators.map((ind) => (
                <div key={ind.id} className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 flex flex-col gap-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-white">{ind.title}</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-red-950 text-red-300 border border-red-800/40">
                      {ind.severity}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">{ind.description}</p>
                  {ind.evidence_snippet && (
                    <div className="text-[11px] font-mono text-slate-300 bg-black/40 px-2 py-1 rounded mt-1 border border-slate-800">
                      Matched: "{ind.evidence_snippet}"
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Extracted Checkable Claims & Authoritative Source Verification */}
        {analysis.claims.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-blue-400" />
              {copy.claimsEvidence}
            </h4>
            <div className="space-y-3">
              {analysis.claims.map((claim) => (
                <div key={claim.id} className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-xs font-medium text-slate-200">"{claim.claim_text}"</p>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 whitespace-nowrap">
                      {claim.verification_status}
                    </span>
                  </div>
                  {claim.explanation && (
                    <p className="text-[11px] text-slate-400 italic">{claim.explanation}</p>
                  )}

                  {/* Verification Results per Source */}
                  {claim.verification_results.map((vr) => (
                    <div key={vr.id} className="pt-2 border-t border-slate-800/80 flex items-start justify-between gap-2 text-[11px] text-slate-300">
                      <div>
                        <span className="font-semibold text-emerald-400">{vr.source_name}{vr.source_type ? ` (${vr.source_type})` : ''}: </span>
                        <span className="text-slate-400">{vr.evidence_text}</span>
                        <p className="mt-1 text-[10px] text-slate-500">
                          {vr.retrieval_status || vr.status} · Retrieved {new Date(vr.retrieved_at).toLocaleString()}
                          {vr.source_published_at ? ` · Published ${new Date(vr.source_published_at).toLocaleDateString()}` : ''}
                          {vr.source_version ? ` · Version ${vr.source_version}` : ''}
                        </p>
                      </div>
                      {vr.source_url && (
                        <a
                          href={vr.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-emerald-400 hover:underline flex items-center gap-1 shrink-0"
                        >
                          Official Portal <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Extracted Entities */}
        {analysis.entities.length > 0 && (
          <div className="pt-2">
            <h4 className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
              {copy.entities}
            </h4>
            <div className="flex flex-wrap gap-2">
              {analysis.entities.map((ent) => (
                <span key={ent.id} className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-[11px] text-slate-300 font-mono">
                  <span className="text-emerald-500 font-semibold">{ent.entity_type}:</span> {ent.entity_text}
                </span>
              ))}
            </div>
          </div>
        )}
          </>
        )}
      </div>
    </div>
  );
};
