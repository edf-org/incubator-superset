from flask import Blueprint, jsonify, request

from aqdc_helpers import (aqdc_exposed_columns, bq_slugify, slugify,
                          superset_query)

from aqdc_map_search import (aqdc_map_search)

def respond_with_csv(base_name, dataframe):
    resp = make_response(dataframe.to_csv())
    resp.headers["Content-Disposition"] = f"attachment; filename={base_name}.csv"
    resp.headers["Content-Type"] = "text/csv"
    return resp

def df_to_catalog(df):
    # exploiting pointers and mutability
    # by inserting refs into the list inline,
    # instead of functionally
    datasets = [] 
    registry = {}
    for index, row in df.iterrows():
        title = row['data_coll_prj_nm']
        name  = slugify(title)
        dataset = registry.get(name, {
            'name': name,
            'title': title,
            'description': (
                f'Some hypothetical user description of the dataset {title}\n'
                'That will likely go on for multiple lines.\n'
                'Other top-level searchable fields will probable be bounding boxes/sites in some form'
            ),
            'resources': [{
                'name': 'dply_snsr_sys',
                'title': 'Deployment Sensor Systems',
                'data': [ ]
            }],
        })
        # TODO assert title = resource['title'] because of slugs
        if not name in registry:
            datasets.append(dataset)
            registry[name] = dataset
        dataset['resources'][0]['data'].append(row.to_dict())
    return datasets

class DatasetCatalog:
    def __init__(self):
        # we have to import lazily to avoid circular imports in config
        from aqdc_models import aqdc_sensor_systems
        self.sensor_systems = aqdc_sensor_systems

    def _query_for_catalog(self, where = None):
        query = superset_query( self.sensor_systems, where=where)
        return df_to_catalog(query.df)

    # todo kinda-scratch code
    def get_dataset(self, approximate_project_name):
        # TODO assert there is only one
        datasets_catalog = self._query_for_catalog(
            where=f'{bq_slugify("data_coll_prj_nm")} = NORMALIZE("{slugify(approximate_project_name)}")'
        )
        assert len(datasets_catalog) == 1, 'No such dataset'
        return datasets_catalog[0]


    def search(self, approximate_project_name):
        return self._query_for_catalog(
            where=f'REGEXP_CONTAINS({bq_slugify("data_coll_prj_nm")}, NORMALIZE("{slugify(approximate_project_name)}"))'
            if approximate_project_name else None
        )


catalog_app = Blueprint('dataset_catalog', __name__)

@catalog_app.route('/aqdc/datasets')
def datasets():
    """Retrieve all datasets, or else search for a project
    """
    return jsonify(DatasetCatalog().search(request.args.get('search', None)))

@catalog_app.route('/aqdc/dataset/<project_slug>')
def dataset(project_slug):
    """Retrieve a single dataset
    """
    return jsonify(DatasetCatalog().get_dataset(project_slug))

BLUEPRINTS = [catalog_app ]
