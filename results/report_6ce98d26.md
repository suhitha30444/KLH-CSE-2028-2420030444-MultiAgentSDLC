# Traceability Report — run `6ce98d26`

**Final status:** done

**Retries spent:** spec_approval=0/3, test_review=3/5
*(3 Coder/Tester/Reviewer attempt(s) were rejected before this final one — see the criteria below for the ACCEPTED attempt only; earlier attempts' specific failures aren't retained by this report, only their count.)*

**Requirement:** Write a ShoppingCart class with add_item(name, price, qty), remove_item(name), apply_percentage_discount(percent), and get_total(). Adding an item that already exists should increase its quantity rather than duplicate it. Removing an item that doesn't exist should raise a KeyError. The discount should only apply to the current total, not stack across multiple calls. get_total() should return 0 for an empty cart.

Each section below follows ONE acceptance criterion end to end: the task(s) meant to satisfy it, the code that resulted, the real test executed against it, and the Reviewer's verdict.

## AC1: add_item stores a new item with the specified name, price, and quantity

**Task(s):**
- `T2` — Implement add_item to add new items and increase quantity for existing items

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED test confirms add_item stores a new item with correct name, price, and quantity.

## AC2: add_item increments the quantity of an existing item instead of creating a duplicate

**Task(s):**
- `T2` — Implement add_item to add new items and increase quantity for existing items

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED test confirms add_item increments quantity of an existing item instead of duplicating.

## AC3: remove_item deletes an existing item and raises KeyError when the item name is not in the cart

**Task(s):**
- `T3` — Implement remove_item to delete items and raise KeyError if item not found

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED test confirms remove_item deletes an existing item and raises KeyError when the item is absent.

## AC4: apply_percentage_discount reduces the current total by the given percent and does not compound when called multiple times

**Task(s):**
- `T4` — Implement apply_percentage_discount to apply a one-time discount to the current total

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED test confirms apply_percentage_discount reduces total by the given percent and does not compound on multiple calls.

## AC5: get_total returns the sum of price*quantity for all items minus any applied discount, and returns 0 when the cart is empty

**Task(s):**
- `T5` — Implement get_total to compute total after discount and return 0 for empty cart

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED test confirms get_total returns sum of price*quantity minus discounts and returns 0 for an empty cart.

