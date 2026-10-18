import csv
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render
from catalog.models import Product

FIELDS = ["source", "source_id", "title", "price", "currency", "description", "image_url", "listing_url", "availability", "scraped_at"]

def products(request):
    query = request.GET.get("q", "").strip()
    result = Product.objects.all()
    return result.filter(title__icontains=query) if query else result

def index(request):
    rows = products(request)
    return render(request, "catalog/index.html", {"page": Paginator(rows, 24).get_page(request.GET.get("page")), "q": request.GET.get("q", ""), "total": Product.objects.count()})

def export(request, kind):
    rows = list(products(request).values(*FIELDS))
    if kind == "json":
        response = JsonResponse(rows, safe=False, json_dumps_params={"indent": 2, "ensure_ascii": False})
    elif kind == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response.write("\ufeff")
        writer = csv.writer(response)
        writer.writerow(FIELDS)
        for row in rows:
            # Neutralize spreadsheet formulas in scraped text.
            values = [str(row[field]) for field in FIELDS]
            writer.writerow(["'" + v if v.lstrip().startswith(("=", "+", "-", "@")) else v for v in values])
    else:
        raise Http404("Choose csv or json")
    response["Content-Disposition"] = f'attachment; filename="products.{kind}"'
    return response
