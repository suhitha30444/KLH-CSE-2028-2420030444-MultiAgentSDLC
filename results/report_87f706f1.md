# Traceability Report — run `87f706f1`

**Final status:** done

**Requirement:** Write a function is_prime(n) that returns True if n is a prime number and False otherwise. Handle n less than 2 correctly.

Each section below follows ONE acceptance criterion end to end: the task(s) meant to satisfy it, the code that resulted, the real test executed against it, and the Reviewer's verdict.

## AC1: For any integer n less than 2, is_prime returns False.

**Task(s):**
- `T1` — Add a check that returns False when n is less than 2.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED — is_prime returns False for integers n<2

## AC2: For prime numbers (e.g., 2,3,5,7,11), is_prime returns True.

**Task(s):**
- `T2` — Implement a trial-division algorithm up to sqrt(n) to determine primality, returning True for primes and False for composites.

**Code:**
`prime.py`:
```python
def is_prime(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True
```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED — is_prime returns True for prime numbers (2,3,5,7,11)

## AC3: For composite numbers greater than or equal to 2 (e.g., 4,6,9,15), is_prime returns False.

**Task(s):**
- `T2` — Implement a trial-division algorithm up to sqrt(n) to determine primality, returning True for primes and False for composites.

**Code:**
`prime.py`:
```python
def is_prime(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True
```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED — is_prime returns False for composite numbers (4,6,9,15)

