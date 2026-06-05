package table

// Columns taken from the first map only; later maps with extra keys lose those
// fields in the projected rows.
func toTable(records []map[string]any) ([]string, []map[string]any) {
	var columns []string
	for k := range records[0] {
		columns = append(columns, k)
	}
	return columns, project(records, columns)
}
