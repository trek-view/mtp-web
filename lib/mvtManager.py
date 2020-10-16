from rest_framework_mvt.managers import MVTManager

class CustomMVTManager(MVTManager):

    select_columns = None
    is_show_id = True
    source_layer = 'default'

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

    def _build_query(self, filters=None):
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
            WHERE {parameterized_where_clause}
            LIMIT %s
            OFFSET %s) AS q;
        """
        return (query.strip(), where_clause_parameters)
