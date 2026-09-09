export function formatCompactCount(n: number): string {
  if (Math.abs(n) >= 1000) {
    return `${(n / 1000).toFixed(1)}K`;
  }
  return Math.round(n).toLocaleString();
}


export function formatPercentFromFraction(fraction: number, digits = 1): string {
  return `${(fraction * 100).toFixed(digits)}%`;
}


export function formatPercentValue(pct: number, digits = 1): string {
  return `${pct.toFixed(digits)}%`;
}

export function formatNumber(n: number, digits = 1): string {
  return n.toFixed(digits).replace(/\.0$/, ".0"); 
}


export function formatBaselineDelta(observed: number, baseline: number, isPercentageMetric: boolean): string {
  if (baseline === 0) return "no baseline available";
  if (isPercentageMetric) {
    const pointsDelta = (observed - baseline) * 100;
    const sign = pointsDelta >= 0 ? "+" : "";
    return `${sign}${pointsDelta.toFixed(1)} percentage points`;
  }
  const pctDelta = ((observed - baseline) / baseline) * 100;
  const sign = pctDelta >= 0 ? "+" : "";
  return `${sign}${pctDelta.toFixed(0)}% above baseline`;
}


export function stripStructuredBlocks(text: string): string {
  return text
    .replace(/KEY_METRICS\s*:\s*\n(?:[ \t]*\w+\s*:\s*.+\n?)+/g, "")
    .replace(/NOTABLE_PATTERN\s*:.*$/m, "")
    .replace(/VERDICT\s*:\s*(SUPPORTED|CONTRADICTED|INCONCLUSIVE)\s*/gi, "")
    .trim();
}


export function firstSentence(text: string): string {
  const cleaned = text.trim();
  const match = cleaned.match(/^(.*?[.!?])(\s|$)/);
  const sentence = match ? match[1] : cleaned;
  return /[.!?]$/.test(sentence) ? sentence : `${sentence}.`;
}


export function roundLooseDecimalsInText(text: string): string {
  return text.replace(/\d+\.\d{3,}/g, (match) => parseFloat(match).toFixed(1));
}
