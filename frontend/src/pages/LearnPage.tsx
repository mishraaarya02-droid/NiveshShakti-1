import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, ShieldAlert, AlertTriangle, CheckCircle, ExternalLink } from 'lucide-react';
import { uiCopy } from '../uiCopy';

interface LessonItem {
  id: string;
  title: string;
  title_hindi: string;
  summary: string;
  summary_hindi: string;
  body: string;
  body_hindi: string;
  source_url: string;
  risk_level: 'info' | 'caution' | 'danger';
}

const LESSONS: LessonItem[] = [
  {
    id: 'guaranteed_returns',
    title: 'Return Promises Need Independent Checking',
    title_hindi: 'रिटर्न के वादों की स्वतंत्र जाँच करें',
    summary: 'A promised return is a claim to check against the product documents and official material.',
    summary_hindi: 'रिटर्न का वादा एक दावा है; इसे उत्पाद के आधिकारिक दस्तावेज़ों से जाँचें।',
    body: `Words such as "guaranteed," "fixed," or "assured" describe a claim, not proof that an offer is genuine or fraudulent.

  Before relying on a return statement, identify the product, read its official offer or disclosure documents, and check whether the named entity and communication channel can be verified independently.

  Do not treat a high percentage, an official-looking logo, or a claim of regulator approval as evidence by itself. NiveshShakti cannot determine an offer's legal status from wording alone.`,
    body_hindi: `"गारंटीड" या "फिक्स्ड" रिटर्न का वाक्य एक दावा है, किसी प्रस्ताव की असलियत या धोखाधड़ी का प्रमाण नहीं।

  उत्पाद की पहचान करें, आधिकारिक दस्तावेज़ पढ़ें और संस्था व संपर्क माध्यम को स्वतंत्र रूप से जाँचें। केवल ऊँचा प्रतिशत या आधिकारिक दिखने वाला लोगो प्रमाण नहीं है।`,
    source_url: 'https://investor.sebi.gov.in/personalsecurities.html',
    risk_level: 'danger',
  },
  {
    id: 'sebi_registration',
    title: 'How to Verify a SEBI Registration Number',
    title_hindi: 'SEBI पंजीकरण संख्या कैसे सत्यापित करें',
    summary: 'Use official intermediary-status routes; a registration claim needs an exact, independently checked match.',
    summary_hindi: 'पंजीकरण के दावे को आधिकारिक मार्ग से नाम और पहचान संख्या मिलाकर जाँचें।',
    body: `SEBI registration numbers follow specific formats depending on the type of intermediary:
• **Research Analysts:** INH followed by 9 digits (e.g., INH000001234)
• **Investment Advisers:** INA followed by 9 digits
• **Stock Brokers:** INZ followed by 9 digits
• **Portfolio Managers:** INP followed by 9 digits

**How to verify:**
1. Open SEBI Investor Support from the official SEBI Investor website.
2. Follow its current "Check Registration Status of Market Intermediary" route.
3. Compare the exact name and identifier; check current status and any notices.
4. If the official search is unavailable or the details do not match, treat the claim as unverified and use the published manual support route.

**Warning signs:**
• Claiming "SEBI approved" without a specific registration number
• Using registration numbers in formats that don't match SEBI standards
• Refusing to share their registration number
• A mismatch between the claimed identity and information shown by an official route`,
    body_hindi: `SEBI पंजीकरण संख्या मध्यस्थ के प्रकार के अनुसार विशिष्ट प्रारूप होती है:
• शोध विश्लेषक: INH + 9 अंक
• निवेश सलाहकार: INA + 9 अंक
• स्टॉक ब्रोकर: INZ + 9 अंक

**कैसे सत्यापित करें:** https://www.sebi.gov.in पर जाएं और "Intermediaries" अनुभाग में संख्या खोजें।`,
    source_url: 'https://investor.sebi.gov.in/Investor-support.html',
    risk_level: 'info',
  },
  {
    id: 'telegram_whatsapp_tips',
    title: 'Private Messaging Groups Do Not Verify Investment Claims',
    title_hindi: 'निजी मैसेजिंग समूह निवेश दावों की पुष्टि नहीं करते',
    summary: 'A messaging-group invitation is a channel cue, not proof of identity, registration, or fraud.',
    summary_hindi: 'मैसेजिंग समूह का निमंत्रण पहचान, पंजीकरण या धोखाधड़ी का प्रमाण नहीं है।',
    body: `A private group, paid channel, or testimonial does not establish who is responsible for a financial claim.

  Check the exact person or entity and the relevant activity using official investor-support routes. Do not assume that a shared registration number belongs to the sender or covers the offer being made.

**Common formats of these scams:**
• "Free Jackpot Tips — Join our VIP channel"
• "NSE/BSE premium calls at ₹5000/month"
• "Insider tips from market analysts"
• "100% accuracy track record"

**Before paying or acting:** preserve the full message, independently check the claimed identity, and read the official terms for any service. SCORES is for eligible grievances concerning SEBI-regulated entities; consult its current process before filing.`,
    body_hindi: `निजी समूह, भुगतान वाला चैनल या प्रशंसापत्र यह साबित नहीं करते कि वित्तीय दावे के लिए कौन जिम्मेदार है।

  आधिकारिक निवेशक सहायता मार्ग से व्यक्ति या संस्था और संबंधित गतिविधि की जाँच करें। साझा किया गया पंजीकरण नंबर अपने आप प्रेषक या प्रस्ताव की पुष्टि नहीं करता।`,
    source_url: 'https://investor.sebi.gov.in/Investor-support.html',
    risk_level: 'danger',
  },
  {
    id: 'upi_payment_red_flag',
    title: 'Check Payment Instructions Independently',
    title_hindi: 'भुगतान निर्देशों की स्वतंत्र जाँच करें',
    summary: 'Payment instructions should be checked through a known official app or contact channel.',
    summary_hindi: 'भुगतान निर्देशों को आधिकारिक ऐप या सत्यापित संपर्क से जाँचें।',
    body: `A request to transfer money is a reason to pause and independently verify the payee and instructions. A UPI handle or bank account name alone does not establish who controls it.

  Do not use payment details sent in an unsolicited message without checking them through the financial institution's official site or app. If you already paid and suspect misuse, contact your bank or payment provider promptly using a verified channel and preserve transaction references.`,
    body_hindi: `पैसे भेजने का अनुरोध मिलने पर भुगतान पाने वाले और निर्देशों को स्वतंत्र रूप से जाँचें। UPI आईडी या बैंक खाते का नाम अकेले यह साबित नहीं करता कि उसे कौन नियंत्रित करता है।

  यदि आपने भुगतान किया है और दुरुपयोग का संदेह है, तो सत्यापित आधिकारिक माध्यम से बैंक या भुगतान सेवा से तुरंत संपर्क करें।`,
    source_url: 'https://investor.sebi.gov.in/Investor-support.html',
    risk_level: 'danger',
  },
  {
    id: 'otp_remote_access',
    title: 'Protect OTPs, Passwords, and Device Access',
    title_hindi: 'कभी OTP शेयर न करें या रिमोट एक्सेस की अनुमति न दें',
    summary: 'Keep authentication codes private and verify support requests through known official channels.',
    summary_hindi: 'सुरक्षा कोड निजी रखें और सहायता के अनुरोध आधिकारिक माध्यम से जाँचें।',
    body: `Never disclose an OTP, password, PIN, or recovery code to a caller or message sender. Be cautious of requests to install screen-sharing or remote-access tools.

**Remote access software (AnyDesk, TeamViewer, Quick Support):**
Remote-access software can expose information or allow device control. Only install it when you have independently verified the need and the support provider.

**If you have already shared access:** use a trusted device and the provider's official instructions to secure the affected account, contact the institution promptly, and preserve related alerts and messages. For online crime, use the Government of India's cybercrime reporting portal.`,
    body_hindi: `One-Time Password (OTP) एक सुरक्षा कोड है जिसे आपको कभी किसी के साथ साझा नहीं करना चाहिए — यहां तक कि बैंक अधिकारी, SEBI अधिकारी या ब्रोकर होने का दावा करने वाले के साथ भी नहीं।

यदि आपने OTP शेयर किया है: तुरंत अपने बैंक के धोखाधड़ी हेल्पलाइन पर कॉल करें और 1930 पर कॉल करें।`,
    risk_level: 'danger',
    source_url: 'https://investor.sebi.gov.in/secure_ur_inv_account.html',
  },
  {
    id: 'mutual_fund_basics',
    title: 'Read Fund Information Carefully',
    title_hindi: 'फंड की जानकारी ध्यान से पढ़ें',
    summary: 'Use the official scheme documents and current investor education material, not an isolated marketing claim.',
    summary_hindi: 'विपणन संदेश के बजाय योजना के आधिकारिक दस्तावेज़ और नवीनतम निवेशक सामग्री देखें।',
    body: `When reviewing a fund-related message, identify the scheme and fund house, then locate the current official documents and disclosures for that exact product.

  Compare the message with those documents and note the publication date. A screenshot or forwarded summary may omit context. If an intermediary is named, check that identity using an official investor-support route.

  This is general document-literacy guidance, not a product assessment or investment recommendation.`,
    body_hindi: `फंड से जुड़ा संदेश पढ़ते समय योजना और फंड हाउस की पहचान करें। उसी उत्पाद के नवीनतम आधिकारिक दस्तावेज़ और घोषणाएँ देखें।

  संदेश को उन दस्तावेज़ों से मिलाएँ और तारीख़ नोट करें। स्क्रीनशॉट या अग्रेषित सारांश में संदर्भ छूट सकता है। यह सामान्य जानकारी है, निवेश सलाह नहीं।`,
    source_url: 'https://investor.sebi.gov.in/moneymatters.html',
    risk_level: 'info',
  },
];

const riskColors = {
  info: 'border-emerald-800/40 bg-emerald-950/10',
  caution: 'border-amber-800/40 bg-amber-950/10',
  danger: 'border-red-800/40 bg-red-950/10',
};

const riskBadge = {
  info: 'bg-emerald-950 text-emerald-300',
  caution: 'bg-amber-950 text-amber-300',
  danger: 'bg-red-950 text-red-300',
};

const riskIcon = {
  info: <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />,
  caution: <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />,
  danger: <ShieldAlert className="w-4 h-4 text-red-400 shrink-0" />,
};

interface LearnPageProps {
  language: 'EN' | 'HI' | 'HINGLISH';
}

export const LearnPage: React.FC<LearnPageProps> = ({ language }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const copy = uiCopy(language);

  const toggle = (id: string) => setExpandedId(expandedId === id ? null : id);
  const showHindi = language === 'HI';
  const showHinglishFallback = language === 'HINGLISH';

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <div className="text-center space-y-2 mb-8">
        <div className="flex items-center justify-center gap-2 mb-3">
          <BookOpen className="w-6 h-6 text-emerald-400" />
          <h2 className="text-2xl font-extrabold text-white tracking-tight">{copy.learnTitle}</h2>
        </div>
        <p className="text-sm text-slate-400 max-w-xl mx-auto">
          {copy.learnIntro}
        </p>
      </div>

      <div className="space-y-3">
        {LESSONS.map((lesson) => (
          <div
            key={lesson.id}
            className={`rounded-xl border overflow-hidden transition-all ${riskColors[lesson.risk_level]}`}
          >
            <button
              onClick={() => toggle(lesson.id)}
              className="w-full p-4 text-left flex items-start justify-between gap-3 hover:bg-white/5 transition-colors"
            >
              <div className="flex items-start gap-3 min-w-0">
                {riskIcon[lesson.risk_level]}
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-white leading-tight">
                      {showHindi ? lesson.title_hindi : lesson.title}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${riskBadge[lesson.risk_level]}`}>
                      {lesson.risk_level === 'danger' ? 'PROTECT ACCOUNT' : lesson.risk_level === 'caution' ? 'PAUSE AND CHECK' : 'KNOW THIS'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">{showHindi ? lesson.summary_hindi : lesson.summary}</p>
                </div>
              </div>
              {expandedId === lesson.id
                ? <ChevronUp className="w-4 h-4 text-slate-400 shrink-0 mt-1" />
                : <ChevronDown className="w-4 h-4 text-slate-400 shrink-0 mt-1" />
              }
            </button>

            {expandedId === lesson.id && (
              <div className="px-5 pb-5 border-t border-white/5 space-y-4">
                <div className="pt-4 text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                  {showHindi ? lesson.body_hindi : lesson.body}
                </div>

                {showHinglishFallback && <p role="note" className="text-xs text-amber-700">{copy.learnFallback}</p>}

                <a href={lesson.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[11px] text-emerald-400 underline underline-offset-2">
                  {copy.learnSource} <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 leading-relaxed">
        {copy.learnDisclaimer}
      </div>
    </div>
  );
};

export default LearnPage;
