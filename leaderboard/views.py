# Python packages

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Sum
# Django Packages
from django.shortcuts import render

# Project packages
from accounts.models import CustomUser
from sequence.models import Sequence, ImageViewPoint, CameraMake
from .forms import *

# Custom Libs ##
# App packages

############################################################################

MAIN_PAGE_DESCRIPTION = "Leaderboard shows the ranking of users by Monthly and Transport type. One image is counted as 1 point."

############################################################################


def index(request):

    sequences = None
    page = 1

    y = None
    m = None
    time_type = None
    if request.method == "GET":
        filter_time = request.GET.get('time')
        # page = request.GET.get('page')
        # transport_type = request.GET.get('transport_type')
        # time_type = request.GET.get('time_type')
        form = LeaderboardSearchForm(request.GET)
        if form.is_valid():
            page = request.GET.get('page')
            transport_type = form.cleaned_data['transport_type']
            time_type = form.cleaned_data['time_type']
            if not page or page is None:
                page = 1

            camera_makes = form.cleaned_data['camera_make']

            if time_type is None or not time_type or time_type == 'all_time':
                sequences = Sequence.objects.all().exclude(image_count=0)
            else:
                if time_type == 'monthly':
                    if filter_time is None:
                        now = datetime.now()
                        y = now.year
                        m = now.month
                        form.set_timely('YYYY-MM', str(y) + '-' + str(m))
                    else:
                        form.set_timely('YYYY-MM', filter_time)
                        y = filter_time.split('-')[0]
                        m = filter_time.split('-')[1]
                    sequences = Sequence.objects.filter(
                        captured_at__month=m,
                        captured_at__year=y
                    ).exclude(image_count=0)
                    time_type = 'monthly'
                elif time_type == 'yearly':
                    if filter_time is None:
                        now = datetime.now()
                        y = now.year
                        form.set_timely('YYYY', str(y))
                    else:
                        form.set_timely('YYYY', filter_time)
                        y = filter_time
                    sequences = Sequence.objects.filter(
                        captured_at__year=y
                    ).exclude(image_count=0)
                    time_type = 'yearly'

            if transport_type is not None and transport_type != 'all' and transport_type != '':
                transport_type_obj = TransType.objects.filter(name=transport_type).first()
                if transport_type_obj is not None:
                    children_trans_type = TransType.objects.filter(parent=transport_type_obj)
                    if children_trans_type.count() > 0:
                        types = [transport_type_obj]
                        for t in children_trans_type:
                            types.append(t)
                        sequences = sequences.filter(transport_type__in=types)
                    else:
                        sequences = sequences.filter(transport_type=transport_type_obj)

                form.set_transport_type(transport_type)

            if camera_makes is not None and len(camera_makes) > 0:
                sequences = sequences.filter(camera_make__name__in=camera_makes)
                form.set_camera_makes(camera_makes)

    if sequences is None:
        sequences = Sequence.objects.all().exclude(image_count=0)

    filter_type = request.GET.get('filter_type')

    top_title = 'Uploads Leaderboard'
    if filter_type is not None and filter_type == '1':
        user_json = sequences.values('user').annotate(all_distance=Sum('distance')).order_by('-all_distance')
        form.set_filter_type(filter_type)
        top_title = 'Distance Leaderboard'

    elif filter_type is not None and filter_type == '2':
        user_json = ImageViewPoint.objects.filter(image__sequence__in=sequences).values('owner').annotate(
            image_view_count=Count('image')).order_by('-image_view_count')
        form.set_filter_type(filter_type)
        top_title = 'Viewpoints Leaderboard'

    else:
        user_json = sequences.values('user').annotate(image_count=Sum('image_count')).order_by('-image_count')

    paginator = Paginator(user_json, 10)

    try:
        pItems = paginator.page(page)
    except PageNotAnInteger:
        pItems = paginator.page(1)
    except EmptyPage:
        pItems = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pItems.number < 4:
            first_num = 1
            last_num = 7
        elif pItems.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pItems.number - 3
            last_num = pItems.number + 3
    pItems.paginator.pages = range(first_num, last_num + 1)
    pItems.count = len(pItems)

    for i in range(len(pItems)):
        pItems[i]['rank'] = i + 1
        if 'owner' in pItems[i].keys():
            pItems[i]['user'] = pItems[i]['owner']
        user = CustomUser.objects.get(pk=pItems[i]['user'])

        if user is None or not user:
            continue
        pItems[i]['username'] = user.username

        u_sequences = sequences.filter(user=user)

        used_cameras = []
        u_camera_sequences = u_sequences.values('camera_make').annotate(camera_count=Count('camera_make'))
        if u_camera_sequences.count() > 0:
            for u_s in u_camera_sequences:
                if u_s['camera_make'] is None:
                    continue
                camera = CameraMake.objects.get(pk=u_s['camera_make'])
                used_cameras.append(camera.name)

        used_cameras_str = ', '.join(used_cameras)
        pItems[i]['used_cameras_str'] = used_cameras_str

        used_trans = []
        u_trans_sequences = u_sequences.values('transport_type').annotate(camera_count=Count('transport_type'))
        if u_trans_sequences.count() > 0:
            for u_s in u_trans_sequences:
                transport_t = TransType.objects.filter(pk=u_s['transport_type'])
                if transport_t.count() == 0:
                    continue
                used_trans.append(transport_t[0].name)
        used_trans.sort()
        used_trans_str = ', '.join(used_trans)
        pItems[i]['transport_type'] = used_trans_str

        u_distance = 0
        u_photo_count = 0
        if u_sequences.count() > 0:
            for u_s in u_sequences:
                u_distance += float(u_s.get_distance())
                u_photo_count += u_s.get_image_count()
        pItems[i]['distance'] = "%.3f" % u_distance
        pItems[i]['photo_count'] = u_photo_count

        u_viewpoints = ImageViewPoint.objects.filter(image__sequence__in=sequences, owner=user)
        u_view_point = u_viewpoints.count()
        pItems[i]['view_points'] = u_view_point

    if time_type is None:
        time_type = 'all_time'
    form.set_time_type(time_type)
    content = {
        'items': pItems,
        'form': form,
        'pageName': 'Leaderboard',
        'pageTitle': 'Leaderboard',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page,
        'time_type': time_type,
        'top_title': top_title,
        'filter_time': filter_time
    }
    return render(request, 'leaderboard/list.html', content)
