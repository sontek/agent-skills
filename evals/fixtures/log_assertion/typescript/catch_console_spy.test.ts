import { lookupUser } from "../src/users";

test("logs a warning when the user is missing", () => {
  const spy = jest.spyOn(console, "warn").mockImplementation(() => {});

  lookupUser(999);

  // Asserts on the logged message text via a console spy — pins the wording,
  // not the behavior. Same anti-pattern as caplog.text, different sink.
  expect(spy).toHaveBeenCalledWith("user not found: 999");
});
