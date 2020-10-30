## Django Packages
from django.shortcuts import get_object_or_404, render
from lib.functions import *
from sys_setting.models import BusinessTier, GoldTier, SilverTier
############################################################################

MAIN_PAGE_DESCRIPTION = "Access street-level imagery and map data from all over the world.  Fill in the gaps by requesting new coverage or capturing your own."

def index(request):
    content = {
        'pageName': 'Map the Paths',
        'pageTitle': 'Map the Paths',
        'pageDescription': MAIN_PAGE_DESCRIPTION
    }
    return render(request, 'home.html', content)
    # return redirect(reverse('sequence.sequence_list') + '?view_type=map-view')


@my_login_required
def app_download(request):
    content = {
        'pageName': 'MTP Uploader',
        'pageTitle': 'MTP Uploader',
        'pageDescription': MAIN_PAGE_DESCRIPTION
    }
    return render(request, 'app_download.html', content)


def hall_of_fame(request):
    business = BusinessTier.objects.all()
    gold = GoldTier.objects.all()
    silver = SilverTier.objects.all()
    content = {
        'business': business,
        'gold': gold,
        'silver': silver,
        'pageName': 'Hall of Fame',
        'pageTitle': 'Hall of Fame',
        'pageDescription': 'Trek View is creating open source software to save the environment. The Hall of Fame highlights people helping us to achieve our ambitious goal.'
    }

    return render(request, 'about/hall_of_fame.html', content)
