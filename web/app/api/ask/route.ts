// POST /api/ask - proxy between the browser and the RAG API on Azure.
// Runs on the server only: RAG_API_KEY never reaches the browser.
import { checkRateLimit } from "@/lib/rateLimit";
import type { AskResponse, ErrorResponse } from "@/lib/types";

// Same limits as AskRequest in api.py
const MIN_LENGTH = 3;
const MAX_LENGTH = 500;

// Cold start of the Container App (~20 s) + Mistral answer: leave some margin
const TIMEOUT_MS = 60_000;

const UNAVAILABLE = "Le service est momentanément indisponible. Réessayez dans un instant.";

function error(message: string, status: number, headers?: HeadersInit) {
  return Response.json({ error: message } satisfies ErrorResponse, { status, headers });
}

// The Container Apps ingress adds the real address at the end of the list.
// The addresses before it come from the client, which can invent them.
function visitorIp(request: Request) {
  const forwarded = request.headers.get("x-forwarded-for") ?? "";
  return forwarded.split(",").at(-1)?.trim() || "unknown";
}

function formatWait(seconds: number) {
  const minutes = Math.ceil(seconds / 60);
  if (minutes < 120) return minutes === 1 ? "1 minute" : `${minutes} minutes`;
  return `${Math.ceil(minutes / 60)} heures`;
}

export async function POST(request: Request) {
  const apiUrl = process.env.RAG_API_URL;
  const apiKey = process.env.RAG_API_KEY;
  if (!apiUrl || !apiKey) {
    console.error("RAG_API_URL or RAG_API_KEY is missing");
    return error(UNAVAILABLE, 500);
  }

  // request.json() throws if the body is not valid JSON
  const body: unknown = await request.json().catch(() => null);
  const question =
    typeof body === "object" && body !== null && "question" in body
      ? String(body.question).trim()
      : "";
  if (question.length < MIN_LENGTH || question.length > MAX_LENGTH) {
    return error(`La question doit contenir entre ${MIN_LENGTH} et ${MAX_LENGTH} caractères.`, 400);
  }

  // After the checks above: an invalid question costs nothing, so it does not count
  const retryAfter = checkRateLimit(visitorIp(request), {
    perMinute: Number(process.env.RATE_LIMIT_PER_MINUTE) || 5,
    perDay: Number(process.env.RATE_LIMIT_PER_DAY) || 20,
  });
  if (retryAfter !== null) {
    return error(
      `Vous avez posé beaucoup de questions. Réessayez dans ${formatWait(retryAfter)}.`,
      429,
      { "Retry-After": String(retryAfter) },
    );
  }

  let res: Response;
  try {
    res = await fetch(`${apiUrl}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
      body: JSON.stringify({ question }),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch {
    console.error("The RAG API did not answer in time");
    return error(UNAVAILABLE, 504);
  }

  if (res.status === 429) {
    return error("Le site a atteint sa limite de questions pour aujourd'hui. Revenez demain.", 429);
  }
  if (res.status === 503) {
    return error("Le service a atteint sa limite d'utilisation. Réessayez plus tard.", 503);
  }
  if (!res.ok) {
    // 401 = wrong key, 422 = question rejected by FastAPI
    console.error(`The RAG API answered with status ${res.status}`);
    return error(UNAVAILABLE, 502);
  }

  const data = (await res.json()) as AskResponse;
  return Response.json(data);
}
