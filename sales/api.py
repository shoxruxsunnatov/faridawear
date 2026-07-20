import json

from django.views import View
from django.http import JsonResponse
from django.db.models import Prefetch, F
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction

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

        sales = (
            Sale.objects.filter(
                organization=req.user.organization
            )
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
                    )
                )
            )
            .order_by("-date_created")
        )
        data = [
            {
                "id": sale.id,
                "author": (
                    sale.author.get_full_name()
                    if sale.author else None
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
            for sale in sales
        ]

        return JsonResponse(
            data,
            safe=False
        )

