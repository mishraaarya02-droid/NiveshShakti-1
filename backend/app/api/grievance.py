"""Curated, non-transactional investor guidance with official manual routes."""
from fastapi import APIRouter

from ..schemas import GrievanceChannel, GrievanceSituation

router = APIRouter()

SCORES = GrievanceChannel(
    name="SEBI SCORES",
    url="https://scores.sebi.gov.in/",
    description="For grievances concerning SEBI-regulated entities; check current eligibility and first-contact requirements on the portal.",
)
SEBI_SUPPORT = GrievanceChannel(
    name="SEBI Investor Support",
    url="https://investor.sebi.gov.in/Investor-support.html",
    description="Official investor support, intermediary-status links, and investor-service routes.",
)
CYBERCRIME = GrievanceChannel(
    name="National Cyber Crime Reporting Portal",
    url="https://www.cybercrime.gov.in/",
    description="Government portal for reporting cybercrime. For an active payment fraud, contact your bank immediately using its official app/card channel as well.",
)
NPCI_UPI = GrievanceChannel(
    name="NPCI UPI Help",
    url="https://www.upihelp.npci.org.in/",
    description="Official UPI complaint and support information; also notify the bank or UPI app used for the transaction.",
)

GENERAL_NOTE = (
    "NiveshShakti is an independent guidance tool, not a regulator or complaint authority. "
    "It does not submit complaints or contact institutions for you."
)

SITUATIONS = [
    GrievanceSituation(
        id="suspicious_solicitation",
        title="Suspicious investment solicitation",
        title_hindi="संदिग्ध निवेश प्रस्ताव",
        description="Someone is asking you to invest, join a tip group, or pay a fee for promised results.",
        description_hindi="कोई व्यक्ति निवेश, टिप समूह में शामिल होने या मुनाफ़े के वादे पर शुल्क माँग रहा है।",
        immediate_actions=["Pause before paying or clicking links.", "Verify any claimed registration using an official SEBI route.", "Do not share OTPs, passwords, or remote-access permissions."],
        evidence_to_preserve=["Original messages and attachments", "Phone numbers, account handles, URLs, and timestamps", "Payment requests or receipts, if any"],
        required_information=["Name and contact details claimed by the sender", "Claimed registration identifier", "Communication dates and channel"],
        official_channels=[SEBI_SUPPORT, CYBERCRIME],
        important_note=GENERAL_NOTE,
    ),
    GrievanceSituation(
        id="money_paid",
        title="Money already paid",
        title_hindi="पैसे भेज दिए हैं",
        description="You transferred money in response to a suspected investment offer or impersonation.",
        description_hindi="संदिग्ध निवेश प्रस्ताव या पहचान का झूठा दावा देखकर आपने पैसे भेजे हैं।",
        immediate_actions=["Contact your bank and payment provider immediately using independently verified contact details.", "For online financial fraud, use the government cybercrime reporting route promptly.", "Do not pay anyone promising guaranteed recovery of the funds."],
        evidence_to_preserve=["Bank statement and transaction confirmation", "UTR/reference number, date, time, amount, and beneficiary details", "Messages, call logs, URLs, and complaint reference numbers"],
        required_information=["Your bank/payment provider details", "Transaction reference and beneficiary details", "Chronology of contact and transfer"],
        official_channels=[CYBERCRIME, NPCI_UPI, SCORES],
        important_note=GENERAL_NOTE,
    ),
    GrievanceSituation(
        id="credentials_shared",
        title="OTP, password, or personal information shared",
        title_hindi="OTP, पासवर्ड या निजी जानकारी साझा हुई",
        description="You shared account credentials, an OTP, identity documents, or granted screen-sharing access.",
        description_hindi="आपने खाते की जानकारी, OTP, पहचान दस्तावेज़ साझा किए या स्क्रीन साझा करने की अनुमति दी।",
        immediate_actions=["Contact the affected bank, broker, or depository using its official app or a verified number.", "Ask the institution how to secure the affected account and revoke active sessions or access.", "Change exposed credentials from a trusted device; never disclose a new OTP to a caller."],
        evidence_to_preserve=["Messages and call details", "Time and type of information disclosed", "Bank alerts and any unauthorized transaction records"],
        required_information=["Affected account or service", "Time of disclosure", "Actions already taken and institution reference numbers"],
        official_channels=[CYBERCRIME, SEBI_SUPPORT],
        important_note=GENERAL_NOTE,
    ),
    GrievanceSituation(
        id="impersonation",
        title="Someone impersonated a regulator or intermediary",
        title_hindi="किसी ने नियामक या मध्यस्थ बनकर संपर्क किया",
        description="A caller or message claims to represent SEBI, an exchange, a bank, or a registered intermediary and pressures you to act.",
        description_hindi="कॉलर या संदेश SEBI, एक्सचेंज, बैंक या पंजीकृत मध्यस्थ होने का दावा करके कार्रवाई का दबाव डालता है।",
        immediate_actions=["End contact and do not use phone numbers or links supplied in that message.", "Find the institution through its official website and verify the contact independently.", "Do not transfer money, share OTPs, or install remote-access software."],
        evidence_to_preserve=["Caller ID, call time, recordings where lawfully held, and messages", "Email headers, sender addresses, links, and documents", "Payment details if money was requested or sent"],
        required_information=["Name and role claimed", "Contact details and exact request", "Any transaction or account affected"],
        official_channels=[SEBI_SUPPORT, CYBERCRIME],
        important_note=GENERAL_NOTE,
    ),
    GrievanceSituation(
        id="misleading_information",
        title="Misleading financial information",
        title_hindi="भ्रामक वित्तीय जानकारी",
        description="A communication contains a claim you believe is inaccurate, incomplete, or presented without context.",
        description_hindi="किसी संदेश में ऐसा दावा है जो आपको गलत, अधूरा या संदर्भ से बाहर लगता है।",
        immediate_actions=["Keep the complete original material, not only a cropped excerpt.", "Check whether the claim names a source, date, and relevant product or entity.", "Do not treat an unverified claim as false or as proof of fraud."],
        evidence_to_preserve=["Full publication or message and its URL", "Publication date, author/account, and edits if visible", "The exact statement and any cited source material"],
        required_information=["Exact wording and context", "Publisher and date", "Why the claim appears misleading and supporting documents"],
        official_channels=[SEBI_SUPPORT, SCORES],
        important_note=GENERAL_NOTE,
    ),
    GrievanceSituation(
        id="intermediary_issue",
        title="Issue with a broker or other intermediary",
        title_hindi="ब्रोकर या अन्य मध्यस्थ से जुड़ी समस्या",
        description="You have a service, transaction, or grievance issue involving a market intermediary.",
        description_hindi="बाज़ार मध्यस्थ से सेवा, लेन-देन या शिकायत से जुड़ी समस्या है।",
        immediate_actions=["Raise the issue with the entity through its official grievance channel and retain its acknowledgement.", "Use exchange or depository investor-service contacts where relevant.", "Review current SCORES eligibility and process before lodging a grievance there."],
        evidence_to_preserve=["Account statements, contract notes, and transaction references", "Written complaint and acknowledgement", "Relevant correspondence and dates"],
        required_information=["Intermediary name and official identifier", "Account/client reference, shared only on official forms", "Complaint history and supporting records"],
        official_channels=[SCORES, SEBI_SUPPORT],
        important_note=GENERAL_NOTE,
    ),
    GrievanceSituation(
        id="investor_rights",
        title="Investor-rights question",
        title_hindi="निवेशक अधिकारों से जुड़ा प्रश्न",
        description="You need official information about investor support, services, or complaint routes.",
        description_hindi="आपको निवेशक सहायता, सेवाओं या शिकायत के आधिकारिक तरीकों की जानकारी चाहिए।",
        immediate_actions=["Start with SEBI's investor website and read the current guidance for your situation.", "Use contact details published on the official institution website.", "Keep a copy of submissions and acknowledgement numbers."],
        evidence_to_preserve=["Relevant account or service records", "Prior communications and acknowledgements", "Dates and reference numbers"],
        required_information=["A concise description of the issue", "Entity or service involved", "Relevant dates and prior steps"],
        official_channels=[SEBI_SUPPORT, SCORES],
        important_note=GENERAL_NOTE,
    ),
    GrievanceSituation(
        id="suspicious_activity",
        title="Suspicious financial activity",
        title_hindi="संदिग्ध वित्तीय गतिविधि",
        description="You noticed an unfamiliar transaction, account change, or activity linked to a financial service.",
        description_hindi="आपको वित्तीय सेवा से जुड़ा अनजान लेन-देन, खाता परिवर्तन या गतिविधि दिखी है।",
        immediate_actions=["Contact the relevant bank or service provider through its official channel immediately.", "Secure the affected account using the provider's official instructions.", "Report suspected online crime through the government portal."],
        evidence_to_preserve=["Transaction alerts and account statements", "Date, time, amount, and reference numbers", "Messages and service-provider complaint references"],
        required_information=["Affected service and account", "Activity details and when discovered", "Actions taken and reference numbers"],
        official_channels=[CYBERCRIME, NPCI_UPI, SEBI_SUPPORT],
        important_note=GENERAL_NOTE,
    ),
]


@router.get("/situations", response_model=list[GrievanceSituation])
def get_grievance_situations():
    return SITUATIONS
