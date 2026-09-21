# Traceability Report — run `9eeb8577`

**Final status:** failed

**Retries spent:** spec_approval=0/3, test_review=5/5
*(5 Coder/Tester/Reviewer attempt(s) were rejected before this final one — see the criteria below for the ACCEPTED attempt only; earlier attempts' specific failures aren't retained by this report, only their count.)*

**Requirement:** Write a ShoppingCart class with add_item(name, price, qty), remove_item(name), apply_percentage_discount(percent), and get_total(). Adding an item that already exists should increase its quantity rather than duplicate it. Removing an item that doesn't exist should raise a KeyError. The discount should only apply to the current total, not stack across multiple calls. get_total() should return 0 for an empty cart.

Each section below follows ONE acceptance criterion end to end: the task(s) meant to satisfy it, the code that resulted, the real test executed against it, and the Reviewer's verdict.

## AC1: Adding a new item stores it with the given name, price, and quantity.

**Task(s):**
- `T2` — Implement add_item method to add new items and increase quantity for existing items.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- (none — this criterion was never reached by the Tester)

**Review verdict:**
- (none — this criterion was never reached by the Reviewer)

## AC2: Adding an item with a name that already exists increases its quantity rather than creating a duplicate entry.

**Task(s):**
- `T2` — Implement add_item method to add new items and increase quantity for existing items.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- (none — this criterion was never reached by the Tester)

**Review verdict:**
- (none — this criterion was never reached by the Reviewer)

## AC3: Removing an existing item removes it from the cart.

**Task(s):**
- `T3` — Implement remove_item method that removes an item or raises KeyError if not present.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- (none — this criterion was never reached by the Tester)

**Review verdict:**
- (none — this criterion was never reached by the Reviewer)

## AC4: Removing an item that does not exist raises a KeyError.

**Task(s):**
- `T3` — Implement remove_item method that removes an item or raises KeyError if not present.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- (none — this criterion was never reached by the Tester)

**Review verdict:**
- (none — this criterion was never reached by the Reviewer)

## AC5: Applying a percentage discount reduces the total by the given percent and does not stack across multiple discount calls.

**Task(s):**
- `T4` — Implement apply_percentage_discount method that applies a discount to the current total without stacking across calls.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- (none — this criterion was never reached by the Tester)

**Review verdict:**
- (none — this criterion was never reached by the Reviewer)

## AC6: get_total returns the correct total reflecting added items, removed items, and applied discounts.

**Task(s):**
- `T5` — Implement get_total method that calculates total with discount, returns correct value and 0 for an empty cart.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- (none — this criterion was never reached by the Tester)

**Review verdict:**
- (none — this criterion was never reached by the Reviewer)

## AC7: get_total returns 0 for an empty cart.

**Task(s):**
- `T5` — Implement get_total method that calculates total with discount, returns correct value and 0 for an empty cart.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- (none — this criterion was never reached by the Tester)

**Review verdict:**
- (none — this criterion was never reached by the Reviewer)

