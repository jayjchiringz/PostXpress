import csv
from django.core.management.base import BaseCommand
from postal.models import Station
from django.conf import settings

class Command(BaseCommand):
    help = 'Import stations from a CSV file'

    def handle(self, *args, **kwargs):
        file_path = "/home/opc/PostXpress/Stations_2.csv"
        
        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    code = row['Code']
                    office = row['Office']
                    Station.objects.get_or_create(code=code, office=office)
                    self.stdout.write(self.style.SUCCESS(f'Successfully added station: {office} ({code})'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error importing stations: {e}'))
