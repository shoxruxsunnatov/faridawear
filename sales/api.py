import json
from datetime import datetime, time, date

from django.views import View
from django.http import JsonResponse
from django.db.models import Prefetch, F, Q, Sum
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date

from account.security import (
    CSRFExempt,
)

from products.models import (
    Product
)
from sales.models import (
    Sale,
    SaleItem,
    Payment
)

from sales.utils import (
    to_int,
    make_payment
)


class SalesListViewAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, *args, **kwargs):

        data = {
            "message": "failed",
            "errors": [],
        }

        try:
            sale_data = json.loads(req.body)
            sale_data["cart"]
            sale_data["total"] = to_int(sale_data["total"])
            sale_data["card_payment"] = to_int(sale_data["card_payment"])
            sale_data["cash_payment"] = to_int(sale_data["cash_payment"])
        except Exception as e:
            data["errors"].append("corrupt-data")

            return JsonResponse(data, safe=False)
        
        
        for product in sale_data.get("cart"):
            if not Product.objects.filter(
                id=product["id"],
                organization=req.user.organization
            ).exists():
                
                data["errors"].append("product-not-found")
                data["title"] = f'({product["serial"]}) {product["title"]}'
            
                break

        total_payment = sale_data.get("card_payment") + sale_data.get("cash_payment")
        if sale_data.get("total") > total_payment or sale_data.get("total") <= 0:
            data["errors"].append("funds")
        
        if req.user.role not in ("sales", "admin", "supervisor"):
            data["errors"].append("permission")
            

        if not data["errors"]:
            with transaction.atomic():
                sale = Sale(
                    author=req.user,
                    organization=req.user.organization,
                    sale_total=sale_data.get("total"),
                    base_total=0,
                    paid=0,
                    debt=sale_data.get("total"),
                    profit=0
                )
                sale.save()
                
                for product in sale_data.get("cart"):

                    db_product = Product.objects.select_for_update().get(
                        id=product["id"],
                        organization=req.user.organization
                    )
                    sale.base_total += db_product.base_price * product["quantity"]

                    if db_product.stock >= product["quantity"]:
                        sale_item = SaleItem(
                            sale=sale,
                            organization=req.user.organization,
                            product=db_product,
                            quantity=product["quantity"],
                            sale_price=product["sale_price"]
                        )
                        sale_item.save()

                        Product.objects.filter(
                            id=product["id"]
                        ).update(
                            stock=F("stock") - product["quantity"]
                        )
                    else:
                        data["errors"].append("product-stock")
                        data["title"] = f'({product["serial"]}) {product["title"]}'
                        

                        transaction.set_rollback(True)
                        return JsonResponse(data, safe=False)
                
                sale.save(update_fields=["base_total"])
                
                try:
                    if sale_data.get("card_payment"):
                        make_payment(
                            sale=sale,
                            amount=sale_data.get("card_payment"),
                            method="card",
                            author=req.user
                        )
                    
                    if sale_data.get("cash_payment"):
                        make_payment(
                            sale=sale,
                            amount=sale_data.get("cash_payment"),
                            method="cash",
                            author=req.user
                        )
                    
                    data.update(
                        {
                            "message": "success",

                        }
                    )

                except ValueError:
                    transaction.set_rollback(True)
                    data["errors"].append("payment-amount")
                
        return JsonResponse(data, safe=False)


    def get(self, req, *args, **kwargs):

        page = req.GET.get("page", "1")
        per = req.GET.get("per", 30)

        start_date = parse_date(req.GET.get("start", ""))
        end_date = parse_date(req.GET.get("end", ""))

        if (
            not start_date
            or not end_date
            or start_date > end_date
        ):
            today = date.today()
            
            start_date = today
            end_date = today

        start_datetime = timezone.make_aware(
            datetime.combine(start_date, time.min)
        )

        end_datetime = timezone.make_aware(
            datetime.combine(end_date, time.max)
        )

        sales_queryset = Sale.objects.filter(
            organization=req.user.organization,
            date_created__gte=start_datetime,
            date_created__lte=end_datetime,
        )

        # Statistics
        sale_statistics = sales_queryset.aggregate(
            total=Sum("sale_total"),
        )

        payment_statistics = Payment.objects.filter(
            sale__organization=req.user.organization,
            sale__date_created__gte=start_datetime,
            sale__date_created__lte=end_datetime,
        ).aggregate(
            cash=Sum(
                "amount",
                filter=Q(method="cash"),
            ),
            card=Sum(
                "amount",
                filter=Q(method="card"),
            ),
        )

        sales = (
            sales_queryset
            .only(
                "id",
                "author",
                "sale_total",
                "debt",
                "date_created"
            )
            .prefetch_related(
                Prefetch(
                    "payments",
                    queryset=Payment.objects.only(
                        "id",
                        "amount",
                        "method",
                        "sale_id",
                        "author__first_name",
                        "author__last_name",
                    )
                )
            )
            .order_by("-date_created")
        )

        try:
            paginator = Paginator(sales, int(per))
        except:
            paginator = Paginator(sales, 30)

        page_obj = paginator.get_page(page)

        data = [
            {
                "id": sale.id,
                "author": (
                    sale.author.get_full_name()
                    if sale.author else "O'chirilgan hisob"
                ),
                "sale_total": sale.sale_total,
                "debt": sale.debt,
                "date_created": sale.date_created,

                "payments": [
                    {
                        "id": payment.id,
                        "amount": payment.amount,
                        "method": payment.method,
                    }
                    for payment in sale.payments.all()
                ]
            }
            for sale in page_obj
        ]

        return JsonResponse(
            {
                "data": data,

                "total": sale_statistics["total"] or 0,
                "cash": payment_statistics["cash"] or 0,
                "card": payment_statistics["card"] or 0,

                "page": page_obj.number,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
            },
            safe=False
        )

