from django.core.management.base import BaseCommand
from sequence.models import Sequence, Image, TransType
import time
from datetime import datetime, timedelta




def check_sequence(sequences):
    for sequence in sequences:
        start_time = sequence.start_time
        end_time = sequence.end_time


class Command(BaseCommand):
    help = 'check sequences published on mapillary'

    def handle(self, *args, **options):
        last_hour_date_time = datetime.now() - timedelta(hours=1)
        tmp_sequences = Sequence.objects.filter(image_count=0, updated_at__gte=last_hour_date_time)


