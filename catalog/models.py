from django.db import models

class Product(models.Model):
    source = models.CharField(max_length=100)
    source_id = models.CharField(max_length=100)
    title = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=2000)
    listing_url = models.URLField(max_length=2000)
    availability = models.CharField(max_length=200, blank=True)
    scraped_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["source", "source_id"], name="unique_source_product")]
        ordering = ["title"]
