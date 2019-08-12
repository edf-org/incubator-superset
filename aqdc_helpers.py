import re
from copy import deepcopy


def select_fields_as_dict(source, fields):
    """ Select a subdict of the given source based on fields
    """
    return {
        field: getattr(source, field)
        for field in fields
    }

def natural_key_adder(session, cls, natural_key_fields, surrogate_key_field='id'):
    """Wrap sqlalchemy's session.add with a human-usable, natural-key-based, idempotent adder

    By using this adder we can safely ensure a resource with the given properties exists in superset,
    And can thus confidently use it in our extension routes
    """

    def add_instance(instance):
        with session.no_autoflush:
            # get the natural key we've declared
            natural_key = select_fields_as_dict(instance, natural_key_fields)
            existing = session.query(cls).filter_by(**natural_key).first()
            if existing:
                # remove existing instance if present
                if instance in session:
                    session.expunge(instance)
                setattr(
                    instance,
                    surrogate_key_field,
                    getattr(existing, surrogate_key_field)
                )
                session.merge(instance)
                return existing
            else:
                if instance not in session:
                    session.add(instance)
                return instance

    return add_instance


# TODO hide user id? 
_aqdc_private_columns = {
    # at least `snsr_sys` accounted for here
    'src_data_stor_bkt',
    'mtdt_config_file_nm',
    'dc_curr_flg',
    'dc_eff_ts',
    'dc_end_ts',
    'dc_updt_by',
    'dc_batch_nbr',

    'aqdc_dply_snsr_sys_id',
    'aqdc_dply_snsr_id',
}

def aqdc_exposed_columns(sqla_table):
    return [
        column for column in 
        sqla_table.column_names
        if column not in _aqdc_private_columns
    ]


_default_query_obj = {
    'metrics': [],
    'groupby': [],
    'granularity': None,
    'from_dttm': None,
    'to_dttm': None,
    'is_timeseries': False,
    'extras': {},
    'is_prequery': False,
    'prequeries': [],
    'filter': [{
        "col": "dc_curr_flg", "op": "==", "val": True,
    }]
}

def superset_query(table, query_obj = None, where = None):
    query_obj = deepcopy({**_default_query_obj, **(query_obj or {})})
    if where:
        query_obj['extras']['where'] = where
    if not 'columns' in query_obj:
        # default to all non-hidden aqdc columns
        query_obj['columns'] = aqdc_exposed_columns(table)
    return table.query(query_obj)


_slug_substitutions = [
    (r'[^\w_]+', '_'),
    (r'__+', '_'),
    (r'^_+|_+$', '')
]

# TODO add project slug to schema
def slugify(project_name):
    if not project_name:
      return ''
    
    slug = project_name.strip().lower()
    for find_pattern, substitution in _slug_substitutions:
      slug = re.sub(find_pattern, substitution, slug)
    return slug



def bq_slugify(field_name):
    # normalize just in case of special characters
    slug_expression = f'LOWER(TRIM(NORMALIZE({field_name})))'
    for find_pattern, substitution in _slug_substitutions:
        slug_expression = f'REGEXP_REPLACE({slug_expression}, r"{find_pattern}", "{substitution}")'
    return slug_expression 
