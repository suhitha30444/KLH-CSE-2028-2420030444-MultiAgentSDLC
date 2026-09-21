# Traceability Report — run `f79ef7ff`

**Final status:** failed

**Retries spent:** spec_approval=0/3, test_review=5/5
*(5 Coder/Tester/Reviewer attempt(s) were rejected before this final one — see the criteria below for the ACCEPTED attempt only; earlier attempts' specific failures aren't retained by this report, only their count.)*

**Requirement:** Write a ShoppingCart class with add_item(name, price, qty), remove_item(name), apply_percentage_discount(percent), and get_total(). Adding an item that already exists should increase its quantity rather than duplicate it. Removing an item that doesn't exist should raise a KeyError. The discount should only apply to the current total, not stack across multiple calls. get_total() should return 0 for an empty cart.

Each section below follows ONE acceptance criterion end to end: the task(s) meant to satisfy it, the code that resulted, the real test executed against it, and the Reviewer's verdict.

## AC1: add_item adds a new item with the specified name, price, and quantity.

**Task(s):**
- `T2` — Implement add_item(name, price, qty) to add new items and increase quantity for existing items.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED

## AC2: Adding an item with a name that already exists increases its quantity instead of creating a duplicate entry.

**Task(s):**
- `T2` — Implement add_item(name, price, qty) to add new items and increase quantity for existing items.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED

## AC3: remove_item successfully removes an existing item from the cart.

**Task(s):**
- `T3` — Implement remove_item(name) to delete items and raise KeyError if the item is not present.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED

## AC4: remove_item raises a KeyError when attempting to remove an item that does not exist.

**Task(s):**
- `T3` — Implement remove_item(name) to delete items and raise KeyError if the item is not present.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED

## AC5: apply_percentage_discount applies the given percentage discount to the current total.

**Task(s):**
- `T4` — Implement apply_percentage_discount(percent) to set a discount based on the current total without stacking across calls.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED

## AC6: The discount does not stack across multiple calls; each call calculates discount based on the undiscounted total.

**Task(s):**
- `T4` — Implement apply_percentage_discount(percent) to set a discount based on the current total without stacking across calls.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **FAIL** — FAILED (real sandboxed execution): Traceback (most recent call last):
  File "C:\Users\Hamsini\AppData\Local\Temp\sdlc_sandbox_2vv_nsty\test_AC6.py", line 5, in <module>
    assert cart.get_total()==3.0*0.8
           ^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError

**Review verdict:**
- **REJECTED** — FAILED assertion in test

## AC7: get_total returns the correct total price after discounts, and returns 0 for an empty cart.

**Task(s):**
- `T5` — Implement get_total() to compute the total price after applying the discount, returning 0 for an empty cart.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED

