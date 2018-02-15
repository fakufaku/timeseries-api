Timeseries API
==============

A dead simple API to store time-series collected by IoT devices such as the
ESP8266 or the ESP32.

Based on [flask](http://flask.pocoo.org/),
[flask-restful](https://flask-restful.readthedocs.io/en/latest/), and
[dataset](https://dataset.readthedocs.io/en/latest/index.html).

Endpoints
---------

* `/series` (GET) gets all series metadata
* `/series/new` (PUT) creates a new series
* `/series/<series_id>` (GET) gets all the points in one series
* `/series/<series_id>` (DELETE) deletes a series and all the points associated
* `/point/new` (PUT) Creates new point
* `/point/<point_id>` (GET) Display a point
* `/point/<point_id>` (DELETE) Delete a point

### Authentification

All PUT and DELETE endpoints need to be authentified. GET endpoints are not
authentified.

The authentification is designed for (very) small scale operations. The list of
users is maintained as a JSON file stored at `/etc/timeseries-api/users.json`
with the following structure.

    {
      "this-is-a-long-string-used-as-a-token" : {
        "name" : "Robin",
          "id" : 1
      }
    }

The file is intended to be maintained manually.

Example
-------

    import requests, time

    # The URL of the server running the api
    url = 'https://www.mydatadump.org/api'

    # The authentication token
    # This can be stored in a file for example
    auth_token = 'my-secret-authentication-token'

    new_series = {
            'desc': 'Temperature in Tokyo',
            'device_desc': 'ESP32 with DS18B20 temperature sensor',
            'device_id': '12:AB:CD:XY:ZU:57',
            'token' : auth_token,
            }

    new_points = [
            { 'fields': {'temp_C': 13}, },
            { 'fields': {'temp_C': 13.5}, },
            { 'fields': {'temp_C': 12.5}, },
            ]

    # Create a new timeseries. The creation timestamp is done server side
    ret = requests.put(url + '/series/new', json=new_series)

    if ret.ok:
        series_id = ret.json()
    else:
        raise ValueError('{} {}'.format(ret.status_code, ret.text))

    # Now add some points to the series
    for point in new_points:
        # add authentication token
        point['token'] = auth_token

        # add the series_id
        point['series_id'] = series_id

        ret = requests.put(url + '/point/new', json=point)

        if not ret.ok:
            raise ValueError('{} {}'.format(ret.status_code, ret.text))

        # The points are also timestamped server side
        time.sleep(5)

    # Now we can get the data
    # No authentication required for that
    ret = requests.get(url + '/series/' + str(series_id))
    data = ret.json()
    print(data)


Server Configuration
--------------------

The full configuration of the Apache2 server is beyond the scope
of this doc, but here are a few pointers to get started.

I use Apache2 with WSGI and followed the instructions in the [Flask
doc](http://flask.pocoo.org/docs/0.12/deploying/mod_wsgi/) to get going.

The authentification relies on secret tokens that should be transmitted with
the data. This means that it is essential to use an SSL encrypted connection.
I used [Let's encrypt](https://letsencrypt.org/) to get a free and official SSL
certificate. I used the automatic `certbot from EFF to install it and even
setup automatic renewal. They have very good
[instructions](https://certbot.eff.org/).

Here is the apache site configuration file I am using
`/etc/apache2/sites-available/api.conf` for my website
`data.robinscheibler.org`. I configured it so that all requests to port 80 are
automatically redirected to 443 to avoid any problems.

    <VirtualHost *:80>
        ServerName data.robinscheibler.org

        WSGIDaemonProcess api user=www-data group=www-data threads=5
        WSGIScriptAlias /api /var/www/api/api.wsgi

        <Directory /var/www/api>
            WSGIProcessGroup api
            WSGIApplicationGroup %{GLOBAL}
            Require all granted
        </Directory>

        RewriteEngine on
        RewriteCond %{SERVER_NAME} =data.robinscheibler.org
        RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
    </VirtualHost>

    <IfModule mod_ssl.c>
    <VirtualHost *:443>
        ServerName data.robinscheibler.org

        WSGIScriptAlias /api /var/www/api/api.wsgi

        <Directory /var/www/api>
            WSGIProcessGroup api
            WSGIApplicationGroup %{GLOBAL}
            Require all granted
        </Directory>
        SSLCertificateFile /etc/letsencrypt/live/data.robinscheibler.org/fullchain.pem
        SSLCertificateKeyFile /etc/letsencrypt/live/data.robinscheibler.org/privkey.pem
        Include /etc/letsencrypt/options-ssl-apache.conf
    </VirtualHost>
    </IfModule>

API root folder permission
--------------------------

The apache user needs to be able to read/write the database file for correct operation.
Once the file has been created, for example by runnint `tests/test_api.py`

    chown -R www-data:www-data /var/www/api
    chmod -R u+w /var/www/api
