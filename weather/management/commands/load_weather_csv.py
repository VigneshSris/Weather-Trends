import csv
from django.core.management.base import BaseCommand
from weather.models import WeatherRecord
from django.utils.dateparse import parse_date
from django.db import transaction

class Command(BaseCommand):
    help = 'Load weather CSV'
    def add_arguments(self, parser):
        parser.add_argument('csvfile', type=str)
        parser.add_argument('--truncate', action='store_true')
    def handle(self, *args, **options):
        path = options['csvfile']
        if options['truncate']:
            WeatherRecord.objects.all().delete()
        rows = []
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                d = parse_date(r.get('date')) or None
                try:
                    rows.append(WeatherRecord(
                        date=d,
                        city=r.get('city','').strip(),
                        temperature_c=float(r.get('temperature_c') or 0),
                        humidity=float(r.get('humidity') or 0),
                        rainfall_mm=float(r.get('rainfall_mm') or 0)
                    ))
                except Exception:
                    continue
        with transaction.atomic():
            WeatherRecord.objects.bulk_create(rows, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(rows)} records.'))
