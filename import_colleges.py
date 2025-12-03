import csv
from django.core.management.base import BaseCommand
from accounts.models import College

class Command(BaseCommand):
    help = "Import college data from CSV"

    def handle(self, *args, **kwargs):
        with open('/home/brijesh/kalolsavam2026/colleges.csv', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                College.objects.update_or_create(
                    username=row['username'],
                    defaults={
                        'college_name': row['college'],
                        'district': row['district'],
                        'password': row['password'],   # store hashed later
                    }
                )
        self.stdout.write(self.style.SUCCESS("College data imported successfully!"))
