// Three sibling chart-body renderers for the same ChartSpec, deliberately spread
// apart (a PieChartBody sits between the bar and line bodies) so the divergence
// isn't trivially adjacent. BarChartBody honors spec.stacked; LineChartBody
// hardcodes stacked:false, so a backend-requested stacked line chart silently
// renders unstacked. The blank cell in the parity table is the bug.
type Series = { id: string; points: number[] };
type ChartSpec = { stacked?: boolean; series: Series[] };

export function BarChartBody({ spec }: { spec: ChartSpec }) {
  return renderBars(spec.series, {
    groupMode: spec.stacked ? "stacked" : "grouped",
  });
}

export function PieChartBody({ spec }: { spec: ChartSpec }) {
  // pie has no stacking concept; unrelated distractor between the two siblings
  return renderPie(spec.series.map((s) => ({ id: s.id, value: sum(s.points) })));
}

export function LineChartBody({ spec }: { spec: ChartSpec }) {
  return renderLines(spec.series, {
    yScale: { type: "linear", stacked: false }, // ignores spec.stacked
  });
}
