from decimal import Decimal

def get_monthly_budget_increment(budget_info: dict) -> Decimal:
    increment = budget_info['increment']
    if budget_info['frequency'] == 'Y':
        increment = (increment / Decimal('12.00')).quantize(Decimal('1.00'))
    elif budget_info['frequency'] == 'D':
        increment = ((increment * Decimal('365.0')) / Decimal('12.0')).quantize(Decimal('1.00'))
    elif budget_info['frequency'] == 'W':
        increment = ((increment * Decimal('52.0')) / Decimal('12.0')).quantize(Decimal('1.00'))
    return increment