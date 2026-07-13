from django.views import View
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, CharField
from django.db.models.functions import Cast

from account.security import (
    CSRFExempt,
    AdminRoleRequired
)

from products.models import (
    Product
)


class ProductsListViewAPI(CSRFExempt, AdminRoleRequired, View):

    def post(self, req, pk, *args, **kwargs):

        data = {
            "message": "failed",
            "errors": [],
        }

        text = req.POST.get("text", "").strip().replace('’', "'")
        text =  re.sub(r'\s+', ' ', text)
        translation = req.POST.get("translation", "").strip()
        description = req.POST.get("description", "").strip()
        category = req.POST.get("category", "").strip()
        image = req.FILES.get('image')
        auto_generate = req.POST.get("auto_generate")
        

        if not 1 < len(text) < 200:
            data["errors"].append("text-translation")
        else:
            text = nlp(text)[0].lemma_.lower()
        
        if auto_generate != "on":
            if not 1 < len(translation) < 200:
                data["errors"].append("text-translation")

            if not len(description) < 300:
                data["errors"].append("description")
            
            if category not in ("other", "noun", "adjective", "verb"):
                data["errors"].append("category")

        if not (req.user.has_perm("account.edit_dictionary") or req.user.role == "supervisor"):
            data["errors"].append("permission")

        if vp.vocabularies.count() >= 50:
            data["errors"].append("capacity")
        
        existing = Vocabulary.objects.filter(text=text.lower(), created_by="supervisor", organization=req.user.organization).first()
        if existing:
            data["existing"] = {
                "id": existing.id,
                "text": existing.text,
                "translation": existing.translation,
                "description": existing.description,
                "package": existing.package.title,
                "author": existing.author.get_full_name() if existing.author else None,
                "date_created": existing.date_created
            }
            data["errors"].append("existing")

        if image:
            if image.name.split('.')[-1].lower() not in ['png', 'jpg', 'jfif']:
                data["errors"].append("image")
        # else:
        #     data["errors"].append("image")

        if not data["errors"]:

            spelling_check = check_text(text)
            if not spelling_check:
                
                if auto_generate == "on":
                    sys_vocabulary = Vocabulary.objects.filter(text=text, created_by="system").first()
                    if sys_vocabulary:
                        vocabulary = Vocabulary(
                            author=req.user,
                            parent=sys_vocabulary,
                            package=vp,
                            text=sys_vocabulary.text,
                            translation=sys_vocabulary.translation,
                            description=sys_vocabulary.description,
                            category=sys_vocabulary.category,
                            created_by="supervisor",
                            organization=req.user.organization
                        )
                    else:

                        response = get_full_vocabulary(text)
                        if not response:
                            return JsonResponse(data, safe=False)
                        
                        sys_vocabulary = Vocabulary(
                            text=text,
                            translation=response[0].strip(),
                            description=response[2].strip(),
                            category=response[1].strip(),
                            created_by="system",
                            organization=req.user.organization
                        )
                        sys_vocabulary.save()

                        vocabulary = Vocabulary(
                            author=req.user,
                            parent=sys_vocabulary,
                            package=vp,
                            text=text,
                            translation=response[0].strip(),
                            description=response[2].strip(),
                            category=response[1].strip(),
                            created_by="supervisor",
                            organization=req.user.organization
                        )
                else:
                    vocabulary = Vocabulary(
                        author=req.user,
                        package=vp,
                        text=text,
                        translation=translation,
                        description=description,
                        category=category,
                        created_by="supervisor",
                        organization=req.user.organization
                    )
                    
                if image:
                    vocabulary.image = image
                vocabulary.save()

                data["message"] = "success"
            
            else:
                data.update(
                    {
                        "errors": ["spelling"],
                        "suggestions": spelling_check
                    }
                )
        
        return JsonResponse(data, safe=False)


    def get(self, req, *args, **kwargs):

        query = req.GET.get("search", "").strip().lower()

        if query:
            print("query", query)
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
                for product in Product.objects.annotate(
                    serial_str=Cast("serial", CharField())
                ).filter(
                    Q(serial_str__icontains=query) | Q(title__icontains=query),
                    organization=req.user.organization
                )
            ]
        
        else:
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
                for product in Product.objects.filter(
                    organization=req.user.organization
                )
            ]

        return JsonResponse(data, safe=False)
