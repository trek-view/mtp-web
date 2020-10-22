## Django Packages
import random
## Python Packages
import uuid
from datetime import datetime

from colorful.fields import RGBColorField
from django.contrib.auth import (
    get_user_model, )
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from mptt.models import MPTTModel, TreeForeignKey

from lib.functions import *
from lib.mvtManager import CustomMVTManager
from sys_setting.models import Tag

UserModel = get_user_model()


def image_directory_path(instance, filename):
    path = 'sequence/{}/{}/{}.jpg'.format(instance.user.username, str(instance.sequence.unique_id), instance.image_key)
    return path


class Icon(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
    font_awesome = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name


def getAllTags():
    items = Tag.objects.filter(is_actived=True)
    itemsTuple = ()
    for item in items:
        itemsTuple = itemsTuple + ((item.pk, item.name),)
    return itemsTuple


class TransType(MPTTModel):
    name = models.CharField(max_length=50, unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    icon = models.ForeignKey(Icon, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.parent is None:
            return self.name
        else:
            return self.parent.name + ' - ' + self.name

    def getFullName(self):
        if self.parent is None:
            return self.name
        else:
            return self.parent.name + ' - ' + self.name

    def getPK(self):
        return self.pk

    class MPTTMeta:
        level_attr = 'mptt_level'
        order_insertion_by = ['name']

    class Meta:
        verbose_name_plural = 'Transport Type'


class LabelType(MPTTModel):
    name = models.CharField(max_length=100)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    description = models.TextField(blank=True, null=True)
    # type is one of "point" and "polygon"
    # type = models.CharField(max_length=50, choices=(('point', 'point'), ('polygon', 'polygon'),), default='point')
    type = models.CharField(max_length=50, choices=(('polygon', 'polygon'),), default='polygon')
    color = RGBColorField(null=True, blank=True)
    source = models.CharField(max_length=50, choices=(('mtpw', 'MTPW'), ('mapillary', 'Mapillary')), default='mtpw')

    def __str__(self):
        if self.parent is None:
            return self.name
        else:
            return self.parent.name + '--' + self.name

    def save(self, *args, **kwargs):
        color = self.color
        if self.pk is None:
            super().save(*args, **kwargs)
            if self.parent is None or self.source == 'mapillary':
                while True:
                    while color is None or color == '#000000':
                        color = '#%02X%02X%02X' % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                    labelType = LabelType.objects.filter(color=color).exclude(pk=self.pk)
                    if labelType.count() == 0:
                        self.color = color
                        break
                    color = '#%02X%02X%02X' % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            else:
                if color is None or color == '#000000':
                    self.color = self.parent.color
            self.save()
        else:
            labelType = LabelType.objects.get(pk=self.pk)
            if labelType.parent != self.parent:
                self.color = self.parent.color
            super().save(*args, **kwargs)

    def getKey(self):
        if self.parent is None:
            key = self.name
        else:
            key = self.parent.name + '--' + self.name
        key = key.replace(' ', '-')
        key = key.lower()
        return key

    class MPTTMeta:
        level_attr = 'mptt_level'
        order_insertion_by = ['name']

    class Meta:
        verbose_name_plural = 'Image Label Type'


class CameraMake(models.Model):
    name = models.CharField(max_length=50, default='')

    def __str__(self):
        return self.name


class CameraModel(models.Model):
    name = models.CharField(max_length=50, default='')

    def __str__(self):
        return self.name


class CustomSequenceMVTManager(CustomMVTManager):
    def get_additional_where(self, additional_filters={}, request=None):
        from tour.models import Tour
        additional_where = ""
        page_name = ''
        if 'page_name' in additional_filters.keys() and additional_filters['page_name'] != '':
            page_name = additional_filters['page_name']
        else:
            return ''

        if page_name == 'tour_detail' and 'tour_unique_id' in additional_filters.keys():
            tours = Tour.objects.filter(unique_id=additional_filters['tour_unique_id'])[:1]
            if tours.count() > 0:
                tour_id = tours[0].pk
                table_name = 'tour_toursequence'
                additional_where += f"""
                and id in (Select sequence_id From {table_name} Where tour_id = '{tour_id}')  
                """

        if page_name == 'tour_list' and request.session['tours_query'] is not None:
            additional_where = ' AND id in ( SELECT "tour_toursequence"."sequence_id" FROM "tour_toursequence" WHERE "tour_toursequence"."tour_id" in ( SELECT t.id as id FROM (' + request.session['tours_query'] + ') as t )) '

        if page_name == 'sequence_list' and request.session['sequences_query'] is not None:
            additional_where = ' AND id in ( SELECT t.id as id FROM (' + request.session['sequences_query'] + ') as t )'

        additional_where = additional_where.replace('(%', "('%%").replace('%)', "%%')")
        return additional_where


class Sequence(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    camera_make = models.ForeignKey(CameraMake, on_delete=models.CASCADE, null=True, blank=True)
    captured_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    seq_key = models.CharField(max_length=100, null=True, blank=True, verbose_name="Mapillary Sequence Key",)
    pano = models.BooleanField(default=False)
    user_key = models.CharField(max_length=100, null=True, blank=True, verbose_name="Mapillary User Key",)
    username = models.CharField(max_length=100, null=True, blank=True, verbose_name="Mapillary Username",)
    geometry_coordinates = models.LineStringField(null=True, blank=True, srid=4326)
    geometry_coordinates_ary = ArrayField(ArrayField(models.FloatField(default=1)), null=True, blank=True)
    coordinates_cas = ArrayField(models.FloatField(default=0), null=True, blank=True)
    coordinates_image = ArrayField(models.CharField(default='', max_length=100), null=True, blank=True)
    is_uploaded = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)

    name = models.CharField(max_length=100, default='')
    description = models.TextField(default='')
    transport_type = models.ForeignKey(TransType, on_delete=models.CASCADE, null=True)
    tag = models.ManyToManyField(Tag)

    image_count = models.IntegerField(default=0)

    is_mapillary = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)
    is_image_download = models.BooleanField(default=False)
    is_map_feature = models.BooleanField(default=False)

    google_street_view = models.BooleanField(default=False)
    strava = models.CharField(max_length=50, null=True, blank=True)

    distance = models.FloatField(null=True, blank=True)

    objects = models.Manager()
    vector_tiles = CustomSequenceMVTManager(
        geo_col='geometry_coordinates',
        select_columns=['seq_key', 'unique_id'],
        is_show_id=False,
        source_layer='mtp-sequences'
    )

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('sequence.sequence_detail', kwargs={'unique_id': str(self.unique_id)})

    def get_image_count(self):
        if self.coordinates_image is not None:
            return len(self.coordinates_image)
        else:
            return 0

    def get_tag_str(self):
        tags = []
        if self.tag.all().count() == 0:
            return ''
        for tag in self.tag.all():
            if tag and tag.is_actived:
                tags.append(tag.name)

        if len(tags) > 0:
            return ', '.join(tags)
        else:
            return ''

    def get_tags(self):
        tags = []
        if self.tag.all().count() == 0:
            return ''
        for tag in self.tag.all():
            if tag and tag.is_actived:
                tags.append(tag.name)
        return tags

    def get_short_description(self):
        description = self.description
        if len(description) > 100:
            return description[0:100] + '...'
        else:
            return description

    def get_first_image_key(self):
        if len(self.coordinates_image) > 0:
            return self.coordinates_image[0]
        else:
            return ''

    def get_mapillary_username(self):
        return self.username

    def get_like_count(self):
        liked_guidebook = SequenceLike.objects.filter(sequence=self)
        if not liked_guidebook:
            return 0
        else:
            return liked_guidebook.count()

    def get_distance(self):
        all_distance = 0
        if self.geometry_coordinates_ary is None:
            return all_distance

        if len(self.geometry_coordinates_ary) > 0:
            first_point = self.geometry_coordinates_ary[0]
            for i in range(len(self.geometry_coordinates_ary) - 1):
                if i == 0:
                    continue
                second_point = self.geometry_coordinates_ary[i]
                d = distance(first_point, second_point)
                first_point = second_point
                all_distance += d
            all_distance = "%.3f" % all_distance
        return all_distance

    def get_cover_image(self):
        image_keys = self.coordinates_image
        if image_keys is None:
            return None
        if len(image_keys) > 0:
            return image_keys[0]
        else:
            return None

    def get_first_point_lat(self):
        if self.geometry_coordinates_ary is None:
            return None
        lat = self.geometry_coordinates_ary[0][1]
        return lat

    def get_first_point_lng(self):
        if self.geometry_coordinates_ary is None:
            return None
        lng = self.geometry_coordinates_ary[0][0]
        return lng


class CustomImageMVTManager(CustomMVTManager):
    def get_additional_where(self, additional_filters={}, request=None):
        from tour.models import Tour
        additional_where = ""
        page_name = ''
        if 'page_name' in additional_filters.keys() and additional_filters['page_name'] != '':
            page_name = additional_filters['page_name']
        else:
            return ''
        if page_name == 'tour_detail' and 'tour_unique_id' in additional_filters.keys():
            tours = Tour.objects.filter(unique_id=additional_filters['tour_unique_id'])[:1]
            if tours.count() > 0:
                tour_id = tours[0].pk
                table_name = 'tour_toursequence'
                additional_where += f"""
                and sequence_id in (Select sequence_id From {table_name} Where tour_id = '{tour_id}')  
                """

        elif page_name == 'tour_list' and request.session['tours_query'] is not None:
            additional_where = ' AND sequence_id in ( SELECT "tour_toursequence"."sequence_id" FROM "tour_toursequence" WHERE "tour_toursequence"."tour_id" in ( SELECT t.id as id FROM (' + request.session['tours_query'] + ') as t )) '

        elif page_name == 'sequence_list' and request.session['sequences_query'] is not None:
            additional_where = ' AND sequence_id in ( SELECT t.id as id FROM (' + request.session['sequences_query'] + ') as t )'

        elif page_name == 'photo_list' and request.session['images_query'] is not None:
            additional_where = ' AND id in ( SELECT t.id as id FROM (' + request.session['images_query'] + ') as t )'

        additional_where = additional_where.replace('(%', "('%%").replace('%)', "%%')")
        return additional_where


class Image(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)

    camera_make = models.ForeignKey(CameraMake, on_delete=models.CASCADE, null=True, blank=True)
    camera_model = models.ForeignKey(CameraModel, on_delete=models.CASCADE, null=True, blank=True)
    cas = models.FloatField(default=0)
    captured_at = models.DateTimeField(null=True, blank=True)
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE, null=True, blank=True)
    seq_key = models.CharField(max_length=100, default='')
    image_key = models.CharField(max_length=100)
    pano = models.BooleanField(default=False)
    user_key = models.CharField(max_length=100, default='')
    username = models.CharField(max_length=100, default='')
    organization_key = models.CharField(max_length=255, null=True)
    is_uploaded = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)
    is_mapillary = models.BooleanField(default=True)
    lat = models.FloatField(default=0)
    lng = models.FloatField(default=0)
    ele = models.FloatField(default=0)
    type = models.CharField(max_length=50, default='Point')

    point = models.PointField(null=True, blank=True)

    mapillary_image = models.ImageField(upload_to=image_directory_path, null=True, blank=True)

    image_label = models.ManyToManyField(LabelType, through='ImageLabel')

    objects = models.Manager()
    vector_tiles = CustomImageMVTManager(
        geo_col='point',
        select_columns=['image_key', 'unique_id'],
        is_show_id=False,
        source_layer='mtp-images'
    )

    def get_sequence_by_key(self):
        if self.seq_key != '':
            sequence = Sequence.objects.get(seq_key=self.seq_key)
            if sequence is None or not sequence:
                return None
            return sequence
        return None


class SequenceLike(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE)


class ImageViewPoint(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    owner = models.ForeignKey(UserModel, on_delete=models.CASCADE, null=True, blank=True, related_name='owner_id')


class ImageLabel(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    label_type = models.ForeignKey(LabelType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    point = models.PointField(null=True, blank=True)
    polygon = models.PolygonField(null=True, blank=True)


class SequenceWeather(models.Model):
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE)

    location_name = models.CharField(max_length=100, null=True, blank=True)
    location_country = models.CharField(max_length=100, null=True, blank=True)
    location_region = models.CharField(max_length=100, null=True, blank=True)
    location_timezone_id = models.CharField(max_length=100, null=True, blank=True)
    location_lat = models.FloatField(default=0)
    location_lon = models.FloatField(default=0)
    location_localtime = models.CharField(max_length=100, null=True, blank=True)
    location_localtime_epoch = models.IntegerField(default=0)
    location_utc_offset = models.CharField(max_length=100, null=True, blank=True)

    current_observation_time = models.CharField(max_length=50, null=True, blank=True)
    current_temperature = models.IntegerField(default=0)
    current_weather_code = models.IntegerField(default=0)
    current_weather_icons = ArrayField(models.TextField(default=''), null=True, blank=True)
    current_weather_descriptions = ArrayField(models.CharField(max_length=100, default=''), null=True, blank=True)
    current_wind_speed = models.IntegerField(default=0)
    current_wind_degree = models.IntegerField(default=0)
    current_wind_dir = models.CharField(max_length=100, null=True, blank=True)
    current_pressure = models.IntegerField(default=0)
    current_precip = models.IntegerField(default=0)
    current_humidity = models.IntegerField(default=0)
    current_cloudcover = models.IntegerField(default=0)
    current_feelslike = models.IntegerField(default=0)
    current_uv_index = models.IntegerField(default=0)
    current_visibility = models.IntegerField(default=0)
    current_is_day = models.CharField(max_length=50, null=True, blank=True)

    his_date = models.DateField(null=True, blank=True)
    his_date_epoch = models.IntegerField(default=0)
    his_astro_sunrise = models.CharField(max_length=50, null=True, blank=True)
    his_astro_sunset = models.CharField(max_length=50, null=True, blank=True)
    his_astro_moonrise = models.CharField(max_length=50, null=True, blank=True)
    his_astro_moonset = models.CharField(max_length=50, null=True, blank=True)
    his_astro_moon_phase = models.CharField(max_length=50, null=True, blank=True)

    his_mintemp = models.IntegerField(default=0)
    his_maxtemp = models.IntegerField(default=0)
    his_avgtemp = models.IntegerField(default=0)
    his_totalsnow = models.IntegerField(default=0)
    his_sunhour = models.IntegerField(default=0)
    his_uv_index = models.IntegerField(default=0)

    his_hourly_time = models.IntegerField(default=0)
    his_hourly_temperature = models.IntegerField(default=0)
    his_hourly_wind_speed = models.IntegerField(default=0)
    his_hourly_wind_degree = models.IntegerField(default=0)
    his_hourly_wind_dir = models.CharField(max_length=50, null=True, blank=True)
    his_hourly_weather_code = models.IntegerField(default=0)
    his_hourly_weather_icons = ArrayField(models.TextField(default=''), null=True, blank=True)
    his_hourly_weather_descriptions = ArrayField(models.CharField(max_length=100, default=''), null=True, blank=True)
    his_hourly_precip = models.IntegerField(default=0)
    his_hourly_humidity = models.IntegerField(default=0)
    his_hourly_visibility = models.IntegerField(default=0)
    his_hourly_pressure = models.IntegerField(default=0)
    his_hourly_cloudcover = models.IntegerField(default=0)
    his_hourly_heatindex = models.IntegerField(default=0)
    his_hourly_dewpoint = models.IntegerField(default=0)
    his_hourly_windchill = models.IntegerField(default=0)
    his_hourly_windgust = models.IntegerField(default=0)
    his_hourly_feelslike = models.IntegerField(default=0)
    his_hourly_chanceofrain = models.IntegerField(default=0)
    his_hourly_chanceofremdry = models.IntegerField(default=0)
    his_hourly_chanceofwindy = models.IntegerField(default=0)
    his_hourly_chanceofovercast = models.IntegerField(default=0)
    his_hourly_chanceofsunshine = models.IntegerField(default=0)
    his_hourly_chanceoffrost = models.IntegerField(default=0)
    his_hourly_chanceofhightemp = models.IntegerField(default=0)
    his_hourly_chanceoffog = models.IntegerField(default=0)
    his_hourly_chanceofsnow = models.IntegerField(default=0)
    his_hourly_chanceofthunder = models.IntegerField(default=0)
    his_hourly_uv_index = models.IntegerField(default=0)


class MapFeature(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    accuracy = models.FloatField(default=0)
    altitude = models.FloatField(default=0)
    direction = models.FloatField(default=0)
    first_seen_at = models.DateTimeField(null=True, blank=True)
    mf_key = models.CharField(max_length=100, null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    layer = models.CharField(max_length=50)
    value = models.CharField(max_length=100)
    geometry_type = models.CharField(max_length=50, default='Point')
    geometry_point = models.PointField(null=True, blank=True)
    detection_keys = ArrayField(ArrayField(models.CharField(max_length=50)), null=True, blank=True)
    image_keys = ArrayField(ArrayField(models.CharField(max_length=50)), null=True, blank=True)
    user_keys = ArrayField(ArrayField(models.CharField(max_length=50)), null=True, blank=True)


# class MapFeatureDetection(models.Model):
#     image_key = models.CharField(max_length=100, null=True, blank=True)
#     detection_key = models.CharField(max_length=100, null=True, blank=True)
#     user_key = models.CharField(max_length=100, null=True, blank=True)
#     map_feature = models.ForeignKey(MapFeature, on_delete=models.CASCADE)
