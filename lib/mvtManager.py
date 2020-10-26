from rest_framework_mvt.managers import MVTManager
import re

class CustomMVTManager(MVTManager):

    select_columns = None
    is_show_id = True
    source_layer = 'default'
    additional_where = ''

    def __init__(self, *args, geo_col="geom", source_name=None, select_columns=None, is_show_id=True, source_layer='default', **kwargs):
        super(MVTManager, self).__init__(*args, **kwargs)
        self.geo_col = geo_col
        self.source_name = source_name
        self.select_columns = select_columns
        self.is_show_id = is_show_id
        self.source_layer = source_layer

    def _get_non_geom_columns(self):
        """
        Retrieves all table columns that are NOT the defined geometry column
        """
        columns = []
        if self.select_columns is None:
            for field in self.model._meta.get_fields():
                if hasattr(field, "get_attname_column"):
                    column_name = field.get_attname_column()[1]
                    if column_name != self.geo_col:
                        columns.append(column_name)
        else:
            columns = self.select_columns

        return columns

    def _build_query(self, filters=None, additional_where=''):
        """
        Args:
            filters (dict): keys represent column names and values represent column
                            values to filter on.
        Returns:
            tuple:
            A tuple of length two.  The first element is a string representing a
            parameterized SQL query.  The second element is a list of parameters
            used as inputs to the query's WHERE clause.
        """
        if filters is None:
            filters = {}
        table = self.model._meta.db_table.replace('"', "")
        select_statement = self._create_select_statement()
        (
            parameterized_where_clause,
            where_clause_parameters,
        ) = self._create_where_clause_with_params(table, filters)
        query = f"""
        SELECT NULL AS id, ST_AsMVT(q, '{self.source_layer}', 4096, 'mvt_geom')
            FROM (SELECT {select_statement}
                ST_AsMVTGeom(ST_Transform({table}.{self.geo_col}, 3857),
                ST_Transform(ST_SetSRID(ST_GeomFromText(%s), 4326), 3857), 4096, 0, false) AS mvt_geom
            FROM {table}
            WHERE {parameterized_where_clause} {additional_where}
            LIMIT %s
            OFFSET %s) AS q;
        """
        return (query.strip(), where_clause_parameters)

    def intersect(self, bbox="", limit=-1, offset=0, filters={}, additional_filters={}, request=None ):
        """
        Args:
            bbox (str): A string representing a bounding box, e.g., '-90,29,-89,35'.
            limit (int): Number of entries to include in the result.  The default
                         is -1 (includes all results).
            offset (int): Index to start collecting entries from.  Index size is the limit
                          size.  The default is 0.
            filters (dict): The keys represent column names and the values represent column
                            values to filter on.
        Returns:
            bytes:
            Bytes representing a Google Protobuf encoded Mapbox Vector Tile.  The
            vector tile will store each applicable row from the database as a
            feature.  Applicable rows fall within the passed in bbox.

        Raises:
            ValidationError: If filters include keys or values not accepted by
                             the manager's model.

        Note:
            The sql execution follows the guidelines from Django below.  As suggested, the executed
            query string does NOT contain quoted parameters.

            https://docs.djangoproject.com/en/2.2/topics/db/sql/#performing-raw-queries
        """
        additional_where = self.get_additional_where(additional_filters=additional_filters, request=request)

        additional_where = additional_where.replace("('%", "('%%").replace("%)'", "%%')")
        date_format = re.findall('\d\d\d\d-\d\d-\d\d 00:00:00[+]00:00', additional_where)
        for d in date_format:
            additional_where = additional_where.replace(d, "'{}'".format(d))
        additional_where = additional_where.replace("['", "ARRAY['")
        # print(additional_where)
        # additional_where = ''
        limit = "ALL" if limit == -1 else limit
        query, parameters = self._build_query(filters=filters, additional_where=additional_where)
        with self._get_connection().cursor() as cursor:
            cursor.execute(query, [str(bbox), str(bbox)] + parameters + [limit, offset])
            mvt = cursor.fetchall()[-1][-1]  # should always return one tile on success
        return mvt

    def get_additional_where(self, additional_filters={}, request=None):
        additional_where = ''
        return additional_where
