// POST /api/ask - proxy between the browser and the RAG API on Azure.
// Runs on the server only: RAG_API_KEY never reaches the browser.
import type { AskResponse, ErrorResponse } from "@/lib/types";

// Same limits as AskRequest in api.py
const MIN_LENGTH = 3;
const MAX_LENGTH = 500;

// Cold start of the Container App (~20 s) + Mistral answer: leave some margin
const TIMEOUT_MS = 60_000;

function error(message: string, status: number) {
  return Response.json({ error: message } satisfies ErrorResponse, { status });
}

export async function POST(request: Request) {
  const apiUrl = process.env.RAG_API_URL;
  const apiKey = process.env.RAG_API_KEY;
  if (!apiUrl || !apiKey) {
    return error("RAG_API_URL or RAG_API_KEY is missing in .env.local", 500);
  }

  // request.json() throws if the body is not valid JSON
  const body: unknown = await request.json().catch(() => null);
  const question =
    typeof body === "object" && body !== null && "question" in body
      ? String(body.question).trim()
      : "";
  if (question.length < MIN_LENGTH || question.length > MAX_LENGTH) {
    return error(`The question must be ${MIN_LENGTH} to ${MAX_LENGTH} characters long`, 400);
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
    return error("The RAG API did not answer in time", 504);
  }

  if (!res.ok) {
    // 401 = wrong key in .env.local, 422 = question rejected by FastAPI
    return error(`The RAG API answered with status ${res.status}`, 502);
  }

  const data = (await res.json()) as AskResponse;
  return Response.json(data);
}
