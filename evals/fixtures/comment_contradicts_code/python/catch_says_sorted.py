# reporting/views.py
def recent_authors(commits):
    """Return the distinct author names, sorted alphabetically."""
    seen = []
    for c in commits:
        if c.author not in seen:
            seen.append(c.author)
    return seen
