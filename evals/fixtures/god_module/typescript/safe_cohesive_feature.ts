// billing/subscription.ts
export async function createSubscription(orgId: string, plan: string) { /* ... */ }
export async function changePlan(orgId: string, plan: string) { /* ... */ }
export async function cancelSubscription(orgId: string) { /* ... */ }
export async function resumeSubscription(orgId: string) { /* ... */ }
export async function previewProration(orgId: string, plan: string) { /* ... */ }
export async function applyCoupon(orgId: string, code: string) { /* ... */ }
export function isPastDue(sub: Subscription): boolean { return false; }
export function nextRenewal(sub: Subscription): Date { return new Date(0); }
