import csv
from django.core.management.base import BaseCommand
from accounts.models import Item

class Command(BaseCommand):
    help = "Load items from CSV into Item model"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to CSV file")

    def handle(self, *args, **kwargs):
        csv_file = kwargs["csv_file"]

        try:
            with open(csv_file, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    name = row["ITEM"].strip()
                    numbers = int(row["Numbers"])
                    category = row["Category"].strip()

                    # If you want max_participants = numbers, uncomment:
                    max_participants = numbers

                    obj, created = Item.objects.get_or_create(
                        name=name,
                        defaults={
                            "numbers": numbers,
                            "category": category,
                            "max_participants": max_participants,
                        }
                    )

                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Added → {name}"))
                    else:
                        # Update existing entry
                        obj.numbers = numbers
                        obj.category = category
                        obj.max_participants = max_participants
                        obj.save()

                        self.stdout.write(self.style.WARNING(f"Updated → {name}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
