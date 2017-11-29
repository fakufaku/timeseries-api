from flask import Flask
from flask_restful import Resource, Api, reqparse, abort
import datetime
import json
import elasticsearch as elasticsearch

es = elasticsearch.Elasticsearch()

API_INDEX = 'timeseries-api'
API_USERS_LIST = '/etc/timeseries-api/users.json'

app = Flask(__name__)
api = Api(app)


point_parser = reqparse.RequestParser()
point_parser.add_argument('token', type=str, help='The authentication token')
point_parser.add_argument('series_id', type=str, 
                       help='The session identification number produced by the device')
point_parser.add_argument('value', help='The value of the measurement')
point_parser.add_argument('unit', type=str, help='The unit of the measurement')

# get the users list from a file
with open(API_USERS_LIST, 'r') as f:
    users = json.load(f)
print(users)

class Series(Resource):
    def get(self, series_id):
        return {'series_id' : series_id}

class Point(Resource):
    def get(self, point_id):
        try:
            res = es.get(index=API_INDEX, doc_type='point', id=point_id)
            return res['_source']
        except elasticsearch.exceptions.NotFoundError:
            abort(404, message="Point {} doesn't exist".format(point_id))

    def delete(self, point_id):
        try:
            res = es.get(index=API_INDEX, doc_type='point', id=point_id)
            return '', 204
        except elasticsearch.exceptions.NotFoundError:
            abort(404, message="Point {} doesn't exist".format(point_id))

    def put(self, point_id):
        args = point_parser.parse_args(strict=True)

        # authentify user
        token = args['token']
        if token not in users:
            abort(404, message="Token {} doesn't exist".format(token))
        args.pop('token')

        # add data in elasticsearch
        args['user_id'] = users[token]['id']
        args['timestamp'] = datetime.datetime.now()
        res = es.index(index=API_INDEX, doc_type='point', body=args)
        return res['_id'], 201

api.add_resource(Point, '/point/<point_id>')
api.add_resource(Series, '/series/<series_id>')

if __name__ == '__main__':
    app.run(debug=True)
