# Traceability Report — run `8c411b81`

**Final status:** failed

**Retries spent:** spec_approval=0/3, test_review=3/3
*(3 Coder/Tester/Reviewer attempt(s) were rejected before this final one — see the criteria below for the ACCEPTED attempt only; earlier attempts' specific failures aren't retained by this report, only their count.)*

**Requirement:** Write a ShoppingCart class with add_item(name, price, qty), remove_item(name), apply_percentage_discount(percent), and get_total(). Adding an item that already exists should increase its quantity rather than duplicate it. Removing an item that doesn't exist should raise a KeyError. The discount should only apply to the current total, not stack across multiple calls. get_total() should return 0 for an empty cart.

Each section below follows ONE acceptance criterion end to end: the task(s) meant to satisfy it, the code that resulted, the real test executed against it, and the Reviewer's verdict.

## AC1: add_item stores a new item with the given name, price, and quantity.

**Task(s):**
- `T2` — Implement add_item to add new items and increase quantity for existing items.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- (none — this criterion was never reached by the Tester)

**Review verdict:**
- (none — this criterion was never reached by the Reviewer)

## AC2: add_item with a name that already exists increases the existing item's quantity by the provided qty instead of creating a duplicate entry.

**Task(s):**
- `T2` — Implement add_item to add new items and increase quantity for existing items.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- (none — this criterion was never reached by the Tester)

**Review verdict:**
- (none — this criterion was never reached by the Reviewer)

## AC3: remove_item deletes the item with the specified name from the cart.

**Task(s):**
- `T3` — Implement remove_item to delete items and raise KeyError for missing items.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- (none — this criterion was never reached by the Tester)

**Review verdict:**
- (none — this criterion was never reached by the Reviewer)

## AC4: remove_item raises a KeyError when the specified name is not present in the cart.

**Task(s):**
- `T3` — Implement remove_item to delete items and raise KeyError for missing items.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- (none — this criterion was never reached by the Tester)

**Review verdict:**
- (none — this criterion was never reached by the Reviewer)

## AC5: apply_percentage_discount reduces the cart's total by the given percentage and does not compound with any previously applied discounts.

**Task(s):**
- `T4` — Implement apply_percentage_discount so that it applies a single discount to the current total without stacking.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- (none — this criterion was never reached by the Tester)

**Review verdict:**
- (none — this criterion was never reached by the Reviewer)

## AC6: get_total returns the sum of (price * quantity) for all items, reflecting any applied discount.

**Task(s):**
- `T5` — Implement get_total to compute the total price, apply any discount, and return 0 for an empty cart.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- (none — this criterion was never reached by the Tester)

**Review verdict:**
- (none — this criterion was never reached by the Reviewer)

## AC7: get_total returns 0 when the cart contains no items.

**Task(s):**
- `T5` — Implement get_total to compute the total price, apply any discount, and return 0 for an empty cart.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- (none — this criterion was never reached by the Tester)

**Review verdict:**
- (none — this criterion was never reached by the Reviewer)

