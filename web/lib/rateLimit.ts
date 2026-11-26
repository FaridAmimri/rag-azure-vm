// Per-visitor limit on questions, to preserve the Mistral budget.
// Counters live in memory: they reset when the Container App scales to zero
// or restarts. That is enough with a single replica (--max-replicas 1).

const MINUTE_MS = 60_000;
const DAY_MS = 24 * 60 * MINUTE_MS;

// A script changing IP on every request must not fill the memory
const MAX_VISITORS = 10_000;

type Limits = { perMinute: number; perDay: number };

type Visitor = {
  minuteEnd: number;
  minuteCount: number;
  dayEnd: number;
  dayCount: number;
};

const visitors = new Map<string, Visitor>();

function removeOldVisitors(now: number) {
  for (const [ip, visitor] of visitors) {
    if (visitor.dayEnd <= now) visitors.delete(ip);
  }
  // Still full: forget everyone rather than crash, Mistral's cap is still there
  if (visitors.size >= MAX_VISITORS) visitors.clear();
}

// Counts one question. Returns null if it is allowed,
// otherwise the number of seconds to wait before the next one.
export function checkRateLimit(
  ip: string,
  limits: Limits,
  now = Date.now(),
): number | null {
  let visitor = visitors.get(ip);
  if (!visitor) {
    if (visitors.size >= MAX_VISITORS) removeOldVisitors(now);
    visitor = { minuteEnd: 0, minuteCount: 0, dayEnd: 0, dayCount: 0 };
    visitors.set(ip, visitor);
  }

  if (visitor.dayEnd <= now) {
    visitor.dayEnd = now + DAY_MS;
    visitor.dayCount = 0;
  }
  if (visitor.minuteEnd <= now) {
    visitor.minuteEnd = now + MINUTE_MS;
    visitor.minuteCount = 0;
  }

  // The day limit comes first: its wait is the longest
  if (visitor.dayCount >= limits.perDay) {
    return Math.ceil((visitor.dayEnd - now) / 1000);
  }
  if (visitor.minuteCount >= limits.perMinute) {
    return Math.ceil((visitor.minuteEnd - now) / 1000);
  }

  visitor.dayCount += 1;
  visitor.minuteCount += 1;
  return null;
}

// Only for the tests
export function resetRateLimit() {
  visitors.clear();
}
