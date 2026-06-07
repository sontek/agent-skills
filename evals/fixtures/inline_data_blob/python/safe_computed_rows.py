# coverages/views.py
# The rows here are COMPUTED from the queryset argument, not a static literal.
# The function holds logic (aggregation), not embedded content — nothing to move
# to a template or data file.
def coverage_rows(request, commit_sha: str):
    files = CoverageFile.objects.filter(commit__sha=commit_sha).order_by("path")
    rows = []
    for f in files:
        covered = f.covered_lines
        total = f.total_lines or 1
        rows.append(
            {
                "path": f.path,
                "covered": covered,
                "total": total,
                "pct": round(100 * covered / total, 1),
            }
        )
    return render(request, "coverages/grid.html", {"rows": rows})
