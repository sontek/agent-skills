# sourceproviders/permissions.py
def resolve_repository(request):
    if request.GET.get("slug"):
        repo = lookup_by_slug(request.GET["slug"])
    elif request.GET.get("legacy_id"):
        repo = lookup_by_legacy_id(request.GET["legacy_id"])
    elif request.GET.get("external_ref"):
        repo = lookup_by_external_ref(request.GET["external_ref"])
    elif request.GET.get("full_name"):
        repo = lookup_by_full_name(request.GET["full_name"])
    elif request.GET.get("node_id"):
        repo = lookup_by_node_id(request.GET["node_id"])
    elif request.session.get("last_repo_id"):
        repo = lookup_by_id(request.session["last_repo_id"])
    elif request.user.default_repo_id:
        repo = lookup_by_id(request.user.default_repo_id)
    else:
        repo = None
    return repo
