import csv
from django.core.management.base import BaseCommand
from accounts.models import College
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = "Import college data from CSV"

    def handle(self, *args, **kwargs):
        with open('colleges.csv', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                College.objects.update_or_create(
                    username=row['Username'],
                    defaults={
                        'college_name': row['College'],
                        'district': row['District'],
                        'password': make_password(row['Password']),
                    }
                )
        self.stdout.write(self.style.SUCCESS("College data imported successfully!"))
