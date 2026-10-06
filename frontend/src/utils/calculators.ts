export function eloWinProbability(ratingA: number, ratingB: number): number {
  return 1 / (1 + 10 ** ((ratingB - ratingA) / 400));
}

export function impliedProbFromAmerican(odds: number): number {
  if (odds < 0) return (-odds) / (-odds + 100);
  return 100 / (odds + 100);
}

export function toAmericanOdds(prob: number): number {
  const p = Math.max(0.01, Math.min(0.99, prob));
  if (p >= 0.5) return -Math.round((p / (1 - p)) * 100);
  return Math.round(((1 - p) / p) * 100);
}

export function toDecimalOdds(prob: number): number {
  const p = Math.max(0.01, Math.min(0.99, prob));
  return Math.round(1 / p * 100) / 100;
}

export function calculateEdge(modelProb: number, dkAmericanOdds: number) {
  let dkImplied: number;
  if (dkAmericanOdds < 0) {
    dkImplied = (-dkAmericanOdds) / (-dkAmericanOdds + 100);
  } else {
    dkImplied = 100 / (dkAmericanOdds + 100);
  }
  const edgePct = (modelProb - dkImplied) * 100;
  const payout = dkAmericanOdds >= 0
    ? dkAmericanOdds
    : 100 / (-dkAmericanOdds / 100);
  const ev = modelProb * payout - (1 - modelProb) * 100;
  let grade: string;
  if (edgePct >= 5) grade = "A";
  else if (edgePct >= 3) grade = "B";
  else if (edgePct >= 1.5) grade = "C";
  else grade = "D";
  return {
    model_prob: Math.round(modelProb * 10000) / 10000,
    dk_implied: Math.round(dkImplied * 10000) / 10000,
    edge_pct: Math.round(edgePct * 100) / 100,
    expected_value: Math.round(ev * 100) / 100,
    grade,
  };
}

function _poissonCdf(k: number, mu: number): number {
  if (k < 0) return 0;
  let p = Math.exp(-mu);
  let total = p;
  for (let i = 1; i <= k; i++) {
    p *= mu / i;
    total += p;
  }
  return Math.min(1, total);
}

export function prob180sOver(expected: number, line: number): number {
  return 1 - _poissonCdf(Math.floor(line), expected);
}

export function prob180sUnder(expected: number, line: number): number {
  return 1 - prob180sOver(expected, line);
}

export function expected180sInMatch(
  avgPerLeg: number,
  legsToWin: number,
  expectedLegs?: number
): number {
  const el = expectedLegs ?? legsToWin * 1.6;
  return avgPerLeg * el;
}

export function formatAdjustedProbability(
  baseProb: number,
  legsToWin: number,
  setsToWin?: number | null
): number {
  if (setsToWin) {
    const totalSets = setsToWin * 2 - 1;
    const signal = (baseProb - 0.5) * (1 + totalSets / 20);
    return Math.max(0.02, Math.min(0.98, 0.5 + signal));
  }
  const signal = (baseProb - 0.5) * (0.6 + legsToWin / 15);
  return Math.max(0.02, Math.min(0.98, 0.5 + signal));
}

export function parlay(legs: Array<{ prob: number; odds: number }>) {
  let combinedModelProb = 1;
  let combinedImpliedProb = 1;
  let combinedDecimal = 1;
  for (const leg of legs) {
    let dkImpl: number, decimal: number;
    if (leg.odds < 0) {
      dkImpl = (-leg.odds) / (-leg.odds + 100);
      decimal = 1 + 100 / (-leg.odds);
    } else {
      dkImpl = 100 / (leg.odds + 100);
      decimal = 1 + leg.odds / 100;
    }
    combinedModelProb *= leg.prob;
    combinedImpliedProb *= dkImpl;
    combinedDecimal *= decimal;
  }
  const edgePct = (combinedModelProb - combinedImpliedProb) * 100;
  const ev100 = combinedModelProb * ((combinedDecimal - 1) * 100) - (1 - combinedModelProb) * 100;
  return {
    combined_model_prob: Math.round(combinedModelProb * 10000) / 10000,
    combined_implied_prob: Math.round(combinedImpliedProb * 10000) / 10000,
    combined_decimal_odds: Math.round(combinedDecimal * 10000) / 10000,
    edge_pct: Math.round(edgePct * 100) / 100,
    ev_per_100: Math.round(ev100 * 100) / 100,
  };
}
