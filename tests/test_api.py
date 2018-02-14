import requests, datetime, json

api_url = 'http://127.0.0.1:5000'
API_USERS_LIST = '/etc/timeseries-api/users.json'

# get the users list from a file
with open(API_USERS_LIST, 'r') as f:
    users = json.load(f)

token, user = users.popitem()

auth = {'token': token}

new_series = {
        'desc': 'A test series',
        'device_desc': 'Test script',
        'device_id': '12:AB:CD:XY:ZU:57',
        'timestamp': datetime.datetime.now().isoformat(),
        'token' : token,
        }

new_points = [
        { 'fields': {"temp_C": 1}, },
        { 'fields': {"temp_C": 2}, },
        { 'fields': {"temp_C": 3}, },
        ]

def test_series(url=None):

    if url is None:
        url = api_url

    # test insertion
    r = requests.put(url + '/series/new', json=new_series)
    assert r.ok
    assert r.status_code == 201

    # get the new created series id
    series_id = r.json()
    assert type(series_id) == int

    print('* New series created with id', series_id)

    # get the list and ensure it is there
    r = requests.get(url + '/series')
    assert r.ok
    series_list = r.json()
    assert str(series_id) in series_list

    print('* New series is in the list of series')



    # Now add a few points
    new_points_id = []
    for point in new_points:
        # add series id and token for authentification
        point['series_id'] = series_id
        point.update(auth)

        # send req
        r = requests.put(url + '/point/new', json=point)

        # check
        assert r.ok
        assert r.status_code == 201
        point_id = r.json()

        # report
        print('  # Successfully created point with id', point_id)
        new_points_id.append(point_id)

    # And there should be three points in the list
    r = requests.get(url + '/series/' + str(series_id))
    assert r.ok
    assert r.status_code == 200
    assert len(r.json()) == len(new_points)
    print('* Series has expected number of points')

    # try to get one of the points
    r = requests.get(url + '/point/' + str(new_points_id[0]))
    assert r.ok
    assert r.status_code == 200
    print('* Successfully get back a single point', new_points_id[0])

    # try to delete this point
    r = requests.delete(url + '/point/' + str(new_points_id[0]), json=auth)
    assert r.ok
    assert r.status_code == 204
    print('* Successfully deleted that point', new_points_id[0])

    # we should get a 404 now
    r = requests.get(url + '/point/' + str(new_points_id[0]))
    assert r.status_code == 404
    print('* Point is now missing now, good')

    # And there should be two points in the list
    r = requests.get(url + '/series/' + str(series_id))
    assert r.ok
    assert r.status_code == 200
    assert len(r.json()) == len(new_points) - 1
    print('* Series has one less point, good')


    # try to delete the new series
    r = requests.delete(url + '/series/' + str(series_id), json=auth)
    assert r.ok
    assert r.status_code == 204

    print('* Successfully deleted series', series_id)

    # check the id is not in the list anymore
    r = requests.get(url + '/series')
    assert r.ok
    series_list = r.json()
    assert str(series_id) not in series_list

    print('* It is not in the list anymore')
    
    # And there should be two points in the list
    r = requests.get(url + '/series/' + str(series_id))
    assert r.status_code == 404
    print('* Series is now missing, good')
    


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='Test the API operations')
    parser.add_argument('--url', type=str, help='An alternative url for the API')

    test_series()
