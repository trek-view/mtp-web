from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Scrapes spoj.com to obtain the details of all the classical problems.'

    def handle(self, *args, **options):
        print('test')
