from datetime import timedelta

from django.utils import timezone

from main.models import Group
from payment.models import Transaction


def charge_group_tuition(group: Group) -> None:

    users = group.students.filter(is_paid=True, payment_due__lte=timezone.now())

    for user in users:
        if user.tuition_cost and user.tuition_cost <= user.balance:

            user.balance -= user.tuition_cost
            user.payment_due += timedelta(days=30)
            
            transaction = Transaction(
                user=user,
                amount=-user.tuition_cost,
                category="charge-tuition",
                group=user.group,
                organization=user.organization,
            )
            transaction.save()

        else:

            user.is_paid = False
            print("Henloooooooooooooooooooooooooooooooo")
            
        user.save()

    print(users.count())
