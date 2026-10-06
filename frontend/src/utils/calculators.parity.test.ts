import assert from "node:assert/strict";
import { calculateEdge, eloWinProbability, expected180sInMatch, formatAdjustedProbability, impliedProbFromAmerican, parlay, prob180sOver, toAmericanOdds } from "./calculators";

assert.equal(toAmericanOdds(0.5), -100);
assert.equal(toAmericanOdds(0.4), 150);
assert.equal(toAmericanOdds(0.6), -150);
assert.equal(impliedProbFromAmerican(-120), 120 / 220);
assert.equal(impliedProbFromAmerican(150), 100 / 250);
assert.equal(eloWinProbability(1500, 1500), 0.5);
assert.deepEqual(calculateEdge(0.6, -120), { model_prob: 0.6, dk_implied: 0.5455, edge_pct: 5.45, expected_value: 10, grade: "A" });
assert.ok(Math.abs(expected180sInMatch(.1, 6) - .96) < 1e-12);
assert.ok(Math.abs(prob180sOver(1, .5) - (1 - Math.exp(-1))) < 1e-12);
assert.equal(formatAdjustedProbability(.65, 6), .65);
assert.deepEqual(parlay([{ prob: .6, odds: -120 }, { prob: .55, odds: 110 }]), { combined_model_prob: .33, combined_implied_prob: .2597, combined_decimal_odds: 3.85, edge_pct: 7.03, ev_per_100: 27.05 });
console.log("Calculator parity fixtures passed.");
