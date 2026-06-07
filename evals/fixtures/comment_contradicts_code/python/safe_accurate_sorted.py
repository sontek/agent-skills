# reporting/views.py
def recent_authors(commits):
    """Return the distinct author names, sorted alphabetically."""
    return sorted({c.author for c in commits})
