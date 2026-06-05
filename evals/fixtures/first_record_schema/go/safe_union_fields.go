package table

// Column set is the union of keys across all records, so later-only fields
// survive.
func toTable(records []map[string]any) ([]string, []map[string]any) {
	seen := map[string]bool{}
	var columns []string
	for _, r := range records {
		for k := range r {
			if !seen[k] {
				seen[k] = true
				columns = append(columns, k)
			}
		}
	}
	return columns, project(records, columns)
}
