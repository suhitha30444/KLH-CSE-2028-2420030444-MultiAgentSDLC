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
