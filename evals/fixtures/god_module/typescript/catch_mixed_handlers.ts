// handlers.ts
export async function handleGithubWebhook(req: Request): Promise<void> {
  const event = parseSignature(req);
  await syncPullRequests(event.repoId);
}

export async function reconcileSubscription(orgId: string): Promise<void> {
  const sub = await stripe.subscriptions.retrieve(orgs.get(orgId).stripeId);
  await orgs.update(orgId, { plan: sub.items.data[0].price.id });
}

export async function sendWelcomeEmail(userId: string): Promise<void> {
  const user = await users.get(userId);
  await mailer.send({ to: user.email, template: "welcome", ctx: { name: user.firstName } });
}

export async function exportAuditCsv(orgId: string): Promise<void> {
  const rows = await auditLog.forOrg(orgId);
  await storage.save(`audit/${orgId}.csv`, toCsv(rows));
}
