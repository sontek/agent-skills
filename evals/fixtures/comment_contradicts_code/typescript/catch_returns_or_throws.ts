// users.ts
/**
 * Look up a user by id.
 * @returns the user; throws NotFoundError if no user exists for `id`.
 */
async function getUser(id: string): Promise<User | null> {
  const row = await db.users.find(id);
  if (!row) return null;
  return toUser(row);
}
