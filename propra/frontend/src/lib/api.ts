/**
 * API client for the Propra backend.
 *
 * Both functions are mocked for now. Replace the mock blocks with real fetch
 * calls once the backend is running. The request and response types are
 * intentionally kept in sync with the backend Pydantic schemas in
 * propra/schemas/.
 */

const BASE_URL = "http://localhost:8000";

// ---------------------------------------------------------------------------
// Shared types
// ---------------------------------------------------------------------------

export type PropertyType =
  | "einfamilienhaus"
  | "mehrfamilienhaus"
  | "gewerbe"
  | "gemischte"
  | "sonderbau";

export type AreaType = "inside" | "outside";

/** The property context collected by the intake form. */
export interface PropertyContext {
  bundesland: string;
  propertyType: PropertyType;
  insideOutside: AreaType;
  postcode: string;
  /** Only required when insideOutside is "inside". */
  floors?: number;
}

// ---------------------------------------------------------------------------
// submitIntake
// ---------------------------------------------------------------------------

export interface IntakeResponse {
  /** Confirmation shown to the user after the form is submitted. */
  userMessage: string;
}

export async function submitIntake(
  context: PropertyContext
): Promise<IntakeResponse> {
  // TODO: replace with real fetch
  // return fetch(`${BASE_URL}/api/intake`, {
  //   method: "POST",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify({
  //     bundesland: context.bundesland,
  //     property_type: context.propertyType,
  //     inside_outside: context.insideOutside,
  //     postcode: context.postcode,
  //     floors: context.floors,
  //   }),
  // }).then((r) => r.json());

  void context; // suppress unused-variable warning until real fetch is in place
  return {
    userMessage:
      "Property details saved. You can now ask your legal question below.",
  };
}

// ---------------------------------------------------------------------------
// submitAssess
// ---------------------------------------------------------------------------

export interface CitedSource {
  paragraph: string;
  regulationName: string;
  jurisdiction: string;
  excerpt: string;
}

export type ConfidenceLevel = "LOW" | "MEDIUM" | "HIGH";

export interface AssessResponse {
  /** Main answer shown in the chat bubble. */
  explanation: string;
  /** Legal sources cited in the answer. */
  sources: CitedSource[];
  confidence: ConfidenceLevel;
  /** German-language summary for the user. */
  userMessage: string;
}

export interface AssessRequest extends PropertyContext {
  question: string;
}

export async function submitAssess(
  request: AssessRequest
): Promise<AssessResponse> {
  // TODO: replace with real fetch
  // return fetch(`${BASE_URL}/api/assess`, {
  //   method: "POST",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify({
  //     bundesland: request.bundesland,
  //     property_type: request.propertyType,
  //     inside_outside: request.insideOutside,
  //     postcode: request.postcode,
  //     floors: request.floors,
  //     question: request.question,
  //   }),
  // }).then((r) => r.json());

  void BASE_URL; // suppress unused-variable warning until real fetch is in place
  void request;
  return {
    explanation:
      "Dies ist eine Platzhaltantwort. Die KI-Anbindung ist noch nicht aktiv.",
    sources: [],
    confidence: "LOW",
    userMessage:
      "Die Analyse ist noch nicht verfügbar. Bitte versuchen Sie es später erneut.",
  };
}
