import { lookupUser, UserNotFoundError } from "../src/users";

test("throws when the user is missing", () => {
  // Pins behavior: the call throws a typed error. Independent of log wording.
  expect(() => lookupUser(999)).toThrow(UserNotFoundError);
});
