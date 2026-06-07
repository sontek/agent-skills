// account.ts
// Invariant: balance is never negative. The raw constructor is private; the only
// way to build an Account is through the validating factory, and balance is
// readonly so it can't be broken after construction.
export class Account {
  private constructor(public readonly balance: number) {}

  static create(initial: number): Account {
    if (initial < 0) throw new RangeError("balance must be non-negative");
    return new Account(initial);
  }
}
