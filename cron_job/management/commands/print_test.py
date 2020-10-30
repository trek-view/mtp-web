from django.core.management.base import BaseCommand
from sequence.models import Sequence, Image, TransType
import time


class Command(BaseCommand):
    help = 'check sequences published on mapillary'

    def handle(self, *args, **options):
        for i in range(100):
            print('---------------{}---------------'.format(i))
            time.sleep(60)
