package report

import (
	"cmp"
	"slices"
)

// cmp.Compare defines a total order over float64 (NaN sorts before everything),
// so the sort is well-defined even if a value is NaN. Not a finding.
func sortRows(rows []float64) {
	slices.SortFunc(rows, func(a, b float64) int { return cmp.Compare(a, b) })
}
