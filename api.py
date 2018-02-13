from flask import Flask, request
from flask_restful import Resource, Api, reqparse, abort
import datetime
import json
import ast
from functools import wraps
import elasticsearch as elasticsearch
import elasticsearch_dsl as es_dsl

es = elasticsearch.Elasticsearch()

# ES indes to store data point
API_INDEX_POINT = 'timeseries-api-points'
API_TYPE_POINT = 'point'
# ES index to store meta-data
API_INDEX_SERIES = 'timeseries-api-series'
API_TYPE_SERIES = 'series'

API_USERS_LIST = '/etc/timeseries-api/users.json'

app = Flask(__name__)
api = Api(app)

series_parser = reqparse.RequestParser()
series_parser.add_argument('token', type=str, required=True, help='The authentication token')
series_parser.add_argument('device_id', required=True, type=str, help='Some kind of device ID')
series_parser.add_argument('device_desc', required=True, type=str, help='Some kind of device ID')
series_parser.add_argument('desc', type=str, help='A description of the series')

point_parser = reqparse.RequestParser()
point_parser.add_argument('series_id', type=str, required=True,
                       help='The session identification number produced by the device')
point_parser.add_argument('fields', action='append', help='A field (key/value) of the data point')
point_parser.add_argument('token', type=str, required=True, help='The authentication token')

# get the users list from a file
with open(API_USERS_LIST, 'r') as f:
    users = json.load(f)

# This is a decorator to request authentications on some actions
def authenticate(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):

        # check the token is in the list
        req_args = request.json
        if req_args['token'] is None:
            abort(403, message="Authentication token is required for access.")
        elif req_args['token'] not in users:
            abort(403, message="Token {} doesn't exist".format(req_args['token']))

	# access granted!
        return func(*args, **kwargs)

    return func_wrapper

    
class ListSeries(Resource):

    def get(self):
        q = es_dsl.Search(using=es).index(API_INDEX_SERIES).query('match_all')
        series_count = q.count()
        res = q[0:series_count].execute()
        response = {}
        for hit in res.hits.hits:
            info = hit['_source']
            try:
                token = info.pop('token')
                info['user'] = users[token]['name']
            except:
                pass
            s = es_dsl.Search(using=es).index(API_INDEX_POINT).query('match', series_id=hit['_id'])
            info['count'] = s.count()
            response[hit['_id']] = info
        return response


class Series(Resource):

    method_decorators = { 'put' : [authenticate], 'delete' : [authenticate] }

    def get(self, series_id):
        q = es_dsl.Search(using=es).index(API_INDEX_POINT).sort('timestamp').query('match', series_id=series_id)
        count = q.count()
        res = q[0:count].execute()
        response = [hit.to_dict() for hit in res]
        return response

    def delete(self, series_id):
        try:
            res = es.get(index=API_INDEX_SERIES, doc_type=API_TYPE_SERIES, id=series_id)
            return '', 204
        except elasticsearch.exceptions.NotFoundError:
            abort(404, message="Point {} doesn't exist".format(point_id))

    def put(self, series_id):
        if series_id != 'new':
            abort(404, message="For now only 'new' resource is available for PUT request")

        args = series_parser.parse_args()

        args.pop

        # add data in elasticsearch
        args['timestamp'] = datetime.datetime.now()
        res = es.index(index=API_INDEX_SERIES, doc_type=API_TYPE_SERIES, body=args)
        return res['_id'], 201


class Point(Resource):

    method_decorators = { 'put' : [authenticate], 'delete' : [authenticate] }

    def get(self, point_id):
        try:
            res = es.get(index=API_INDEX_POINT, doc_type=API_TYPE_POINT, id=point_id)
            return res['_source']
        except elasticsearch.exceptions.NotFoundError:
            abort(404, message="Point {} doesn't exist".format(point_id))

    def delete(self, point_id):
        try:
            res = es.get(index=API_INDEX_POINT, doc_type=API_TYPE_POINT, id=point_id)
            return '', 204
        except elasticsearch.exceptions.NotFoundError:
            abort(404, message="Point {} doesn't exist".format(point_id))

    def put(self, point_id):
        if point_id != 'new':
            abort(404, message="For now only 'new' resource is available for PUT request")

        args = request.json

        # remove token from the document
        token = args['token']
        args.pop('token')

        # add data in elasticsearch
        args['timestamp'] = datetime.datetime.now()
        res = es.index(index=API_INDEX_POINT, doc_type=API_TYPE_POINT, body=args)
        return res['_id'], 201

class PointCount(Resource):

    def get(self):
        s = es_dsl.Search(using=es).index(API_INDEX_POINT).query('match_all')
        return s.count(), 201

api.add_resource(ListSeries, '/series')
api.add_resource(Series, '/series/<series_id>')
api.add_resource(Point, '/point/<point_id>')
api.add_resource(PointCount, '/points/count')

if __name__ == '__main__':
    app.run(debug=True)
