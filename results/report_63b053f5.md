# Traceability Report — run `63b053f5`

**Final status:** done

**Retries spent:** spec_approval=0/3, test_review=0/5

**Requirement:** Write a ShoppingCart class with add_item(name, price, qty), remove_item(name), apply_percentage_discount(percent), and get_total(). Adding an item that already exists should increase its quantity rather than duplicate it. Removing an item that doesn't exist should raise a KeyError. The discount should only apply to the current total, not stack across multiple calls. get_total() should return 0 for an empty cart.

Each section below follows ONE acceptance criterion end to end: the task(s) meant to satisfy it, the code that resulted, the real test executed against it, and the Reviewer's verdict.

## AC1: Adding an item stores the item with the given name, price, and quantity.

**Task(s):**
- `T2` — Implement add_item method to add new items and increase quantity for existing items.

**Code:**
*(no code artifact's task_id matched this criterion's task(s) exactly — showing every file the Coder produced this run, since the test result below confirms which one actually satisfies it)*

`shopping_cart.py`:
```python
class ShoppingCart:
    def __init__(self):
        self.items = {}
        self.discount = 0.0
    def add_item(self, name, price, qty):
        if name in self.items:
            self.items[name]['qty'] += qty
        else:
            self.items[name] = {'price': price, 'qty': qty}
    def remove_item(self, name):
        if name not in self.items:
            raise KeyError(f"Item '{name}' not found in cart")
        del self.items[name]
    def apply_percentage_discount(self, percent):
        if percent < 0 or percent > 100:
            raise ValueError("Percent must be between 0 and 100")
        self.discount = percent / 100.0
    def get_total(self):
        if not self.items:
            return 0.0
        subtotal = sum(details['price'] * details['qty'] for details in self.items.values())
        total = subtotal * (1 - self.discount)
        return total

```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED test confirms item added correctly.

## AC2: Adding an item that already exists increases its quantity rather than creating a duplicate entry.

**Task(s):**
- `T2` — Implement add_item method to add new items and increase quantity for existing items.

**Code:**
*(no code artifact's task_id matched this criterion's task(s) exactly — showing every file the Coder produced this run, since the test result below confirms which one actually satisfies it)*

`shopping_cart.py`:
```python
class ShoppingCart:
    def __init__(self):
        self.items = {}
        self.discount = 0.0
    def add_item(self, name, price, qty):
        if name in self.items:
            self.items[name]['qty'] += qty
        else:
            self.items[name] = {'price': price, 'qty': qty}
    def remove_item(self, name):
        if name not in self.items:
            raise KeyError(f"Item '{name}' not found in cart")
        del self.items[name]
    def apply_percentage_discount(self, percent):
        if percent < 0 or percent > 100:
            raise ValueError("Percent must be between 0 and 100")
        self.discount = percent / 100.0
    def get_total(self):
        if not self.items:
            return 0.0
        subtotal = sum(details['price'] * details['qty'] for details in self.items.values())
        total = subtotal * (1 - self.discount)
        return total

```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED test confirms quantity increment on duplicate add.

## AC3: remove_item successfully removes an existing item from the cart.

**Task(s):**
- `T3` — Implement remove_item method to delete items and raise KeyError if the item is missing.

**Code:**
*(no code artifact's task_id matched this criterion's task(s) exactly — showing every file the Coder produced this run, since the test result below confirms which one actually satisfies it)*

`shopping_cart.py`:
```python
class ShoppingCart:
    def __init__(self):
        self.items = {}
        self.discount = 0.0
    def add_item(self, name, price, qty):
        if name in self.items:
            self.items[name]['qty'] += qty
        else:
            self.items[name] = {'price': price, 'qty': qty}
    def remove_item(self, name):
        if name not in self.items:
            raise KeyError(f"Item '{name}' not found in cart")
        del self.items[name]
    def apply_percentage_discount(self, percent):
        if percent < 0 or percent > 100:
            raise ValueError("Percent must be between 0 and 100")
        self.discount = percent / 100.0
    def get_total(self):
        if not self.items:
            return 0.0
        subtotal = sum(details['price'] * details['qty'] for details in self.items.values())
        total = subtotal * (1 - self.discount)
        return total

```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED test confirms item removal works.

## AC4: remove_item raises a KeyError when attempting to remove an item that does not exist.

**Task(s):**
- `T3` — Implement remove_item method to delete items and raise KeyError if the item is missing.

**Code:**
*(no code artifact's task_id matched this criterion's task(s) exactly — showing every file the Coder produced this run, since the test result below confirms which one actually satisfies it)*

`shopping_cart.py`:
```python
class ShoppingCart:
    def __init__(self):
        self.items = {}
        self.discount = 0.0
    def add_item(self, name, price, qty):
        if name in self.items:
            self.items[name]['qty'] += qty
        else:
            self.items[name] = {'price': price, 'qty': qty}
    def remove_item(self, name):
        if name not in self.items:
            raise KeyError(f"Item '{name}' not found in cart")
        del self.items[name]
    def apply_percentage_discount(self, percent):
        if percent < 0 or percent > 100:
            raise ValueError("Percent must be between 0 and 100")
        self.discount = percent / 100.0
    def get_total(self):
        if not self.items:
            return 0.0
        subtotal = sum(details['price'] * details['qty'] for details in self.items.values())
        total = subtotal * (1 - self.discount)
        return total

```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED test confirms KeyError on removing non-existent item.

## AC5: apply_percentage_discount applies a discount to the current total based on the given percent.

**Task(s):**
- `T4` — Implement apply_percentage_discount method to apply a discount to the current total without stacking across calls.

**Code:**
*(no code artifact's task_id matched this criterion's task(s) exactly — showing every file the Coder produced this run, since the test result below confirms which one actually satisfies it)*

`shopping_cart.py`:
```python
class ShoppingCart:
    def __init__(self):
        self.items = {}
        self.discount = 0.0
    def add_item(self, name, price, qty):
        if name in self.items:
            self.items[name]['qty'] += qty
        else:
            self.items[name] = {'price': price, 'qty': qty}
    def remove_item(self, name):
        if name not in self.items:
            raise KeyError(f"Item '{name}' not found in cart")
        del self.items[name]
    def apply_percentage_discount(self, percent):
        if percent < 0 or percent > 100:
            raise ValueError("Percent must be between 0 and 100")
        self.discount = percent / 100.0
    def get_total(self):
        if not self.items:
            return 0.0
        subtotal = sum(details['price'] * details['qty'] for details in self.items.values())
        total = subtotal * (1 - self.discount)
        return total

```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED test confirms percentage discount applied correctly.

## AC6: Multiple calls to apply_percentage_discount do not stack; each call applies discount to the original total, not cumulatively.

**Task(s):**
- `T4` — Implement apply_percentage_discount method to apply a discount to the current total without stacking across calls.

**Code:**
*(no code artifact's task_id matched this criterion's task(s) exactly — showing every file the Coder produced this run, since the test result below confirms which one actually satisfies it)*

`shopping_cart.py`:
```python
class ShoppingCart:
    def __init__(self):
        self.items = {}
        self.discount = 0.0
    def add_item(self, name, price, qty):
        if name in self.items:
            self.items[name]['qty'] += qty
        else:
            self.items[name] = {'price': price, 'qty': qty}
    def remove_item(self, name):
        if name not in self.items:
            raise KeyError(f"Item '{name}' not found in cart")
        del self.items[name]
    def apply_percentage_discount(self, percent):
        if percent < 0 or percent > 100:
            raise ValueError("Percent must be between 0 and 100")
        self.discount = percent / 100.0
    def get_total(self):
        if not self.items:
            return 0.0
        subtotal = sum(details['price'] * details['qty'] for details in self.items.values())
        total = subtotal * (1 - self.discount)
        return total

```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED test confirms discounts do not stack cumulatively.

## AC7: get_total returns the correct total price after items are added, removed, and discounts applied.

**Task(s):**
- `T5` — Implement get_total method to compute total after discounts and return 0 for an empty cart.

**Code:**
*(no code artifact's task_id matched this criterion's task(s) exactly — showing every file the Coder produced this run, since the test result below confirms which one actually satisfies it)*

`shopping_cart.py`:
```python
class ShoppingCart:
    def __init__(self):
        self.items = {}
        self.discount = 0.0
    def add_item(self, name, price, qty):
        if name in self.items:
            self.items[name]['qty'] += qty
        else:
            self.items[name] = {'price': price, 'qty': qty}
    def remove_item(self, name):
        if name not in self.items:
            raise KeyError(f"Item '{name}' not found in cart")
        del self.items[name]
    def apply_percentage_discount(self, percent):
        if percent < 0 or percent > 100:
            raise ValueError("Percent must be between 0 and 100")
        self.discount = percent / 100.0
    def get_total(self):
        if not self.items:
            return 0.0
        subtotal = sum(details['price'] * details['qty'] for details in self.items.values())
        total = subtotal * (1 - self.discount)
        return total

```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED test confirms total calculation after operations.

## AC8: get_total returns 0 for an empty cart.

**Task(s):**
- `T5` — Implement get_total method to compute total after discounts and return 0 for an empty cart.

**Code:**
*(no code artifact's task_id matched this criterion's task(s) exactly — showing every file the Coder produced this run, since the test result below confirms which one actually satisfies it)*

`shopping_cart.py`:
```python
class ShoppingCart:
    def __init__(self):
        self.items = {}
        self.discount = 0.0
    def add_item(self, name, price, qty):
        if name in self.items:
            self.items[name]['qty'] += qty
        else:
            self.items[name] = {'price': price, 'qty': qty}
    def remove_item(self, name):
        if name not in self.items:
            raise KeyError(f"Item '{name}' not found in cart")
        del self.items[name]
    def apply_percentage_discount(self, percent):
        if percent < 0 or percent > 100:
            raise ValueError("Percent must be between 0 and 100")
        self.discount = percent / 100.0
    def get_total(self):
        if not self.items:
            return 0.0
        subtotal = sum(details['price'] * details['qty'] for details in self.items.values())
        total = subtotal * (1 - self.discount)
        return total

```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — PASSED test confirms total is 0 for empty cart.

