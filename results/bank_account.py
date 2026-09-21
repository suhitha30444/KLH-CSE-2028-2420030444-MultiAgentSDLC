class BankAccount:
    def __init__(self):
        self._balance = 0

    def get_balance(self):
        return self._balance

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self._balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self._balance:
            raise ValueError("Insufficient funds")
        self._balance -= amount

    def transfer(self, other_account, amount):
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        if amount > self._balance:
            raise ValueError("Insufficient funds for transfer")
        # Perform atomic transfer
        self._balance -= amount
        other_account._balance += amount
