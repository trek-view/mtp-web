from django.core.management.base import BaseCommand
from sequence.models import Sequence, Image, TransType



class Command(BaseCommand):
    help = 'check sequences published on mapillary'

    def handle(self, *args, **options):
        transport_types = TransType.objects.all()
        print(transport_types.count())
        for t in transport_types:
            print(t.name)
