def get_correct_sql(query_set_object):
    sql, params = query_set_object.query.sql_with_params()
    new_params = []
    for param in params:
        if isinstance(param, str):
            param = "'" + param + "'"
        new_params.append(param)
    return sql % tuple(new_params)

