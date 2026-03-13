import { createContext, useContext, useState, ReactNode } from "react";

export type Language = "en" | "de";

interface LanguageContextType {
  lang: Language;
  setLang: (l: Language) => void;
  t: (key: string) => string;
}

const translations: Record<Language, Record<string, string>> = {
  en: {
    // Navbar
    "nav.home": "Home",
    "nav.advisor": "AI Advisor",
    "nav.permits": "Permit Process",

    // Landing — hero
    "landing.badge": "German Property Law Intelligence",
    "landing.hero.line1": "Your Property.",
    "landing.hero.line2": "Your Rights.",
    "landing.hero.line3": "Clarified.",
    "landing.hero.sub": "Navigate Germany's complex Immobilienrecht with AI-powered guidance backed by exact legal sources — BGB, BauGB, WEG, and more.",
    "landing.hero.cta1": "Ask a Legal Question",
    "landing.hero.cta2": "Permit Process",
    "landing.hero.samples": "Sample Questions",

    // Landing — stats
    "landing.stat1": "Legal Articles Indexed",
    "landing.stat2": "Citation Accuracy",
    "landing.stat3": "German States Covered",
    "landing.stat4": "AI Availability",

    // Landing — features
    "landing.features.badge": "What We Offer",
    "landing.features.title": "Legal Clarity at Your Fingertips",
    "landing.features.sub": "Purpose-built for property owners, buyers, tenants, and developers navigating German real estate law.",

    "landing.feat1.title": "AI-Powered Legal Advice",
    "landing.feat1.desc": "Ask any property law question in plain language. Our AI understands complex German real estate regulations.",
    "landing.feat2.title": "Exact Legal Citations",
    "landing.feat2.desc": "Every answer is backed by specific §§ from BGB, BauGB, WEG, and other German legal codes.",
    "landing.feat3.title": "Reliability Scoring",
    "landing.feat3.desc": "Each response includes a confidence score so you know exactly how certain the legal guidance is.",
    "landing.feat4.title": "Permit Process Wizard",
    "landing.feat4.desc": "Members get a personalized step-by-step permit roadmap tailored to their specific property project.",
    "landing.feat5.title": "Rechtssichere Schreiben",
    "landing.feat5.desc": "Generate legally-secure documents — Widersprüche, Stellungnahmen, and formal letters pre-filled with relevant §§.",

    // Landing — dashboard section
    "landing.dash.badge": "Case Dashboard",
    "landing.dash.title": "All Cases at a Glance",
    "landing.dash.sub": "Keep track of every legal case — with status indicators, progress bars, and automatic deadline alerts in real time.",
    "landing.dash.bullet1": "Status badges: In Progress, Completed, Pending",
    "landing.dash.bullet2": "Progress bar with step-by-step tracking",
    "landing.dash.bullet3": "Automatic deadline alert for active cases",
    "landing.dash.cta": "Manage Cases",
    "landing.dash.browserLabel": "rechtimmobilien.de — My Cases",
    "landing.dash.dashboardTitle": "Case Dashboard",

    // Landing — legal areas
    "landing.areas.badge": "Legal Coverage",
    "landing.areas.title": "All Areas of German Property Law",
    "landing.areas.sub": "Our AI is trained on the full spectrum of German Immobilienrecht, from purchase contracts to landlord-tenant disputes and construction permits.",
    "landing.areas.cta": "Start Asking",
    "landing.area1": "Property Purchase & Sales",
    "landing.area2": "Construction Law",
    "landing.area3": "Condominium Law",
    "landing.area4": "Tenancy Law",
    "landing.area5": "Land Register",
    "landing.area6": "Real Estate Transfer Tax",
    "landing.area7": "Ground Lease Law",
    "landing.area8": "Zoning Regulations",

    // Landing — CTA
    "landing.cta.title": "Ready to Understand Your Property Rights?",
    "landing.cta.sub": "Join thousands of property owners who use RechtImmobilien to navigate German property law with confidence.",
    "landing.cta.btn1": "Try the AI Advisor Free",
    "landing.cta.btn2": "View Permit Process",

    // Landing — footer
    "landing.footer.disclaimer": "For informational purposes only. Not a substitute for qualified legal counsel.",
    "landing.footer.copy": "© 2024 RechtImmobilien",

    // Case statuses
    "status.in_progress": "In Progress",
    "status.completed": "Completed",
    "status.pending": "Pending",
    "case.steps": "Steps",
    "case.deadline": "Deadline",

    // Advisor page
    "advisor.title": "AI Legal Advisor",
    "advisor.sub": "German Property Law · Backed by Legal Sources",
    "advisor.online": "AI Online",
    "advisor.tab.advisor": "AI Advisor",
    "advisor.tab.cases": "My Cases",
    "advisor.sources": "Legal Sources",
    "advisor.helpful": "Was this helpful?",
    "advisor.loading": "Analyzing German law databases…",
    "advisor.placeholder": "Ask your property law question… e.g. 'Can I rent out my apartment in Berlin short-term?'",
    "advisor.send": "Ask",
    "advisor.hint": "Press Enter to send · Shift+Enter for new line",
    "advisor.disclaimer": "AI responses are for informational purposes only and do not constitute legal advice.",
    "advisor.newCase": "Start New Case",
    "advisor.caseDash": "Case Dashboard",
    "advisor.cases": "Cases",
    "advisor.preset5": "Create a legally-secure letter",
    "advisor.preset5sub": "— Objection, Statement & more",
    "advisor.greeting": "Guten Tag! I'm your German Property Law AI Advisor. Ask me any question about Immobilienrecht — buying, selling, tenancy, construction permits, or property taxes. I'll provide you with precise answers backed by exact legal citations from German law.",
    "advisor.q1": "Can I add a balcony to my apartment in Berlin without permission?",
    "advisor.q2": "What are my rights if my landlord claims Eigenbedarf?",
    "advisor.q3": "How does Grunderwerbsteuer affect my property purchase?",
    "advisor.q4": "What permits do I need to renovate a Denkmalgeschütztes building?",
    "advisor.docPreset": "Ich benötige ein rechtssicheres Widerspruchsschreiben gegen die Baugenehmigung meines Nachbarn.",
    "advisor.words": "words",
    "advisor.copy": "Copy document",
    "advisor.copied": "Copied!",

    // Advisor — guided context inputs
    "advisor.context.title": "Tell us about your property",
    "advisor.context.sub": "This helps us give you precise, location-specific legal guidance.",
    "advisor.context.bundesland.label": "Federal State (Bundesland)",
    "advisor.context.bundesland.placeholder": "Search or select a Bundesland…",
    "advisor.context.bundesland.empty": "No state found.",
    "advisor.context.proptype.label": "Property Type",
    "advisor.context.proptype.placeholder": "Select property type…",
    "advisor.context.floors.label": "Number of Floors (Anzahl Stockwerke)",
    "advisor.context.floors.placeholder": "e.g. 2",
    "advisor.context.ready": "Context set — you can now ask your question below.",
    "advisor.context.proptype.einfamilienhaus": "Einfamilienhaus (Single Family Home)",
    "advisor.context.proptype.mehrfamilienhaus": "Mehrfamilienhaus (Apartment Building)",
    "advisor.context.proptype.gewerbe": "Gewerbe (Commercial)",
    "advisor.context.proptype.gemischte": "Gemischte Nutzung (Mixed Use)",
    "advisor.context.proptype.sonderbau": "Sonderbau (Special Structure)",
    "advisor.context.insideoutside.label": "Location",
    "advisor.context.insideoutside.inside": "Inside",
    "advisor.context.insideoutside.outside": "Outside",
    "advisor.context.postcode.label": "Postcode (optional)",
    "advisor.context.postcode.placeholder": "e.g. 10115",
    "advisor.classify.pick": "Please select a topic:",

    // Permit page
    "permit.badge": "Member Feature",
    "permit.title1": "Your Permit Process,",
    "permit.title2": "Step by Step",
    "permit.sub": "Get a personalized, interactive roadmap for every permit you need to bring your German property project to life — from Bebauungsplan to Bauabnahme.",
    "permit.feat1.title": "7-Phase Roadmap",
    "permit.feat1.desc": "Complete step-by-step process from initial assessment to final inspection",
    "permit.feat2.title": "Document Checklist",
    "permit.feat2.desc": "Every form, drawing, and proof you need for each phase",
    "permit.feat3.title": "Authority Contacts",
    "permit.feat3.desc": "Direct links to the right authority for each step in your Bundesland",
    "permit.locked": "4 more steps locked…",
    "permit.unlock": "Unlock the full permit process with a membership",
    "permit.demo": "Preview Demo",
    "permit.plan1.name": "Basic",
    "permit.plan1.price": "€0",
    "permit.plan1.desc": "For occasional queries",
    "permit.plan1.f1": "AI Legal Advisor (5 questions/day)",
    "permit.plan1.f2": "Legal citations included",
    "permit.plan1.f3": "Reliability scores",
    "permit.plan1.cta": "Get Started Free",
    "permit.plan2.name": "Professional",
    "permit.plan2.price": "€29/mo",
    "permit.plan2.desc": "For serious property owners",
    "permit.plan2.f1": "Unlimited AI Advisor access",
    "permit.plan2.f2": "Full permit process wizard",
    "permit.plan2.f3": "Personalized roadmaps",
    "permit.plan2.f4": "Document checklists",
    "permit.plan2.f5": "Priority support",
    "permit.plan2.cta": "Become a Member",
    "permit.popular": "Most Popular",
    "permit.wizard.title": "Permit Process Wizard",
    "permit.wizard.sub": "Germany · All Bundesländer",
    "permit.wizard.steps": "steps",
    "permit.proj.extension": "Home Extension",
    "permit.proj.renovation": "Major Renovation",
    "permit.proj.newbuild": "New Build",
    "permit.proj.conversion": "Use Conversion",
    "permit.step.tasks": "Tasks & Checklist",
    "permit.step.legal": "Legal Basis",
    "permit.step.tip": "Pro Tip",
    "permit.step.complete": "Mark as complete",
    "permit.step.incomplete": "✓ Mark as incomplete",
    "permit.cta.question": "Have questions about any of these steps?",
    "permit.cta.btn": "Ask the AI Advisor",
    "permit.header.title": "Permit Process — Home Extension",
  },
  de: {
    // Navbar
    "nav.home": "Startseite",
    "nav.advisor": "KI-Berater",
    "nav.permits": "Genehmigungsverfahren",

    // Landing — hero
    "landing.badge": "KI-gestützte Immobilienrechtsberatung",
    "landing.hero.line1": "Ihr Eigentum.",
    "landing.hero.line2": "Ihre Rechte.",
    "landing.hero.line3": "Geklärt.",
    "landing.hero.sub": "Navigieren Sie durch das komplexe deutsche Immobilienrecht mit KI-gestützter Beratung auf Basis exakter Rechtsquellen — BGB, BauGB, WEG und mehr.",
    "landing.hero.cta1": "Rechtsfrage stellen",
    "landing.hero.cta2": "Genehmigungsverfahren",
    "landing.hero.samples": "Beispielfragen",

    // Landing — stats
    "landing.stat1": "Rechtliche Artikel indexiert",
    "landing.stat2": "Zitiergenauigkeit",
    "landing.stat3": "Bundesländer abgedeckt",
    "landing.stat4": "KI-Verfügbarkeit",

    // Landing — features
    "landing.features.badge": "Unser Angebot",
    "landing.features.title": "Rechtssicherheit auf Knopfdruck",
    "landing.features.sub": "Entwickelt für Eigentümer, Käufer, Mieter und Bauherren im deutschen Immobilienrecht.",

    "landing.feat1.title": "KI-gestützte Rechtsberatung",
    "landing.feat1.desc": "Stellen Sie jede Frage zum Immobilienrecht in einfacher Sprache. Unsere KI versteht komplexe deutsche Vorschriften.",
    "landing.feat2.title": "Exakte Rechtszitate",
    "landing.feat2.desc": "Jede Antwort wird durch spezifische §§ aus BGB, BauGB, WEG und anderen Gesetzen belegt.",
    "landing.feat3.title": "Zuverlässigkeitsbewertung",
    "landing.feat3.desc": "Jede Antwort enthält einen Konfidenzwert, damit Sie die Sicherheit der Rechtsauskunft einschätzen können.",
    "landing.feat4.title": "Genehmigungsassistent",
    "landing.feat4.desc": "Mitglieder erhalten einen personalisierten Schritt-für-Schritt-Fahrplan für ihr Bauprojekt.",
    "landing.feat5.title": "Rechtssichere Schreiben",
    "landing.feat5.desc": "Erstellen Sie rechtssichere Dokumente — Widersprüche, Stellungnahmen und formelle Schreiben mit relevanten §§.",

    // Landing — dashboard section
    "landing.dash.badge": "Vorgangs-Dashboard",
    "landing.dash.title": "Alle Vorgänge im Blick",
    "landing.dash.sub": "Behalte jeden Rechtsvorgang im Überblick — mit Statusanzeigen, Fortschrittsbalken und automatischen Fristenwarnungen in Echtzeit.",
    "landing.dash.bullet1": "Status-Badges: In Bearbeitung, Abgeschlossen, Wartend",
    "landing.dash.bullet2": "Fortschrittsbalken mit Schritt-für-Schritt-Tracking",
    "landing.dash.bullet3": "Automatische Fristenwarnung bei laufenden Vorgängen",
    "landing.dash.cta": "Vorgänge verwalten",
    "landing.dash.browserLabel": "rechtimmobilien.de — Meine Vorgänge",
    "landing.dash.dashboardTitle": "Vorgangs-Dashboard",

    // Landing — legal areas
    "landing.areas.badge": "Rechtsbereiche",
    "landing.areas.title": "Alle Bereiche des deutschen Immobilienrechts",
    "landing.areas.sub": "Unsere KI ist auf das gesamte Spektrum des deutschen Immobilienrechts trainiert — von Kaufverträgen bis zu Miet- und Baustreitigkeiten.",
    "landing.areas.cta": "Frage stellen",
    "landing.area1": "Kauf & Verkauf von Immobilien",
    "landing.area2": "Baurecht",
    "landing.area3": "Wohnungseigentumsrecht",
    "landing.area4": "Mietrecht",
    "landing.area5": "Grundbuchordnung",
    "landing.area6": "Grunderwerbsteuer",
    "landing.area7": "Erbbaurecht",
    "landing.area8": "Baunutzungsverordnung",

    // Landing — CTA
    "landing.cta.title": "Bereit, Ihre Eigentumsrechte zu verstehen?",
    "landing.cta.sub": "Schließen Sie sich Tausenden von Eigentümern an, die RechtImmobilien nutzen, um sicher durch das deutsche Immobilienrecht zu navigieren.",
    "landing.cta.btn1": "KI-Berater kostenlos testen",
    "landing.cta.btn2": "Genehmigungsverfahren ansehen",

    // Landing — footer
    "landing.footer.disclaimer": "Nur zu Informationszwecken. Kein Ersatz für qualifizierte Rechtsberatung.",
    "landing.footer.copy": "© 2024 RechtImmobilien",

    // Case statuses
    "status.in_progress": "In Bearbeitung",
    "status.completed": "Abgeschlossen",
    "status.pending": "Wartend",
    "case.steps": "Schritte",
    "case.deadline": "Frist",

    // Advisor page
    "advisor.title": "KI-Rechtsberater",
    "advisor.sub": "Deutsches Immobilienrecht · Belegte Rechtsquellen",
    "advisor.online": "KI Online",
    "advisor.tab.advisor": "KI-Berater",
    "advisor.tab.cases": "Meine Vorgänge",
    "advisor.sources": "Rechtsquellen",
    "advisor.helpful": "War das hilfreich?",
    "advisor.loading": "Analyse der deutschen Rechtsdatenbanken…",
    "advisor.placeholder": "Stellen Sie Ihre Rechtsfrage... z.B. 'Darf ich meine Berliner Wohnung kurzfristig vermieten?'",
    "advisor.send": "Fragen",
    "advisor.hint": "Enter zum Senden · Shift+Enter für neue Zeile",
    "advisor.disclaimer": "KI-Antworten dienen nur zur Information und stellen keine Rechtsberatung dar.",
    "advisor.newCase": "Neuen Vorgang starten",
    "advisor.caseDash": "Vorgangs-Dashboard",
    "advisor.cases": "Vorgänge",
    "advisor.preset5": "Rechtssicheres Schreiben erstellen",
    "advisor.preset5sub": "— Widerspruch, Stellungnahme & mehr",
    "advisor.greeting": "Guten Tag! Ich bin Ihr KI-Rechtsberater für deutsches Immobilienrecht. Stellen Sie mir jede Frage zu Kauf, Verkauf, Miete, Baugenehmigungen oder Grundsteuern — ich liefere präzise Antworten mit exakten Gesetzeszitaten.",
    "advisor.q1": "Darf ich meiner Berliner Wohnung einen Balkon hinzufügen ohne Genehmigung?",
    "advisor.q2": "Was sind meine Rechte bei einer Eigenbedarfskündigung des Vermieters?",
    "advisor.q3": "Wie wirkt sich die Grunderwerbsteuer auf meinen Immobilienkauf aus?",
    "advisor.q4": "Welche Genehmigungen benötige ich für die Renovierung eines Denkmalgeschützten Gebäudes?",
    "advisor.docPreset": "Ich benötige ein rechtssicheres Widerspruchsschreiben gegen die Baugenehmigung meines Nachbarn.",
    "advisor.words": "Wörter",
    "advisor.copy": "Dokument kopieren",
    "advisor.copied": "Kopiert!",

    // Advisor — guided context inputs
    "advisor.context.title": "Erzählen Sie uns von Ihrer Immobilie",
    "advisor.context.sub": "So können wir Ihnen präzise, ortsbezogene Rechtsauskünfte erteilen.",
    "advisor.context.bundesland.label": "Bundesland",
    "advisor.context.bundesland.placeholder": "Bundesland suchen oder auswählen…",
    "advisor.context.bundesland.empty": "Kein Bundesland gefunden.",
    "advisor.context.proptype.label": "Gebäudetyp",
    "advisor.context.proptype.placeholder": "Gebäudetyp auswählen…",
    "advisor.context.floors.label": "Anzahl Stockwerke",
    "advisor.context.floors.placeholder": "z.B. 2",
    "advisor.context.ready": "Kontext gesetzt — Sie können jetzt Ihre Frage stellen.",
    "advisor.context.proptype.einfamilienhaus": "Einfamilienhaus",
    "advisor.context.proptype.mehrfamilienhaus": "Mehrfamilienhaus",
    "advisor.context.proptype.gewerbe": "Gewerbe",
    "advisor.context.proptype.gemischte": "Gemischte Nutzung",
    "advisor.context.proptype.sonderbau": "Sonderbau",
    "advisor.context.insideoutside.label": "Lage",
    "advisor.context.insideoutside.inside": "Innen",
    "advisor.context.insideoutside.outside": "Außen",
    "advisor.context.postcode.label": "Postleitzahl (optional)",
    "advisor.context.postcode.placeholder": "z.B. 10115",
    "advisor.classify.pick": "Bitte wählen Sie ein Thema:",

    // Permit page
    "permit.badge": "Mitglieder-Funktion",
    "permit.title1": "Ihr Genehmigungsverfahren,",
    "permit.title2": "Schritt für Schritt",
    "permit.sub": "Erhalten Sie einen personalisierten, interaktiven Fahrplan für alle Genehmigungen Ihres Immobilienprojekts in Deutschland — vom Bebauungsplan bis zur Bauabnahme.",
    "permit.feat1.title": "7-Phasen-Fahrplan",
    "permit.feat1.desc": "Vollständiger Schritt-für-Schritt-Prozess von der ersten Prüfung bis zur Abnahme",
    "permit.feat2.title": "Dokumenten-Checkliste",
    "permit.feat2.desc": "Jedes Formular, jede Zeichnung und jeder Nachweis für jede Phase",
    "permit.feat3.title": "Behördenkontakte",
    "permit.feat3.desc": "Direkte Links zur richtigen Behörde für jeden Schritt in Ihrem Bundesland",
    "permit.locked": "4 weitere Schritte gesperrt…",
    "permit.unlock": "Schalten Sie den vollständigen Genehmigungsprozess mit einer Mitgliedschaft frei",
    "permit.demo": "Demo ansehen",
    "permit.plan1.name": "Basis",
    "permit.plan1.price": "€0",
    "permit.plan1.desc": "Für gelegentliche Anfragen",
    "permit.plan1.f1": "KI-Rechtsberater (5 Fragen/Tag)",
    "permit.plan1.f2": "Rechtszitate inklusive",
    "permit.plan1.f3": "Zuverlässigkeitsbewertungen",
    "permit.plan1.cta": "Kostenlos starten",
    "permit.plan2.name": "Professional",
    "permit.plan2.price": "€29/Monat",
    "permit.plan2.desc": "Für ernsthafte Immobilieneigentümer",
    "permit.plan2.f1": "Unbegrenzter KI-Berater-Zugang",
    "permit.plan2.f2": "Vollständiger Genehmigungsassistent",
    "permit.plan2.f3": "Personalisierte Fahrpläne",
    "permit.plan2.f4": "Dokumenten-Checklisten",
    "permit.plan2.f5": "Bevorzugter Support",
    "permit.plan2.cta": "Mitglied werden",
    "permit.popular": "Beliebteste Wahl",
    "permit.wizard.title": "Genehmigungsassistent",
    "permit.wizard.sub": "Deutschland · Alle Bundesländer",
    "permit.wizard.steps": "Schritte",
    "permit.proj.extension": "Anbau",
    "permit.proj.renovation": "Kernsanierung",
    "permit.proj.newbuild": "Neubau",
    "permit.proj.conversion": "Nutzungsänderung",
    "permit.step.tasks": "Aufgaben & Checkliste",
    "permit.step.legal": "Rechtsgrundlage",
    "permit.step.tip": "Profi-Tipp",
    "permit.step.complete": "Als erledigt markieren",
    "permit.step.incomplete": "✓ Als unerledigt markieren",
    "permit.cta.question": "Haben Sie Fragen zu diesen Schritten?",
    "permit.cta.btn": "KI-Berater fragen",
    "permit.header.title": "Genehmigungsverfahren — Anbau",
  },
};

const LanguageContext = createContext<LanguageContextType>({
  lang: "en",
  setLang: () => {},
  t: (key) => key,
});

export const LanguageProvider = ({ children }: { children: ReactNode }) => {
  const [lang, setLang] = useState<Language>("en");

  const t = (key: string): string => {
    return translations[lang][key] ?? translations["en"][key] ?? key;
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);
