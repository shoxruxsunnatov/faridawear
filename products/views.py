from django.shortcuts import render
from django.views.generic import TemplateView


class ProductsView(TemplateView):
    template_name = "admins/products_list.html"
