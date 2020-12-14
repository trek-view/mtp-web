## Django Packages
from django.shortcuts import get_object_or_404, render
from lib.functions import *
from sys_setting.models import BusinessTier
from django.contrib.auth import (
    get_user_model, )


from accounts.models import Grade

UserModel = get_user_model()
############################################################################

MAIN_PAGE_DESCRIPTION = "Access off-road street-level imagery and map data from all over the world. Fill in the gaps by requesting new coverage or capturing your own."


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
    paid_grades = Grade.objects.filter(user_type='Paid')
    user_grades = []
    for paid_grade in paid_grades:
        paid_users = UserModel.objects.filter(user_grade=paid_grade)
        if paid_users.count() > 0:
            user_grades.append({
                'grade': paid_grade,
                'users': paid_users
            })
    content = {
        'user_grades': user_grades,
        'business': business,
        'pageName': 'Hall of Fame',
        'pageTitle': 'Hall of Fame',
        'pageDescription': 'Trek View is creating open source software to save the environment. The Hall of Fame highlights people helping us to achieve our ambitious goal.'
    }

    return render(request, 'about/hall_of_fame.html', content)


def about(request):
    content = {
        'pageName': 'About Us',
        'pageTitle': 'About Us',
        'pageDescription': ''
    }

    return render(request, 'about/about.html', content)


def handler404(request, *args, **argv):
    return render(request, '404.html')


def handler500(request, *args, **argv):
    return render(request, '500.html')
