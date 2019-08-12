from superset import db
from superset.connectors.sqla.models import SqlaTable
from superset.models.core import Database

from aqdc_helpers import natural_key_adder

_add_database = natural_key_adder(db.session, Database, ['verbose_name', 'database_name'])
_add_table = natural_key_adder(db.session, SqlaTable, ['database_id', 'schema', 'table_name'])


aqdc_bq = _add_database(Database(
    database_name = 'aqdc_superset_prod_r1',
    sqlalchemy_uri = 'bigquery://glowing-palace-179100/',
    allow_run_async=False,
    allow_multi_schema_metadata_fetch=True
))

aqdc_staging = _add_database(Database(
    database_name = 'aqc_staging',
    sqlalchemy_uri = 'bigquery://glowing-palace-179100/',
    allow_run_async=False,
    allow_multi_schema_metadata_fetch=True
))

aqdc_sensor_systems = _add_table(SqlaTable(
    database_id=aqdc_staging.id,
    database=aqdc_staging,
    schema='aqdc_staging',
    table_name='aqdc_d_dply_snsr_sys',
    #main_dttm_col='dply_mtdt_eff_ts', # not sure if this param is necessary or useful
    description='AQDC Sensor Systems',
))

aqdc_sensor_systems.fetch_metadata()

db.session.flush()
