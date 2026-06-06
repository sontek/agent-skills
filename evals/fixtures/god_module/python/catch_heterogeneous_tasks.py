# sourceproviders/tasks.py
from celery import shared_task


@shared_task
def sync_github_pull_requests(repo_id: int) -> None:
    provider = GitHubProvider(repo_id)
    provider.sync_open_pulls()


@shared_task
def reconcile_stripe_subscription(org_id: int) -> None:
    sub = stripe.Subscription.retrieve(Org.objects.get(id=org_id).stripe_id)
    Org.objects.filter(id=org_id).update(plan=sub["items"]["data"][0]["price"]["id"])


@shared_task
def send_welcome_email(user_id: int) -> None:
    user = User.objects.get(id=user_id)
    mailer.send(to=user.email, template="welcome", ctx={"name": user.first_name})


@shared_task
def export_audit_csv(org_id: int) -> None:
    rows = AuditLog.objects.filter(org_id=org_id).values_list("actor", "action", "ts")
    storage.save(f"audit/{org_id}.csv", _to_csv(rows))
