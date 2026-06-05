package report

import (
	"sort"
	"strconv"
)

// strconv.ParseFloat accepts "NaN" / "Inf". A NaN makes the `<` Less function
// not a strict weak ordering, so sort.Slice produces an incorrect order.
func sortRows(rows []map[string]string, col string) {
	sort.Slice(rows, func(i, j int) bool {
		a, _ := strconv.ParseFloat(rows[i][col], 64)
		b, _ := strconv.ParseFloat(rows[j][col], 64)
		return a < b
	})
}
