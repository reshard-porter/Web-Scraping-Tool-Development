import requests
from django.core.management.base import BaseCommand, CommandError
from catalog.models import Product
from catalog.scraper import BooksClient, ScrapeError

class Command(BaseCommand):
    help = "Collect Books to Scrape products; repeat runs update existing records."

    def add_arguments(self, parser):
        parser.add_argument("--pages", type=int, default=1)
        parser.add_argument("--delay", type=float, default=1.0)

    def handle(self, *args, **options):
        if not 1 <= options["pages"] <= 50:
            raise CommandError("--pages must be between 1 and 50")
        if not 0.5 <= options["delay"] <= 60:
            raise CommandError("--delay must be between 0.5 and 60 seconds")
        client = BooksClient(options["delay"])
        count = 0
        try:
            for data in client.products(options["pages"]):
                source = data.pop("source")
                source_id = data.pop("source_id")
                Product.objects.update_or_create(source=source, source_id=source_id, defaults=data)
                count += 1
                self.stdout.write(f"Saved {count}: {data['title']}")
        except (ScrapeError, requests.RequestException) as exc:
            raise CommandError(f"Stopped after {count} saved products: {exc}. Saved records remain; rerun safely.") from exc
        finally:
            client.close()
        self.stdout.write(self.style.SUCCESS(f"Finished: {count} products saved."))
