# apps/api/views.py
from ninja import Router, Schema

router = Router()


class RepoOut(Schema):
    id: int
    name: str


class JobOut(Schema):
    id: int
    status: str


class CoverageOut(Schema):
    pct: float


@router.get("/repos", response=list[RepoOut])
def list_repos(request):
    return Repo.objects.for_user(request.user)


@router.get("/repos/{repo_id}/jobs", response=list[JobOut])
def list_jobs(request, repo_id: int):
    return Job.objects.filter(repo_id=repo_id)


@router.get("/repos/{repo_id}/coverage", response=CoverageOut)
def repo_coverage(request, repo_id: int):
    return CoverageQueryService(repo_id).summary()


# ...60 more endpoints + their request/response schemas, all on this one router
