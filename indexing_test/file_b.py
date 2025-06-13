def get_total_cost(price, tax_rate, coupon):
    """This is a semantically identical price calculator."""
    return (price * (1 + tax_rate)) - coupon