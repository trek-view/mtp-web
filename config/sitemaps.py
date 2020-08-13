from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse
class StaticViewSitemap(Sitemap):
    def items(self):
        return [
            'marketplace.job_create',
            'marketplace.home',
            'marketplace.photographer_create',
            'guidebook.home',
            'home',
            'guidebook.create'
        ]
    def location(self, item):
        return reverse(item)