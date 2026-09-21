# Traceability Report — run `1ba37606`

**Final status:** failed

**Requirement:** Write a ShoppingCart class with add_item(name, price, qty), remove_item(name), apply_percentage_discount(percent), and get_total(). Adding an item that already exists should increase its quantity rather than duplicate it. Removing an item that doesn't exist should raise a KeyError. The discount should only apply to the current total, not stack across multiple calls. get_total() should return 0 for an empty cart.

Each section below follows ONE acceptance criterion end to end: the task(s) meant to satisfy it, the code that resulted, the real test executed against it, and the Reviewer's verdict.

## AC1: The ShoppingCart class provides methods add_item(name, price, qty), remove_item(name), apply_percentage_discount(percent), and get_total().

**Task(s):**
- `T6` — Verify that the ShoppingCart class includes all required methods as specified.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **FAIL** — FAILED (real sandboxed execution): Traceback (most recent call last):
  File "C:\Users\Hamsini\AppData\Local\Temp\sdlc_sandbox_2a84xle9\test_AC1.py", line 1, in <module>
    from shopping_cart import ShoppingCart
  File "C:\Users\Hamsini\AppData\Local\Temp\sdlc_sandbox_2a84xle9\shopping_cart.py", line 1
    class ShoppingCart:\n    def __init__(self):\n        self.items = {}  # name: (price, qty)\n        self.discount = 0.0  # percent discount as decimal\n\n    def add_item(self, name, price, qty):\n        if name in self.items:\n            existing_price, existing_qty = self.items[name]\n            if existing_price != price:\n                # If price changes, keep existing price.\n                pass\n            self.items[name] = (existing_price, existing_qty + qty)\n        else:\n            self.items[name] =

**Review verdict:**
- **REJECTED** — Import failed due to syntax error; class definition incomplete, so methods are not available.

## AC2: add_item adds a new item to the cart; if an item with the same name already exists, its quantity is increased by the given qty instead of creating a duplicate entry.

**Task(s):**
- `T2` — Implement add_item method to add new items or increase quantity for existing items.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **FAIL** — FAILED (real sandboxed execution): Traceback (most recent call last):
  File "C:\Users\Hamsini\AppData\Local\Temp\sdlc_sandbox_vkb931q0\test_AC2.py", line 1, in <module>
    from shopping_cart import ShoppingCart
  File "C:\Users\Hamsini\AppData\Local\Temp\sdlc_sandbox_vkb931q0\shopping_cart.py", line 1
    class ShoppingCart:\n    def __init__(self):\n        self.items = {}  # name: (price, qty)\n        self.discount = 0.0  # percent discount as decimal\n\n    def add_item(self, name, price, qty):\n        if name in self.items:\n            existing_price, existing_qty = self.items[name]\n            if existing_price != price:\n                # If price changes, keep existing price.\n                pass\n            self.items[name] = (existing_price, existing_qty + qty)\n        else:\n            self.items[name] =

**Review verdict:**
- **REJECTED** — Import failed due to syntax error; add_item behavior cannot be verified.

## AC3: remove_item raises a KeyError when attempting to remove an item that does not exist in the cart.

**Task(s):**
- `T3` — Implement remove_item method with KeyError raised for nonexistent items.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **FAIL** — FAILED (real sandboxed execution): Traceback (most recent call last):
  File "C:\Users\Hamsini\AppData\Local\Temp\sdlc_sandbox_vdp3n6a5\test_AC3.py", line 1, in <module>
    from shopping_cart import ShoppingCart
  File "C:\Users\Hamsini\AppData\Local\Temp\sdlc_sandbox_vdp3n6a5\shopping_cart.py", line 1
    class ShoppingCart:\n    def __init__(self):\n        self.items = {}  # name: (price, qty)\n        self.discount = 0.0  # percent discount as decimal\n\n    def add_item(self, name, price, qty):\n        if name in self.items:\n            existing_price, existing_qty = self.items[name]\n            if existing_price != price:\n                # If price changes, keep existing price.\n                pass\n            self.items[name] = (existing_price, existing_qty + qty)\n        else:\n            self.items[name] =

**Review verdict:**
- **REJECTED** — Import failed due to syntax error; remove_item implementation not reachable.

## AC4: apply_percentage_discount applies a discount to the current total without stacking; multiple calls do not compound discounts.

**Task(s):**
- `T4` — Implement apply_percentage_discount method ensuring discount applies only to the current total and does not stack across calls.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **FAIL** — FAILED (real sandboxed execution): Traceback (most recent call last):
  File "C:\Users\Hamsini\AppData\Local\Temp\sdlc_sandbox_lqekrew2\test_AC4.py", line 1, in <module>
    from shopping_cart import ShoppingCart
  File "C:\Users\Hamsini\AppData\Local\Temp\sdlc_sandbox_lqekrew2\shopping_cart.py", line 1
    class ShoppingCart:\n    def __init__(self):\n        self.items = {}  # name: (price, qty)\n        self.discount = 0.0  # percent discount as decimal\n\n    def add_item(self, name, price, qty):\n        if name in self.items:\n            existing_price, existing_qty = self.items[name]\n            if existing_price != price:\n                # If price changes, keep existing price.\n                pass\n            self.items[name] = (existing_price, existing_qty + qty)\n        else:\n            self.items[name] =

**Review verdict:**
- **REJECTED** — Import failed due to syntax error; apply_percentage_discount cannot be executed.

## AC5: get_total returns 0 for an empty cart and otherwise returns the total cost of items after applying the most recent discount.

**Task(s):**
- `T5` — Implement get_total method to compute total cost, apply latest discount, and return 0 for an empty cart.

**Code:**
- (none — no code artifact was linked to this criterion's task(s))

**Test result:**
- **FAIL** — FAILED (real sandboxed execution): Traceback (most recent call last):
  File "C:\Users\Hamsini\AppData\Local\Temp\sdlc_sandbox__pwdsn0e\test_AC5.py", line 1, in <module>
    from shopping_cart import ShoppingCart
  File "C:\Users\Hamsini\AppData\Local\Temp\sdlc_sandbox__pwdsn0e\shopping_cart.py", line 1
    class ShoppingCart:\n    def __init__(self):\n        self.items = {}  # name: (price, qty)\n        self.discount = 0.0  # percent discount as decimal\n\n    def add_item(self, name, price, qty):\n        if name in self.items:\n            existing_price, existing_qty = self.items[name]\n            if existing_price != price:\n                # If price changes, keep existing price.\n                pass\n            self.items[name] = (existing_price, existing_qty + qty)\n        else:\n            self.items[name] =

**Review verdict:**
- **REJECTED** — Import failed due to syntax error; get_total cannot be tested.

