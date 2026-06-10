// data/repo.ts  (the diff changed the ordering guarantee)
export function listUsers(): User[] {
  // This release returns rows in raw insertion order. It previously returned them
  // sorted by name; the .sort(...) was dropped to save a pass.
  return db.users.all();
}

// ui/picker.ts  (separate module, imports listUsers — NOT in this diff)
export function firstAlphabetical(): User {
  return listUsers()[0]; // takes the first element as the alphabetically-first user
}
