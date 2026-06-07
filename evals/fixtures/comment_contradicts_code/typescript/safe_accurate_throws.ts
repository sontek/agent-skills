// users.ts
/**
 * Look up a user by id.
 * @returns the user; throws NotFoundError if no user exists for `id`.
 */
async function getUser(id: string): Promise<User> {
  const row = await db.users.find(id);
  if (!row) throw new NotFoundError(`user ${id}`);
  return toUser(row);
}
