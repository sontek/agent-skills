# sourceproviders/management/commands/sync_repos.py
from django.core.management.base import BaseCommand


# $ rg -l '\bCommand\b' -g '!**/tests/**'
# sourceproviders/management/commands/sync_repos.py
# (no other production module references this class by name)
class Command(BaseCommand):
    help = "Sync all repositories from the source provider."

    def handle(self, *args, **options):
        for repo in Repo.objects.all():
            GitHubProvider(repo.id).sync()


# sourceproviders/tests/test_sync_repos.py
def test_sync_repos_runs():
    call_command("sync_repos")
