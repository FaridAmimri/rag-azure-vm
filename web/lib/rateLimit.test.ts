// Run with: npm test (Node's built-in test runner, no extra dependency)
import assert from "node:assert/strict";
import { beforeEach, test } from "node:test";
import { checkRateLimit, resetRateLimit } from "./rateLimit.ts";

const LIMITS = { perMinute: 2, perDay: 3 };
const MINUTE_MS = 60_000;
const DAY_MS = 24 * 60 * MINUTE_MS;

beforeEach(resetRateLimit);

test("allows questions up to the minute limit, then gives the wait", () => {
  assert.equal(checkRateLimit("a", LIMITS, 0), null);
  assert.equal(checkRateLimit("a", LIMITS, 0), null);
  assert.equal(checkRateLimit("a", LIMITS, 15_000), 45);
});

test("the minute limit resets after one minute", () => {
  checkRateLimit("a", LIMITS, 0);
  checkRateLimit("a", LIMITS, 0);
  assert.equal(checkRateLimit("a", LIMITS, MINUTE_MS), null);
});

test("the day limit holds after the minute resets, and resets after one day", () => {
  checkRateLimit("a", LIMITS, 0);
  checkRateLimit("a", LIMITS, 0);
  checkRateLimit("a", LIMITS, MINUTE_MS);
  assert.equal(checkRateLimit("a", LIMITS, 2 * MINUTE_MS), (DAY_MS - 2 * MINUTE_MS) / 1000);
  assert.equal(checkRateLimit("a", LIMITS, DAY_MS), null);
});

test("a refused question does not extend the wait", () => {
  checkRateLimit("a", LIMITS, 0);
  checkRateLimit("a", LIMITS, 0);
  checkRateLimit("a", LIMITS, 1_000);
  assert.equal(checkRateLimit("a", LIMITS, MINUTE_MS), null);
});

test("each visitor has their own counters", () => {
  checkRateLimit("a", LIMITS, 0);
  checkRateLimit("a", LIMITS, 0);
  assert.notEqual(checkRateLimit("a", LIMITS, 0), null);
  assert.equal(checkRateLimit("b", LIMITS, 0), null);
});

test("memory stays bounded when many IPs show up", () => {
  for (let i = 0; i < 10_001; i++) checkRateLimit(`ip${i}`, LIMITS, 0);
  // ip0 was forgotten when the table was full: it starts again from zero
  assert.equal(checkRateLimit("ip0", LIMITS, 0), null);
  assert.equal(checkRateLimit("ip0", LIMITS, 0), null);
  assert.notEqual(checkRateLimit("ip0", LIMITS, 0), null);
});
