from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse
class StaticViewSitemap(Sitemap):
    def items(self):
        return [
            'home',
            'login',
            'challenge.challenge_list',
            'challenge.challenge_create',
            'challenge.my_label_challenge_list',
            'challenge.label_challenge_create',
            'guidebook.create',
            'guidebook.guidebook_list',
            'leaderboard.index',
            'photographer.photographer_list',
            'photographer.photographer_create',
            'sequence.sequence_list',
            'sequence.image_leaderboard',
            'tour.tour_list',
            'tour.tour_create'
        ]
    def location(self, item):
        return reverse(item)