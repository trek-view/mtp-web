## Django Packages
from django.shortcuts import get_object_or_404, render

############################################################################

MAIN_PAGE_DESCRIPTION = "Access street-level imagery and map data from all over the world.  Fill in the gaps by requesting new coverage or capturing your own."

def index(request):
    content = {
        'pageName': 'Map the Paths',
        'pageTitle': 'Map the Paths',
        'pageDescription': MAIN_PAGE_DESCRIPTION
    }
    return render(request, 'home.html', content)

def app_download(request):
    content = {
        'pageName': 'MTP Uploader',
        'pageTitle': 'MTP Uploader',
        'pageDescription': MAIN_PAGE_DESCRIPTION
    }
    return render(request, 'app_download.html', content)