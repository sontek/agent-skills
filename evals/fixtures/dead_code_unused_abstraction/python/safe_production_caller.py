# services/slug.py
# Slugify is exercised by its unit test below, but it is ALSO called from
# production code: create_repo() in views/repos.py calls slugify(name) on every
# repo create. The test is not its only reference.
import re


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


# views/repos.py (production caller):
def create_repo(request):
    name = request.POST["name"]
    repo = Repo.objects.create(name=name, slug=slugify(name))
    return redirect(repo)


def test_slugify_collapses_separators():
    assert slugify("My Cool Repo!") == "my-cool-repo"
