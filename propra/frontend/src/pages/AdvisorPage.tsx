import { useState, useRef, useEffect } from "react";
import {
  Send, Scale, BookOpen, Shield, ChevronDown, ChevronUp, Copy,
  ThumbsUp, ThumbsDown, Loader2, FileSignature, Bell,
  CheckCircle2, Circle, Search, Check, Building2, MapPin, Layers, Tag, Home, Trees,
} from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useLanguage } from "@/context/LanguageContext";

const BUNDESLAENDER = [
  "Baden-Württemberg",
  "Bayern",
  "Berlin",
  "Brandenburg",
  "Bremen",
  "Hamburg",
  "Hessen",
  "Mecklenburg-Vorpommern",
  "Niedersachsen",
  "Nordrhein-Westfalen",
  "Rheinland-Pfalz",
  "Saarland",
  "Sachsen",
  "Sachsen-Anhalt",
  "Schleswig-Holstein",
  "Thüringen",
];

interface Source {
  code: string;
  section: string;
  title: string;
  excerpt: string;
  url?: string;
}

interface ResponseData {
  content: string;
  sources: Source[];
  reliability: number;
  reliabilityLabel: string;
  documentBlock?: string;
}

interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  reliability?: number;
  reliabilityLabel?: string;
  timestamp: Date;
  documentBlock?: string;
  classificationLabel?: string;
  awaitingClassification?: boolean;
}

interface CaseStep {
  label: string;
  done: boolean;
}

interface Case {
  id: number;
  title: string;
  status: "in_progress" | "completed" | "pending";
  date: string;
  deadline?: string;
  steps: CaseStep[];
}

const WIDERSPRUCH_LETTER = `Einschreiben mit Rückschein

An die
Stadtentwicklungsbehörde / Baurechtsamt
[Behörde und Adresse]
[PLZ und Ort]

Ihr Zeichen: 2024-BG-00142
[Ort], den [Datum]

Widerspruch gegen Baugenehmigung vom 15. Januar 2024
– Az. 2024-BG-00142, Bauvorhaben Musterstraße 12 –

Sehr geehrte Damen und Herren,

hiermit erhebe ich fristgerecht Widerspruch gemäß § 70 VwGO gegen Ihren
Bescheid vom 15. Januar 2024 (Az.: 2024-BG-00142), mit dem dem Eigentümer
des Grundstücks Musterstraße 12, 10115 Berlin, eine Baugenehmigung für
den Neubau eines viergeschossigen Wohngebäudes erteilt wurde.

I. BEGRÜNDUNG

1. Verstoß gegen den Bebauungsplan (§§ 29, 30 BauGB)

Das genehmigte Vorhaben überschreitet die im rechtskräftigen Bebauungsplan
Nr. II-45 festgesetzte Geschossflächenzahl (GFZ) von 0,8 erheblich. Nach
meiner Berechnung erreicht das Vorhaben eine GFZ von 1,2, was einen Verstoß
gegen die verbindlichen Festsetzungen des § 30 Abs. 1 BauGB darstellt.

2. Verletzung der Abstandsflächenvorschriften (§ 6 BauO Bln)

Gemäß § 6 Abs. 5 BauO Bln ist eine Mindesttiefe der Abstandsflächen von
3 Metern einzuhalten. Das genehmigte Bauvorhaben hält zu meinem Grundstück
lediglich 1,5 Meter ein und verletzt damit nachbarschützende Vorschriften.

3. Verstoß gegen das Rücksichtnahmegebot (§ 15 Abs. 1 BauNVO)

Das Vorhaben führt zu einer unzumutbaren Verschattung meines Wohngebäudes.
In den Wintermonaten werden die Hauptwohnräume mehr als sechs Stunden täglich
ohne Direktbesonnung bleiben, was die Grenze des Zumutbaren überschreitet
(vgl. BVerwG, Urteil vom 23. Mai 1986, Az. 4 C 34/85).

II. ANTRAG

Ich beantrage, den angefochtenen Bescheid aufzuheben und die Baugenehmigung
zu versagen, hilfsweise nur unter Auflagen zur Einhaltung der Abstandsflächen
und einer GFZ von maximal 0,8 zu erteilen.

Mit freundlichen Grüßen

_________________________
[Ihr vollständiger Name]
[Straße, Hausnummer]
[PLZ, Ort]
[Telefon / E-Mail]`;

const STELLUNGNAHME_LETTER = `An die Gemeinde [Gemeindename]
Stadtplanungsamt
[Adresse]
[PLZ und Ort]

[Ort], den [Datum]

Stellungnahme gemäß § 3 Abs. 2 BauGB
zum Bebauungsplanentwurf Nr. B-Plan 45-2

Sehr geehrte Damen und Herren,

im Rahmen der öffentlichen Auslegung gemäß § 3 Abs. 2 BauGB nehme ich als
Eigentümer des Grundstücks [Ihre Adresse] zu dem ausgelegten Bebauungsplan-
entwurf Nr. B-Plan 45-2 wie folgt Stellung:

I. ALLGEMEINE BEDENKEN

Der vorliegende Entwurf sieht eine erhebliche Verdichtung des bestehenden
Wohngebiets vor. Die Infrastrukturkapazitäten — insbesondere Straßennetz,
Parkraum und Grünflächenversorgung — sind für die geplante Nutzungsintensität
nicht ausgelegt.

II. KONKRETE RECHTLICHE EINWÄNDE

1. Überschreitung der zulässigen Bebauungsdichte (§ 17 BauNVO)

Die vorgesehene Grundflächenzahl (GRZ) von 0,6 überschreitet den nach
§ 17 Abs. 1 BauNVO für allgemeine Wohngebiete (WA) geltenden Höchstwert
von 0,4 ohne die nach § 17 Abs. 2 BauNVO erforderliche besondere städte-
bauliche Begründung.

2. Mangelnde gesicherte Erschließung (§ 30 Abs. 1 BauGB)

Eine gesicherte Erschließung gemäß § 30 Abs. 1 BauGB ist nicht gegeben.
Ein aktuelles Verkehrsgutachten liegt nicht vor; die angrenzenden Erschlie-
ßungsstraßen sind für das prognostizierte Verkehrsaufkommen nicht ausgelegt.

3. Unzureichende Eingriffsbilanzierung (§ 1a Abs. 3 BauGB)

Der Entwurf enthält keine ausreichende Eingriffs- und Ausgleichsbilanz
gemäß § 1a Abs. 3 BauGB. Der vollständige Verlust von ca. [X m²] Grünfläche
wurde nicht kompensiert.

III. FORDERUNGEN

Ich fordere die Gemeinde auf, den Entwurf zu überarbeiten:
– Reduzierung der GRZ auf den gesetzlichen Höchstwert von 0,4
– Vorlage eines aktuellen Verkehrsgutachtens vor Satzungsbeschluss
– Vollständige Eingriffs- und Ausgleichsbilanz gemäß § 1a Abs. 3 BauGB

Mit freundlichen Grüßen

_________________________
[Ihr vollständiger Name]
[Grundstücksadresse]
[Datum]`;

const CASES: Case[] = [
  {
    id: 1,
    title: "Widerspruch gegen Baugenehmigung Nachbar",
    status: "in_progress",
    date: "12.02.2024",
    deadline: "15.03.2024",
    steps: [
      { label: "Dokument erstellt", done: true },
      { label: "Eingereicht beim Bauamt", done: true },
      { label: "Stellungnahme angefordert", done: false },
      { label: "Entscheidung ausstehend", done: false },
    ],
  },
  {
    id: 2,
    title: "Eigenbedarfskündigung – Rechtslage prüfen",
    status: "completed",
    date: "08.01.2024",
    steps: [
      { label: "Rechtslage analysiert", done: true },
      { label: "Widerspruch formuliert", done: true },
      { label: "Einigung erzielt", done: true },
    ],
  },
  {
    id: 3,
    title: "Grunderwerbsteuer-Einspruch vorbereiten",
    status: "pending",
    date: "28.02.2024",
    steps: [
      { label: "Unterlagen zusammenstellen", done: false },
      { label: "Einspruch einreichen", done: false },
      { label: "Finanzamt-Antwort abwarten", done: false },
    ],
  },
];

const SAMPLE_RESPONSES: { [key: string]: ResponseData } = {
  default: {
    content: `Based on German property law, I can provide you with a comprehensive answer to your question.

The relevant legal framework in Germany provides specific protections and obligations for property owners and tenants. The Bürgerliches Gesetzbuch (BGB) serves as the primary legal source for property-related matters, supplemented by state-specific regulations (Landesrecht) that vary by Bundesland.

**Key Legal Points:**
- German property law distinguishes between *Eigentum* (ownership) and *Besitz* (possession) — a crucial distinction under § 903 BGB
- Property transactions must be notarized (*notarielle Beurkundung*) as required under § 311b BGB
- The Grundbuch (land register) is the authoritative record of property rights under the Grundbuchordnung (GBO)

**Practical Implications:**
Your rights and obligations depend heavily on the specific circumstances of your property and its location, as municipal building codes (*Bebauungspläne*) can significantly affect what is permissible.

I recommend consulting the specific §§ cited below and, for binding advice, engaging a *Rechtsanwalt* specializing in *Immobilienrecht*.`,
    sources: [
      {
        code: "BGB",
        section: "§ 903",
        title: "Befugnisse des Eigentümers",
        excerpt: "Der Eigentümer einer Sache kann, soweit nicht das Gesetz oder Rechte Dritter entgegenstehen, mit der Sache nach Belieben verfahren und andere von jeder Einwirkung ausschließen.",
      },
      {
        code: "BGB",
        section: "§ 311b Abs. 1",
        title: "Verträge über Grundstücke",
        excerpt: "Ein Vertrag, durch den sich der eine Teil verpflichtet, das Eigentum an einem Grundstück zu übertragen oder zu erwerben, bedarf der notariellen Beurkundung.",
      },
      {
        code: "GBO",
        section: "§ 1",
        title: "Grundbuchordnung — Grundsatz",
        excerpt: "Die Grundbücher werden von den Amtsgerichten als Grundbuchämtern geführt.",
      },
    ],
    reliability: 87,
    reliabilityLabel: "High Confidence",
  },
};

const MOCK_RESPONSES: { keywords: string[]; response: ResponseData }[] = [
  {
    keywords: ["schreiben", "widerspruch", "dokument", "brief"],
    response: {
      content: `Ich habe für Sie ein rechtssicheres **Widerspruchsschreiben** erstellt, das auf die einschlägigen Vorschriften des BauGB, der VwGO und der BauO Bln gestützt ist.

Das Schreiben enthält:
- Formelle Einleitung mit Aktenzeichen und Bezugszeile
- Rechtliche Begründung mit konkreten §§-Verweisen (§ 30 BauGB, § 6 BauO Bln, § 15 BauNVO)
- Klar formulierte Anträge (Haupt- und Hilfsantrag)

Bitte ersetzen Sie alle Angaben in **[eckigen Klammern]** durch Ihre persönlichen Daten. Das fertige Schreiben kann per Einschreiben mit Rückschein an die zuständige Behörde gesandt werden.`,
      documentBlock: WIDERSPRUCH_LETTER,
      sources: [
        {
          code: "VwGO",
          section: "§ 70",
          title: "Widerspruch",
          excerpt: "Über den Widerspruch entscheidet die nächsthöhere Behörde, soweit nicht durch Gesetz eine andere höhere Behörde bestimmt wird.",
        },
        {
          code: "BauGB",
          section: "§ 29",
          title: "Begriff des Vorhabens",
          excerpt: "Für Vorhaben, die die Errichtung, Änderung oder Nutzungsänderung von baulichen Anlagen zum Inhalt haben, gelten die §§ 30 bis 37.",
        },
        {
          code: "BauO Bln",
          section: "§ 6 Abs. 5",
          title: "Abstandsflächen",
          excerpt: "Die Tiefe der Abstandsfläche beträgt 0,4 H, mindestens 3 m.",
        },
      ],
      reliability: 88,
      reliabilityLabel: "High Confidence",
    },
  },
  {
    keywords: ["stellungnahme"],
    response: {
      content: `Ich habe für Sie eine rechtssichere **Stellungnahme** zum Bebauungsplanentwurf erstellt, gestützt auf § 3 Abs. 2 BauGB, § 17 BauNVO und § 1a BauGB.

Das Schreiben enthält:
- Formelle Einleitung gemäß § 3 Abs. 2 BauGB (Öffentlichkeitsbeteiligung)
- Konkrete rechtliche Einwände mit §§-Verweisen
- Klar formulierte Forderungen an die Gemeinde

Bitte ergänzen Sie die in **[eckigen Klammern]** markierten Felder mit Ihren Angaben.`,
      documentBlock: STELLUNGNAHME_LETTER,
      sources: [
        {
          code: "BauGB",
          section: "§ 3 Abs. 2",
          title: "Öffentlichkeitsbeteiligung",
          excerpt: "Die Entwürfe der Bauleitpläne sind mit der Begründung und den nach Einschätzung der Gemeinde wesentlichen, bereits vorliegenden umweltbezogenen Stellungnahmen für die Dauer eines Monats öffentlich auszulegen.",
        },
        {
          code: "BauNVO",
          section: "§ 17",
          title: "Obergrenzen für die Bestimmung des Maßes der baulichen Nutzung",
          excerpt: "Bei der Bestimmung des Maßes der baulichen Nutzung nach § 16 sind die in Absatz 1 festgesetzten Obergrenzen zu beachten.",
        },
        {
          code: "BauGB",
          section: "§ 1a Abs. 3",
          title: "Ergänzende Vorschriften zum Umweltschutz",
          excerpt: "Die Vermeidung und der Ausgleich voraussichtlich erheblicher Beeinträchtigungen des Landschaftsbildes sowie der Leistungs- und Funktionsfähigkeit des Naturhaushalts sind in der Abwägung zu berücksichtigen.",
        },
      ],
      reliability: 85,
      reliabilityLabel: "High Confidence",
    },
  },
  {
    keywords: ["eigenbedarf", "tenant", "landlord", "terminate", "eviction"],
    response: {
      content: `**Eigenbedarfskündigung** (termination for personal use) is regulated under § 573 Abs. 2 Nr. 2 BGB and grants landlords the right to terminate a tenancy if they genuinely need the property for themselves or close family members.

**Requirements for a Valid Eigenbedarf Claim:**
- The landlord must have a **legitimate and concrete** need (*berechtigt und konkret*)
- The person named must be the landlord, their household members, or close relatives
- The landlord must state the specific reasons in writing in the termination notice
- The notice period depends on the duration of the tenancy (3–9 months per § 573c BGB)

**Tenant Protections:**
- Tenants may object to termination if it causes *undue hardship* (*soziale Härte*) under § 574 BGB
- Fictitious Eigenbedarf (Vorgetäuschter Eigenbedarf) gives tenants the right to claim damages
- Tenants aged 70+ or with severe disabilities receive enhanced protection

**Recent Court Decisions:**
German courts apply strict scrutiny to Eigenbedarf claims. The BGH has repeatedly ruled that the landlord's need must be *current*, not speculative.`,
      sources: [
        {
          code: "BGB",
          section: "§ 573 Abs. 2 Nr. 2",
          title: "Berechtigtes Interesse des Vermieters",
          excerpt: "Ein berechtigtes Interesse des Vermieters an der Beendigung des Mietverhältnisses liegt vor, wenn der Vermieter die Räume als Wohnung für sich, seine Familienangehörigen oder Angehörige seines Haushalts benötigt.",
        },
        {
          code: "BGB",
          section: "§ 573c",
          title: "Kündigungsfristen bei der Kündigung des Mietverhältnisses",
          excerpt: "Die Kündigung ist spätestens am dritten Werktag eines Kalendermonats zum Ablauf des übernächsten Monats zulässig. Die Kündigungsfrist für den Vermieter verlängert sich nach fünf und acht Jahren seit der Überlassung des Wohnraums um jeweils drei Monate.",
        },
        {
          code: "BGB",
          section: "§ 574",
          title: "Widerspruch des Mieters",
          excerpt: "Der Mieter kann der Kündigung des Vermieters widersprechen und von ihm die Fortsetzung des Mietverhältnisses verlangen, wenn die Beendigung des Mietverhältnisses für den Mieter, seine Familie oder einen anderen Angehörigen seines Haushalts eine Härte bedeuten würde.",
        },
      ],
      reliability: 92,
      reliabilityLabel: "Very High Confidence",
    },
  },
  {
    keywords: ["permit", "balcony", "extension", "build", "renovate", "construction"],
    response: {
      content: `**Building permits** (*Baugenehmigungen*) in Germany are governed by state-level building codes (*Landesbauordnungen — LBO*), so requirements vary by Bundesland. However, the federal Baugesetzbuch (BauGB) sets overarching principles.

**When is a Permit Required?**
- **New structures** and **substantial modifications** generally require approval
- **Balconies and extensions** typically require a permit, though small additions may qualify as *verfahrensfreie Bauvorhaben* (permit-free works) depending on size thresholds
- In Berlin: extensions up to 10m² of new floor space may be permit-free under § 62 BauO Bln
- In Bavaria: up to 75m³ of additional volume is often permit-free under Art. 57 BayBO

**Process Overview:**
1. Consult your local *Bauamt* (building authority)
2. Check the *Bebauungsplan* (development plan) for your plot
3. Engage a licensed *Bauvorlageberechtigter* (qualified architect) if required
4. Submit application with drawings, site plans, and structural calculations

**Key Consideration:** Even if the project is technically permit-free, you must comply with the applicable LBO, BauNVO setback rules, and any *Denkmalschutz* (heritage protection) requirements.`,
      sources: [
        {
          code: "BauGB",
          section: "§ 29",
          title: "Begriff des Vorhabens",
          excerpt: "Für Vorhaben, die die Errichtung, Änderung oder Nutzungsänderung von baulichen Anlagen zum Inhalt haben, und für Aufschüttungen und Abgrabungen größeren Umfangs sowie für Ausschachtungen, Ablagerungen einschließlich Lagerstätten gelten die §§ 30 bis 37.",
        },
        {
          code: "BauNVO",
          section: "§ 23",
          title: "Überbaubare Grundstücksfläche",
          excerpt: "Ist eine Baulinie festgesetzt, so muss auf ihr gebaut werden. Ist eine Baugrenze festgesetzt, so dürfen Gebäude und Gebäudeteile diese nicht überschreiten.",
        },
        {
          code: "BauO Bln",
          section: "§ 62",
          title: "Verfahrensfreie Bauvorhaben",
          excerpt: "Verfahrensfrei sind: Gebäude ohne Aufenthaltsräume, Toiletten und Feuerstätten, wenn die Grundfläche nicht mehr als 10 Quadratmeter beträgt.",
        },
      ],
      reliability: 84,
      reliabilityLabel: "High Confidence",
    },
  },
  {
    keywords: ["grunderwerbsteuer", "transfer tax", "purchase", "buy", "tax"],
    response: {
      content: `**Grunderwerbsteuer** (Real Estate Transfer Tax) is levied on property transactions in Germany under the Grunderwerbsteuergesetz (GrEStG) and represents a significant cost in property acquisitions.

**Tax Rates by Bundesland (2024):**
| State | Rate |
|-------|------|
| Bavaria, Saxony | 3.5% |
| Hamburg | 5.5% |
| Berlin, Hesse | 6.0% |
| Brandenburg, Saarland, Schleswig-Holstein | 6.5% |
| Most other states | 5.0–6.0% |

**Tax Base:**
The tax is calculated on the *Bemessungsgrundlage*, typically the purchase price (§ 8 GrEStG). Connected transactions (e.g., simultaneous purchase of furnishings) may be excluded if properly documented.

**Exemptions Under § 3 GrEStG:**
- Transactions between spouses or registered partners are exempt
- Acquisitions by direct line relatives (parents/children) are exempt
- Transfers under inheritance law are generally exempt

**Share Deals:**
Acquiring a property-holding company (share deal) can defer the tax if the threshold of 90% ownership change is not reached within 10 years (§ 1 Abs. 3 GrEStG), though recent reforms have tightened this.`,
      sources: [
        {
          code: "GrEStG",
          section: "§ 1 Abs. 1",
          title: "Erwerbsvorgänge",
          excerpt: "Der Grunderwerbsteuer unterliegen die folgenden Rechtsvorgänge, soweit sie sich auf inländische Grundstücke beziehen: ein Kaufvertrag oder ein anderes Rechtsgeschäft, das den Anspruch auf Übereignung begründet.",
        },
        {
          code: "GrEStG",
          section: "§ 8",
          title: "Grundsatz der Bemessung",
          excerpt: "Die Steuer bemisst sich nach dem Wert der Gegenleistung. Die Gegenleistung ist in den Fällen der Abtretung von Übereignungsansprüchen der Wert des abgetretenen Anspruchs.",
        },
        {
          code: "GrEStG",
          section: "§ 3 Nr. 4",
          title: "Allgemeine Ausnahmen von der Besteuerung",
          excerpt: "Von der Besteuerung sind ausgenommen: der Erwerb eines Grundstücks durch den Ehegatten oder den Lebenspartner des Veräußerers.",
        },
      ],
      reliability: 95,
      reliabilityLabel: "Very High Confidence",
    },
  },
];

const getResponse = (question: string): ResponseData => {
  const lower = question.toLowerCase();
  for (const mock of MOCK_RESPONSES) {
    if (mock.keywords.some((k) => lower.includes(k))) {
      return mock.response;
    }
  }
  return SAMPLE_RESPONSES.default;
};

const classifyQuestion = (text: string): string | null => {
  const lower = text.toLowerCase();
  if (["zaun", "grenze", "hecke"].some((k) => lower.includes(k))) return "Zaun / Grenze";
  if (["fenster", "öffnung", "tür"].some((k) => lower.includes(k))) return "Fenster / Öffnung";
  if (["garten", "terrasse", "schuppen"].some((k) => lower.includes(k))) return "Gartenanlage";
  return null;
};

const CLASSIFICATION_TILES = ["Zaun / Grenze", "Fenster / Öffnung", "Gartenanlage"];

const ReliabilityBadge = ({ score, label }: { score: number; label: string }) => {
  const color =
    score >= 90 ? "text-emerald-700 bg-emerald-50 border-emerald-200" :
    score >= 75 ? "text-blue-700 bg-blue-50 border-blue-200" :
    "text-amber-700 bg-amber-50 border-amber-200";

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-body font-medium ${color}`}>
      <Shield className="w-3 h-3" />
      {label} — {score}% confidence
    </div>
  );
};

const SourceCard = ({ source, index }: { source: Source; index: number }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-border rounded-xl overflow-hidden bg-cream hover:border-gold/30 transition-colors">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 hover:bg-gold-muted/30 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-navy flex items-center justify-center shrink-0">
            <span className="text-primary-foreground text-xs font-body font-bold">{index + 1}</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-body font-bold text-gold">{source.code}</span>
              <span className="text-xs font-body font-semibold text-foreground">{source.section}</span>
            </div>
            <div className="text-xs text-muted-foreground font-body">{source.title}</div>
          </div>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
      </button>
      {expanded && (
        <div className="px-4 pb-3 pt-0 border-t border-border">
          <p className="text-xs font-body text-muted-foreground italic leading-relaxed mt-2">
            "{source.excerpt}"
          </p>
        </div>
      )}
    </div>
  );
};

const DocumentCard = ({ content, title, copyLabel, copiedLabel, wordsLabel }: {
  content: string;
  title: string;
  copyLabel: string;
  copiedLabel: string;
  wordsLabel: string;
}) => {
  const [copied, setCopied] = useState(false);
  const wordCount = content.trim().split(/\s+/).length;

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mt-4 border border-gold/30 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-gold/20 bg-gold-muted/30">
        <div className="flex items-center gap-2">
          <FileSignature className="w-4 h-4 text-gold" />
          <span className="text-xs font-body font-semibold text-foreground">Entwurf: {title}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground font-body">{wordCount} {wordsLabel}</span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-gold/15 hover:bg-gold/25 text-gold text-xs font-body font-medium transition-colors"
          >
            <Copy className="w-3 h-3" />
            {copied ? copiedLabel : copyLabel}
          </button>
        </div>
      </div>
      <div className="p-4 max-h-64 overflow-y-auto bg-cream/50">
        <pre className="text-xs font-mono text-foreground/80 whitespace-pre-wrap leading-relaxed">{content}</pre>
      </div>
    </div>
  );
};

const CaseCard = ({ case: c, statusConfig, stepsLabel, deadlineLabel }: {
  case: Case;
  statusConfig: Record<string, { label: string; className: string }>;
  stepsLabel: string;
  deadlineLabel: string;
}) => {
  const doneSteps = c.steps.filter((s) => s.done).length;
  const progress = Math.round((doneSteps / c.steps.length) * 100);
  const status = statusConfig[c.status];

  return (
    <div className="border border-border rounded-xl p-4 bg-background hover:border-gold/30 hover:shadow-sm transition-all">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h3 className="font-body font-semibold text-foreground text-sm">{c.title}</h3>
          <p className="text-xs text-muted-foreground font-body mt-0.5">{c.date}</p>
        </div>
        <span className={`shrink-0 inline-flex items-center px-2.5 py-1 rounded-full border text-xs font-body font-medium ${status.className}`}>
          {status.label}
        </span>
      </div>

      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-muted-foreground font-body">{doneSteps}/{c.steps.length} {stepsLabel}</span>
          <span className="text-xs text-muted-foreground font-body">{progress}%</span>
        </div>
        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              c.status === "completed" ? "bg-emerald-500" :
              c.status === "in_progress" ? "bg-blue-500" : "bg-amber-400"
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {c.steps.map((step, i) => (
          <span
            key={i}
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-body ${
              step.done ? "bg-emerald-50 text-emerald-700" : "bg-muted text-muted-foreground"
            }`}
          >
            {step.done ? <CheckCircle2 className="w-3 h-3" /> : <Circle className="w-3 h-3" />}
            {step.label}
          </span>
        ))}
      </div>

      {c.deadline && c.status === "in_progress" && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-50 border border-amber-200">
          <Bell className="w-3.5 h-3.5 text-amber-600 shrink-0" />
          <span className="text-xs font-body text-amber-700">
            <strong>{deadlineLabel}:</strong> {c.deadline} — Widerspruch muss eingereicht sein
          </span>
        </div>
      )}
    </div>
  );
};

const AdvisorPage = () => {
  const { t } = useLanguage();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"berater" | "vorgaenge">("berater");
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const bundeslandRef = useRef<HTMLDivElement>(null);

  // Guided context inputs
  const [bundesland, setBundesland] = useState("");
  const [bundeslandSearch, setBundeslandSearch] = useState("");
  const [bundeslandOpen, setBundeslandOpen] = useState(false);
  const [propertyType, setPropertyType] = useState("");
  const [insideOutside, setInsideOutside] = useState<"inside" | "outside" | "">("");
  const [postcode, setPostcode] = useState("");
  const [floors, setFloors] = useState("");

  const contextReady =
    bundesland !== "" &&
    propertyType !== "" &&
    insideOutside !== "" &&
    (insideOutside !== "inside" || (floors !== "" && Number(floors) > 0));

  // Close Bundesland dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (bundeslandRef.current && !bundeslandRef.current.contains(e.target as Node)) {
        setBundeslandOpen(false);
      }
    };
    if (bundeslandOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [bundeslandOpen]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const statusConfig = {
    in_progress: { label: t("status.in_progress"), className: "bg-blue-50 text-blue-700 border-blue-200" },
    completed: { label: t("status.completed"), className: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    pending: { label: t("status.pending"), className: "bg-amber-50 text-amber-700 border-amber-200" },
  };

  const sendMessage = async (text?: string) => {
    const question = text || input.trim();
    if (!question || loading) return;

    const userMsg: Message = {
      id: Date.now(),
      role: "user",
      content: question,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    await new Promise((r) => setTimeout(r, 1800 + Math.random() * 800));

    const resp = getResponse(question);
    const label = classifyQuestion(question);
    const aiMsg: Message = {
      id: Date.now() + 1,
      role: "assistant",
      content: resp.content,
      sources: resp.sources,
      reliability: resp.reliability,
      reliabilityLabel: resp.reliabilityLabel,
      timestamp: new Date(),
      documentBlock: resp.documentBlock,
      classificationLabel: label ?? undefined,
      awaitingClassification: label === null,
    };

    setMessages((prev) => [...prev, aiMsg]);
    setLoading(false);
  };

  const setMessageClassification = (id: number, label: string) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === id ? { ...m, classificationLabel: label, awaitingClassification: false } : m
      )
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const renderContent = (text: string) => {
    return text.split("\n").map((line, i) => {
      if (line.startsWith("**") && line.endsWith("**")) {
        return <p key={i} className="font-semibold text-foreground mt-3 mb-1 first:mt-0">{line.slice(2, -2)}</p>;
      }
      if (line.startsWith("- ")) {
        return <li key={i} className="ml-4 text-foreground/85">{line.slice(2)}</li>;
      }
      if (line.trim() === "") return <br key={i} />;
      const parts = line.split(/(\*\*[^*]+\*\*)/g);
      return (
        <p key={i} className="text-foreground/85 leading-relaxed">
          {parts.map((p, j) =>
            p.startsWith("**") && p.endsWith("**")
              ? <strong key={j} className="font-semibold text-foreground">{p.slice(2, -2)}</strong>
              : p
          )}
        </p>
      );
    });
  };

  return (
    <div className="min-h-screen bg-background pt-16 flex flex-col">
      <div className="container mx-auto px-4 max-w-4xl flex-1 flex flex-col py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <div className="w-11 h-11 rounded-xl bg-navy border border-gold/30 flex items-center justify-center shadow-md">
            <Scale className="w-5 h-5 text-gold" />
          </div>
          <div>
            <h1 className="font-display text-2xl font-bold text-foreground">{t("advisor.title")}</h1>
            <p className="text-muted-foreground text-sm font-body">{t("advisor.sub")}</p>
          </div>
          <div className="ml-auto hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-emerald-700 text-xs font-body font-medium">{t("advisor.online")}</span>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "berater" | "vorgaenge")} className="flex-1 flex flex-col">
          <TabsList className="mb-5 self-start bg-muted">
            <TabsTrigger value="berater" className="font-body text-sm gap-2">
              <Scale className="w-3.5 h-3.5" />
              {t("advisor.tab.advisor")}
            </TabsTrigger>
            <TabsTrigger value="vorgaenge" className="font-body text-sm gap-2">
              <BookOpen className="w-3.5 h-3.5" />
              {t("advisor.tab.cases")}
            </TabsTrigger>
          </TabsList>

          {/* ── Tab 1: AI Advisor ── */}
          <TabsContent value="berater" className="flex-1 flex flex-col mt-0">
            {/* Greeting */}
            <div className="flex gap-4 mb-5 animate-fade-up">
              <div className="w-9 h-9 rounded-xl bg-navy border border-gold/30 flex items-center justify-center shrink-0 mt-1">
                <Scale className="w-4 h-4 text-gold" />
              </div>
              <div className="max-w-[85%]">
                <div className="bg-card border border-border rounded-2xl rounded-tl-sm p-5 shadow-sm">
                  <p className="font-body text-sm leading-relaxed">{t("advisor.greeting")}</p>
                </div>
              </div>
            </div>

            {/* Guided context inputs */}
            <div className={`mb-5 border rounded-2xl transition-all ${contextReady ? "border-gold/40 bg-gold-muted/10" : "border-border bg-card"}`}>
              <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
                <Building2 className="w-4 h-4 text-gold shrink-0" />
                <div>
                  <p className="text-sm font-body font-semibold text-foreground">{t("advisor.context.title")}</p>
                  <p className="text-xs text-muted-foreground font-body">{t("advisor.context.sub")}</p>
                </div>
                {contextReady && (
                  <span className="ml-auto flex items-center gap-1.5 text-xs font-body font-medium text-gold">
                    <Check className="w-3.5 h-3.5" />
                    {t("advisor.context.ready")}
                  </span>
                )}
              </div>

              <div className="p-4 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* 1 — Bundesland searchable dropdown */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-body font-semibold text-foreground flex items-center gap-1.5">
                    <MapPin className="w-3 h-3 text-gold" />
                    {t("advisor.context.bundesland.label")}
                  </label>
                  <div className="relative" ref={bundeslandRef}>
                    <button
                      type="button"
                      onClick={() => { setBundeslandOpen((o) => !o); if (!bundeslandOpen) setBundeslandSearch(""); }}
                      className={`w-full flex items-center justify-between h-10 px-3 rounded-xl border text-sm font-body transition-colors ${
                        bundesland
                          ? "border-gold/40 bg-gold-muted/10 text-foreground"
                          : "border-border bg-background text-muted-foreground"
                      } hover:border-gold/50`}
                    >
                      <span className="truncate">{bundesland || t("advisor.context.bundesland.placeholder")}</span>
                      <ChevronDown className={`w-4 h-4 shrink-0 ml-2 transition-transform ${bundeslandOpen ? "rotate-180" : ""}`} />
                    </button>
                    {bundeslandOpen && (
                      <div className="absolute z-50 mt-1 w-full bg-popover border border-border rounded-xl shadow-lg overflow-hidden">
                        <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
                          <Search className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                          <input
                            value={bundeslandSearch}
                            onChange={(e) => setBundeslandSearch(e.target.value)}
                            placeholder={t("advisor.context.bundesland.placeholder")}
                            className="flex-1 text-sm font-body bg-transparent outline-none text-foreground placeholder:text-muted-foreground"
                          />
                        </div>
                        <div className="max-h-48 overflow-y-auto py-1">
                          {BUNDESLAENDER
                            .filter((bl) => bl.toLowerCase().includes(bundeslandSearch.toLowerCase()))
                            .map((bl) => (
                              <button
                                key={bl}
                                type="button"
                                onClick={() => { setBundesland(bl); setBundeslandOpen(false); }}
                                className={`w-full text-left px-3 py-2 text-sm font-body hover:bg-accent hover:text-accent-foreground transition-colors flex items-center justify-between ${bundesland === bl ? "text-gold font-medium" : "text-foreground"}`}
                              >
                                {bl}
                                {bundesland === bl && <Check className="w-3.5 h-3.5 text-gold" />}
                              </button>
                            ))
                          }
                          {BUNDESLAENDER.filter((bl) => bl.toLowerCase().includes(bundeslandSearch.toLowerCase())).length === 0 && (
                            <p className="px-3 py-4 text-xs text-muted-foreground font-body text-center">{t("advisor.context.bundesland.empty")}</p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* 2 — Property type dropdown */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-body font-semibold text-foreground flex items-center gap-1.5">
                    <Building2 className="w-3 h-3 text-gold" />
                    {t("advisor.context.proptype.label")}
                  </label>
                  <div className="relative group">
                    <select
                      value={propertyType}
                      onChange={(e) => setPropertyType(e.target.value)}
                      className={`w-full h-10 px-3 rounded-xl border text-sm font-body appearance-none cursor-pointer transition-colors pr-8 ${
                        propertyType
                          ? "border-gold/40 bg-gold-muted/10 text-foreground"
                          : "border-border bg-background text-muted-foreground"
                      } hover:border-gold/50 focus:outline-none focus:border-gold/50`}
                    >
                      <option value="" disabled>{t("advisor.context.proptype.placeholder")}</option>
                      <option value="einfamilienhaus">{t("advisor.context.proptype.einfamilienhaus")}</option>
                      <option value="mehrfamilienhaus">{t("advisor.context.proptype.mehrfamilienhaus")}</option>
                      <option value="gewerbe">{t("advisor.context.proptype.gewerbe")}</option>
                      <option value="gemischte">{t("advisor.context.proptype.gemischte")}</option>
                      <option value="sonderbau">{t("advisor.context.proptype.sonderbau")}</option>
                    </select>
                    <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                  </div>
                </div>

                {/* 3 — Inside / Outside tiles */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-body font-semibold text-foreground flex items-center gap-1.5">
                    <Home className="w-3 h-3 text-gold" />
                    {t("advisor.context.insideoutside.label")}
                  </label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => { setInsideOutside("inside"); setFloors(""); }}
                      className={`flex-1 flex items-center justify-center gap-1.5 h-10 rounded-xl border text-sm font-body transition-colors ${
                        insideOutside === "inside"
                          ? "border-gold/50 bg-gold-muted/20 text-foreground font-medium"
                          : "border-border bg-background text-muted-foreground hover:border-gold/40"
                      }`}
                    >
                      <Home className="w-3.5 h-3.5" />
                      {t("advisor.context.insideoutside.inside")}
                    </button>
                    <button
                      type="button"
                      onClick={() => { setInsideOutside("outside"); setFloors(""); }}
                      className={`flex-1 flex items-center justify-center gap-1.5 h-10 rounded-xl border text-sm font-body transition-colors ${
                        insideOutside === "outside"
                          ? "border-gold/50 bg-gold-muted/20 text-foreground font-medium"
                          : "border-border bg-background text-muted-foreground hover:border-gold/40"
                      }`}
                    >
                      <Trees className="w-3.5 h-3.5" />
                      {t("advisor.context.insideoutside.outside")}
                    </button>
                  </div>
                </div>
              </div>

              {/* Row 2 — Postcode (always) + Floors (only when inside) */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-body font-semibold text-foreground flex items-center gap-1.5">
                    <MapPin className="w-3 h-3 text-gold" />
                    {t("advisor.context.postcode.label")}
                  </label>
                  <input
                    type="text"
                    inputMode="numeric"
                    maxLength={5}
                    value={postcode}
                    onChange={(e) => setPostcode(e.target.value.replace(/\D/g, ""))}
                    placeholder={t("advisor.context.postcode.placeholder")}
                    className={`h-10 w-full px-3 rounded-xl border text-sm font-body transition-colors ${
                      postcode
                        ? "border-gold/40 bg-gold-muted/10 text-foreground"
                        : "border-border bg-background text-muted-foreground"
                    } hover:border-gold/50 focus:outline-none focus:border-gold/50`}
                  />
                </div>

                {insideOutside === "inside" && (
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-body font-semibold text-foreground flex items-center gap-1.5">
                      <Layers className="w-3 h-3 text-gold" />
                      {t("advisor.context.floors.label")}
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={99}
                      value={floors}
                      onChange={(e) => setFloors(e.target.value)}
                      placeholder={t("advisor.context.floors.placeholder")}
                      className={`h-10 w-full px-3 rounded-xl border text-sm font-body transition-colors ${
                        floors && Number(floors) > 0
                          ? "border-gold/40 bg-gold-muted/10 text-foreground"
                          : "border-border bg-background text-muted-foreground"
                      } hover:border-gold/50 focus:outline-none focus:border-gold/50 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none`}
                    />
                  </div>
                )}
              </div>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto space-y-6 mb-6 min-h-0 max-h-[60vh] pr-1">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""} animate-fade-up`}>
                  {msg.role === "assistant" && (
                    <div className="w-9 h-9 rounded-xl bg-navy border border-gold/30 flex items-center justify-center shrink-0 mt-1">
                      <Scale className="w-4 h-4 text-gold" />
                    </div>
                  )}

                  <div className={`max-w-[85%] ${msg.role === "user" ? "max-w-[75%]" : ""}`}>
                    {msg.role === "user" ? (
                      <div className="bg-navy text-primary-foreground rounded-2xl rounded-tr-sm px-5 py-3 font-body text-sm leading-relaxed">
                        {msg.content}
                      </div>
                    ) : (
                      <>
                      {msg.classificationLabel && (
                        <div className="mb-1.5">
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-body font-medium bg-navy/10 text-navy border border-navy/20">
                            <Tag className="w-3 h-3" />
                            {msg.classificationLabel}
                          </span>
                        </div>
                      )}
                      <div className="bg-card border border-border rounded-2xl rounded-tl-sm p-5 shadow-sm">
                        <div className="font-body text-sm space-y-1">
                          {renderContent(msg.content)}
                        </div>

                        {msg.documentBlock && (
                          <DocumentCard
                            content={msg.documentBlock}
                            title={msg.documentBlock.includes("Stellungnahme") ? "Stellungnahme" : "Widerspruchsschreiben"}
                            copyLabel={t("advisor.copy")}
                            copiedLabel={t("advisor.copied")}
                            wordsLabel={t("advisor.words")}
                          />
                        )}

                        {msg.reliability && (
                          <div className="mt-4 pt-4 border-t border-border">
                            <ReliabilityBadge score={msg.reliability} label={msg.reliabilityLabel!} />
                          </div>
                        )}

                        {msg.sources && msg.sources.length > 0 && (
                          <div className="mt-4">
                            <div className="flex items-center gap-2 mb-3">
                              <BookOpen className="w-3.5 h-3.5 text-gold" />
                              <span className="text-xs font-body font-semibold text-foreground uppercase tracking-wide">
                                {t("advisor.sources")} ({msg.sources.length})
                              </span>
                            </div>
                            <div className="space-y-2">
                              {msg.sources.map((source, i) => (
                                <SourceCard key={i} source={source} index={i} />
                              ))}
                            </div>
                          </div>
                        )}

                        {msg.sources && (
                          <div className="mt-4 flex items-center gap-3">
                            <span className="text-xs text-muted-foreground font-body">{t("advisor.helpful")}</span>
                            <button className="p-1.5 rounded-lg hover:bg-muted transition-colors">
                              <ThumbsUp className="w-3.5 h-3.5 text-muted-foreground hover:text-foreground" />
                            </button>
                            <button className="p-1.5 rounded-lg hover:bg-muted transition-colors">
                              <ThumbsDown className="w-3.5 h-3.5 text-muted-foreground hover:text-foreground" />
                            </button>
                            <button className="p-1.5 rounded-lg hover:bg-muted transition-colors ml-auto">
                              <Copy className="w-3.5 h-3.5 text-muted-foreground hover:text-foreground" />
                            </button>
                          </div>
                        )}

                        {msg.awaitingClassification && (
                          <div className="mt-4 pt-4 border-t border-border">
                            <p className="text-xs font-body text-muted-foreground mb-2">{t("advisor.classify.pick")}</p>
                            <div className="flex flex-wrap gap-2">
                              {CLASSIFICATION_TILES.map((tile) => (
                                <button
                                  key={tile}
                                  type="button"
                                  onClick={() => setMessageClassification(msg.id, tile)}
                                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-navy/30 bg-navy/5 text-navy text-xs font-body font-medium hover:bg-navy/10 hover:border-navy/50 transition-colors"
                                >
                                  <Tag className="w-3 h-3" />
                                  {tile}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      </>
                    )}
                    <div className="text-xs text-muted-foreground font-body mt-1.5 px-1">
                      {msg.timestamp.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" })}
                    </div>
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex gap-4 animate-fade-in">
                  <div className="w-9 h-9 rounded-xl bg-navy border border-gold/30 flex items-center justify-center shrink-0 mt-1">
                    <Scale className="w-4 h-4 text-gold" />
                  </div>
                  <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-5 py-4 flex items-center gap-3">
                    <Loader2 className="w-4 h-4 text-gold animate-spin" />
                    <span className="text-sm text-muted-foreground font-body">{t("advisor.loading")}</span>
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className={`bg-card border rounded-2xl shadow-md p-3 transition-colors ${!contextReady ? "opacity-60 border-border" : "border-border"}`}>
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value.slice(0, 500))}
                onKeyDown={handleKeyDown}
                placeholder={contextReady ? t("advisor.placeholder") : t("advisor.context.sub")}
                rows={3}
                disabled={!contextReady}
                className="w-full bg-transparent font-body text-sm text-foreground placeholder:text-muted-foreground resize-none outline-none leading-relaxed disabled:cursor-not-allowed"
              />
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-border">
                <p className="text-xs text-muted-foreground font-body">
                  {t("advisor.hint")}
                </p>
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-body tabular-nums ${
                    input.length > 500 ? "text-red-500" :
                    input.length > 0 && input.trim().length < 10 ? "text-amber-500" :
                    "text-muted-foreground"
                  }`}>
                    {input.length}/500
                  </span>
                  <button
                    onClick={() => sendMessage()}
                    disabled={input.trim().length < 10 || loading || !contextReady}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-navy text-primary-foreground font-body text-sm font-medium disabled:opacity-40 hover:bg-navy-mid transition-colors disabled:cursor-not-allowed"
                  >
                    <Send className="w-3.5 h-3.5" />
                    {t("advisor.send")}
                  </button>
                </div>
              </div>
            </div>

            <p className="text-center text-xs text-muted-foreground font-body mt-3">
              {t("advisor.disclaimer")}
            </p>
          </TabsContent>

          {/* ── Tab 2: Cases ── */}
          <TabsContent value="vorgaenge" className="mt-0">
            <div className="border border-border rounded-2xl overflow-hidden bg-card shadow-sm">
              <div className="bg-muted border-b border-border px-4 py-3 flex items-center gap-2">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-400/60" />
                  <div className="w-3 h-3 rounded-full bg-amber-400/60" />
                  <div className="w-3 h-3 rounded-full bg-emerald-400/60" />
                </div>
                <div className="flex-1 mx-3">
                  <div className="bg-background rounded px-3 py-0.5 text-xs text-muted-foreground font-body text-center">
                    rechtimmobilien.de — {t("advisor.tab.cases")}
                  </div>
                </div>
              </div>

              <div className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-display text-lg font-semibold text-foreground">{t("advisor.caseDash")}</h2>
                  <span className="text-xs text-muted-foreground font-body bg-muted px-2.5 py-1 rounded-full">
                    {CASES.length} {t("advisor.cases")}
                  </span>
                </div>

                <div className="space-y-3">
                  {CASES.map((c) => (
                    <CaseCard
                      key={c.id}
                      case={c}
                      statusConfig={statusConfig}
                      stepsLabel={t("case.steps")}
                      deadlineLabel={t("case.deadline")}
                    />
                  ))}
                </div>

                <div className="mt-5 pt-4 border-t border-border">
                  <button
                    onClick={() => setActiveTab("berater")}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-navy text-primary-foreground font-body text-sm font-medium hover:bg-navy-mid transition-colors"
                  >
                    <FileSignature className="w-4 h-4" />
                    {t("advisor.newCase")}
                  </button>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AdvisorPage;
