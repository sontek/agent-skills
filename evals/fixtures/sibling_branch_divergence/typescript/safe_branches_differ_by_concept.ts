// FP guard: two sibling chart-body renderers that legitimately differ. A bar chart
// has a stacking concept; a scatter chart does not — it has point sizing instead.
// Each branch reads the spec field that applies to it. No dropped shared field, so
// this must stay CLEAN (the validation gate's "field must be applicable to the
// omitting branch" exemption). A naive "branches differ => flag" rule fails here.
type Series = { id: string; points: number[] };
type ChartSpec = { stacked?: boolean; pointSize?: number; series: Series[] };

export function BarChartBody({ spec }: { spec: ChartSpec }) {
  return renderBars(spec.series, {
    groupMode: spec.stacked ? "stacked" : "grouped",
  });
}

export function ScatterChartBody({ spec }: { spec: ChartSpec }) {
  // scatter has no stacking dimension; nodeSize is its own concept.
  return renderScatter(spec.series, { nodeSize: spec.pointSize ?? 6 });
}
