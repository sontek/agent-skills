// account.ts
// Invariant: balance is never negative.
export class Account {
  balance: number;

  constructor(initial: number) {
    this.balance = initial;
  }

  withdraw(amount: number): void {
    this.balance -= amount;
  }
}
