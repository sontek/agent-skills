# sourceproviders/github.py
def list_open_prs(self, repo):
    # GitHub paginates at 100; we request the max page size to keep the round
    # trips down on busy repos, then let the client follow Link headers.
    return self._client.paginate(f"/repos/{repo}/pulls?state=open&per_page=100")
