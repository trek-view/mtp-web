from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework_gis.filters import TMSTileFilter
from rest_framework_mvt.renderers import BinaryRenderer
from rest_framework_mvt.schemas import MVT_SCHEMA
import time
import threading


class BaseMVTView(APIView):
    """
    Base view for serving a model as a Mapbox Vector Tile given X/Y/Z tile constraints.
    """

    model = None
    geom_col = None
    renderer_classes = (BinaryRenderer,)
    schema = MVT_SCHEMA

    permission_classes = []

    mvt = b""
    bbox = None
    limit = None
    offset = None
    filters = None
    params = None
    request = None

    # pylint: disable=unused-argument
    def get(self, request, *args, **kwargs):
        """
        Args:
            request (:py:class:`rest_framework.request.Request`): Standard DRF request object
        Returns:
            :py:class:`rest_framework.response.Response`:  Standard DRF response object
        """
        params = request.GET.dict()


        if params.pop("tile", None) is not None:
            try:
                limit, offset = self._validate_paginate(
                    params.pop("limit", None), params.pop("offset", None)
                )
            except ValidationError:
                limit, offset = None, None
            bbox = TMSTileFilter().get_filter_bbox(request)
            try:
                fields = self.model._meta.fields
                filters = {}
                for field in fields:
                    if field.name in params.keys():
                        filters[field.name] = params[field.name]
                        params.pop(field.name, None)
                print('=========================================')
                start_time = time.time()
                try:
                    self.bbox = bbox
                    self.limit = limit
                    self.offset = offset
                    self.filters = filters
                    self.params = params
                    self.request = request

                    p1 = threading.Thread(target=self.get_mvt)
                    p1.start()
                    p1.join(timeout=5)

                    status = 200 if self.mvt else 204
                except TimeoutError:
                    print('TimeoutError')
                    self.mvt = b""
                    status = 400
                print("--- %s ---" % (time.time() - start_time))


            except ValidationError:
                self.mvt = b""
                status = 400
        else:
            self.mvt = b""
            status = 400
        return Response(
            bytes(self.mvt), content_type="application/vnd.mapbox-vector-tile", status=status
        )

    def get_mvt(self):
        self.mvt = self.model.vector_tiles.intersect(
            bbox=self.bbox, limit=self.limit, offset=self.offset, filters=self.filters, additional_filters=self.params, request=self.request
        )

    @staticmethod
    def _validate_paginate(limit, offset):
        """
        Attempts to convert given limit and offset as strings to integers.
        Args:
            limit (str): A string representing the size of the pagination request
            offset (str): A string representing the starting index of the pagination request
        Returns:
            tuple:
            A tuple of length two.  The first element is an integer representing
            the limit.  The second element is an integer representing the offset.
        Raises:
            `rest_framework.serializers.ValidationError`: if limit or offset can't be cast
                                                        to an integer
        """
        if limit is not None and offset is not None:
            try:
                limit, offset = int(limit), int(offset)
            except ValueError as value_error:
                raise ValidationError(
                    "Query param validation error: " + str(value_error)
                )

        return limit, offset


def mvt_view_factory(model_class, geom_col="geom"):
    """
    Creates an MVTView that serves Mapbox Vector Tiles for the
    given model and geom column.

    Args:
        model_class (:py:class:`django.contrib.gis.db.models.Model`): A GeoDjango model
        geom_col (str): A string representing the column name containing
                        PostGIS geometry types.
    Returns:
        :py:class:`rest_framework_mvt.views.MVTView`:
        A subclass of :py:class:`rest_framework_mvt.views.MVTView` with its geom_col
        and model set to the function's passed in values.
    """

    return type(
        f"{model_class.__name__}MVTView",
        (BaseMVTView,),
        {"model": model_class, "geom_col": geom_col},
    ).as_view()
