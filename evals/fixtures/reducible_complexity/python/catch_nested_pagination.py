# sourceproviders/providers/github.py
def list_pull_requests(self, repo, since):
    results = []
    for page in self._paginate(f"/repos/{repo}/pulls"):
        for pr in page:
            if pr["state"] == "open":
                if pr.get("user"):
                    if pr.get("created_at"):
                        if _parse(pr["created_at"]) >= since:
                            results.append(
                                {
                                    "number": pr["number"],
                                    "title": pr["title"],
                                    "author": pr["user"]["login"],
                                }
                            )
    return results
