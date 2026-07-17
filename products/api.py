from django.views import View
from django.http import JsonResponse
from django.db.models import Q, CharField
from django.db.models.functions import Cast
from django.core.paginator import Paginator

from account.security import (
    CSRFExempt,
    AdminRoleRequired
)

from products.models import (
    Product
)


class ProductsListViewAPI(CSRFExempt, AdminRoleRequired, View):

    def post(self, req, *args, **kwargs):

        data = {
            "message": "failed",
            "errors": [],
        }

        title = req.POST.get("title", "").strip()
        sale_price = req.POST.get("sale_price", "").replace(" ", "")
        base_price = req.POST.get("base_price", "").replace(" ", "")
        stock = req.POST.get("stock", "").strip()
        serial = req.POST.get("serial", "").strip()
        image = req.FILES.get('image')
        

        if len(title) > 100:
            data["errors"].append("title")
        
        try:
            sale_price = int(sale_price)
        except:
            data["errors"].append("sale_price")
        
        try:
            base_price = int(base_price)
        except:
            data["errors"].append("base_price")
        
        try:
            stock = int(stock)
        except:
            data["errors"].append("stock")
        
        try:
            serial = int(serial)
        except:
            data["errors"].append("serial")
        
        if image:
            if image.name.split('.')[-1].lower() not in ['png', 'jpg', 'jfif']:
                data["errors"].append("image")

        if Product.objects.filter(organization=req.user.organization, serial=serial).exists():
            data["errors"].append("serial-exists")
        
        if req.user.role not in ("admin", "supervisor"):
            data["errors"].append("permission")
            

        if not data["errors"]:

            if sale_price < 0 or base_price < 0 or stock < 0 or serial < 0:
                data["errors"].append("negative-value")

                return JsonResponse(data, safe=False)

            product = Product(
                author=req.user,
                organization=req.user.organization,
                title=title,
                image=image,
                description="",
                base_price=base_price,
                sale_price=sale_price,
                stock=stock,
                serial=serial
            )
            product.save()
            
            data.update(
                {
                    "message": "success",
                    "title": product.title,
                    "serial": product.serial
                }
            )
        
        return JsonResponse(data, safe=False)


    def get(self, req, *args, **kwargs):

        query = req.GET.get("search", "").strip().lower()
        page = req.GET.get("page", "1")
        per = req.GET.get("per", 30)

        if query:
            data = Product.objects.annotate(
                serial_str=Cast("serial", CharField())
            ).filter(
                Q(serial_str__icontains=query) | Q(title__icontains=query),
                organization=req.user.organization
            ).order_by("serial")
        else:
            data = Product.objects.filter(
                organization=req.user.organization
            ).order_by("serial")

        try:
            paginator = Paginator(data, int(per))
        except:
            paginator = Paginator(data, 30)

        page_obj = paginator.get_page(page)

        data = [
            {
                "id": product.id,
                "serial": product.serial,
                "title": product.title,
                "image": product.image.url if product.image else None,
                "base_price": product.base_price,
                "sale_price": product.sale_price,
                "stock": product.stock,
                "date_created": product.date_created
            }
            for product in page_obj
        ]
        

        return JsonResponse(
            {
                "data": data,
                "page": page_obj.number,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
            },
            safe=False
        )
