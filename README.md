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

Examples
--------

TBA

Authentification
----------------

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
