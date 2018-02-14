from flask import Flask, request
from flask_restful import Resource, Api, reqparse, abort
import datetime
import json
import ast
from functools import wraps
import dataset

DB_FILE = 'sqlite:////var/www/api/api_db.sqlite'
db = dataset.connect(DB_FILE)

api_table_series = db['timeseries-api-series']
api_table_points = db['timeseries-api-points']

API_USERS_LIST = '/etc/timeseries-api/users.json'

app = Flask(__name__)
api = Api(app)

series_parser = reqparse.RequestParser()
series_parser.add_argument('token', type=str, required=True, help='The authentication token')
series_parser.add_argument('device_id', required=True, type=str, help='Some kind of device ID')
series_parser.add_argument('device_desc', required=True, type=str, help='Some kind of device ID')
series_parser.add_argument('desc', type=str, help='A description of the series')

point_parser = reqparse.RequestParser()
point_parser.add_argument('series_id', type=int, required=True,
                       help='The session identification number produced by the device')
point_parser.add_argument('fields', action='str', help='A field (key/value) of the data point')
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
        series = api_table_series.all()
        response = {}
        for hit in series:
            try:
                token = hit.pop('token')
                hit['user'] = users[token]['name']
            except:
                pass
            # convert date to ISO 8601 string
            hit['timestamp'] = hit['timestamp'].isoformat()
            # get the number of points in the series
            hit['count'] = api_table_points.count('series_id=' + str(hit['id']))
            response[hit['id']] = hit
        return response, 200


class Series(Resource):

    method_decorators = { 'put' : [authenticate], 'delete' : [authenticate] }

    def get(self, series_id):

        # check the series exists
        series_info = api_table_series.find_one(id=int(series_id))
        if series_info is None:
            abort(404, message="Series {} doesn't exist".format(series_id))

        # get all the points from the DB
        points = api_table_points.find(
                series_id=int(series_id),
                order_by='timestamp',
                )

        # format list of results
        results = []
        for point in points:
            # convert date to ISO8601 string
            point['timestamp'] = point['timestamp'].isoformat()
            # un-stringify the json
            point['fields'] = json.loads(point['fields'])
            results.append(point)

        return results, 200

    def delete(self, series_id):
        db.begin()
        try:
            api_table_points.delete(series_id=int(series_id))
            api_table_series.delete(id=int(series_id))
            db.commit()
            return '', 204
        except:
            db.rollback()
            abort(500, message="Something happend while querying the database.")

    def put(self, series_id):
        if series_id != 'new':
            abort(404, message="For now only 'new' resource is available for PUT request")

        args = series_parser.parse_args()

        # add data in elasticsearch
        args['timestamp'] = datetime.datetime.now()

        db.begin()
        try:
            series_id = api_table_series.insert(args)
            db.commit()
            return series_id, 201
        except:
            db.rollback()
            abort(500, message="Something happend while inserting in the database.")


class Point(Resource):

    method_decorators = { 'put' : [authenticate], 'delete' : [authenticate] }

    def get(self, point_id):
        res = api_table_points.find_one(id=int(point_id))
        if res is not None:
            res['fields'] = json.loads(res['fields'])
            res['timestamp'] = res['timestamp'].isoformat()
            return res, 200
        else:
            abort(404, message="Point {} doesn't exist".format(point_id))

    def delete(self, point_id):
        db.begin()
        try:
            api_table_points.delete(id=int(point_id))
            db.commit()
            return '', 204
        except:
            db.rollback()
            abort(500, message="Something happend while querying the database.")

    def put(self, point_id):
        if point_id != 'new':
            abort(404, message="For now only 'new' resource is available for PUT request")

        args = point_parser.parse_args()

        # check if series exists
        series_info = api_table_series.find_one(id=int(args['series_id']))
        if series_info is None:
            abort(404, message="Series {} not found".format(args['series_id']))

        # check the token is the same for the series
        if series_info['token'] != args['token']:
            abort(403, message="Permission denied")

        # remove token from the document
        token = args.pop('token')

        # stringify the json
        args['fields'] = json.dumps(args['fields'])

        # add timestamp
        args['timestamp'] = datetime.datetime.now()

        print(args)

        db.begin()
        try:
            point_id = api_table_points.insert(args)
            db.commit()
            return point_id, 201
        except:
            db.rollback()
            abort(500, message="Something happend while inserting in the database.")

class PointCount(Resource):

    def get(self):
        count = api_table_points.count()
        return count, 200

api.add_resource(ListSeries, '/series')
api.add_resource(Series, '/series/<series_id>')
api.add_resource(Point, '/point/<point_id>')
api.add_resource(PointCount, '/points/count')

if __name__ == '__main__':
    app.run(debug=True)
