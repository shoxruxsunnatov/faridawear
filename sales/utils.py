from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Sum

from sales.models import (
    Sale,
    Payment
)

def to_int(value, default=0):
    try:
        return int(str(value).replace(" ", ""))
    except (ValueError, TypeError):
        return default


@transaction.atomic
def make_payment(
    *,
    sale: Sale,
    amount,
    method,
    author=None,
):
    amount = Decimal(amount)

    if amount <= 0:
        raise ValueError(
            "Payment amount must be greater than 0."
        )

    if amount > sale.debt:
        raise ValueError(
            "Payment amount exceeds remaining debt."
        )

    total_profit = (
        sale.sale_total -
        sale.base_total
    )

    total_paid_before = (
        sale.payments.aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    total_profit_before = (
        sale.payments.aggregate(
            total=Sum("profit")
        )["total"]
        or Decimal("0.00")
    )

    total_paid_after = (
        total_paid_before +
        amount
    )

    total_profit_after = (
        total_profit *
        total_paid_after /
        sale.sale_total
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    profit_amount = (
        total_profit_after -
        total_profit_before
    )

    payment = Payment.objects.create(
        author=author,
        organization=sale.organization,
        sale=sale,
        amount=amount,
        profit=profit_amount,
        method=method,
    )

    sale.paid += amount
    sale.debt = (
        sale.sale_total -
        sale.paid
    )
    sale.profit = total_profit_before + profit_amount

    sale.save(
        update_fields=[
            "paid",
            "debt",
            "profit",
        ]
    )

    return payment
