Python Timeseries Viewer
========================

This is a simple CLI tool that lets you inspect all the series in the API
and plot them. The tool uses [matplotlib]() and [pandas]().

Quickstart
----------

Help is available

    > python api_access.py --help
    usage: api_access.py [-h] {list,plot} ...

    positional arguments:
      {list,plot}  sub-command help
        list       List all the series available
        plot       Plot a time series

    optional arguments:
      -h, --help   show this help message and exit

List all the series

    > python api_access.py list
    |   9                      | A test series                            | 2017-12-04 02:13 |     0 |
    |   17                     | A test series                            | 2017-12-04 02:21 |     1 |
    |   2                      | A test series                            | 2017-12-04 16:44 |     1 |
    |   10                     | Temperature with a DS18B20 probe.        | 2017-12-04 17:09 |     2 |
    |   12                     | Temperature with a DS18B20 probe.        | 2017-12-04 17:09 |   400 |
    |   18                     | Temperature with a DS18B20 probe.        | 2017-12-04 17:17 |     1 |
    |   3                      | Temperature with a DS18B20 probe.        | 2017-12-04 17:18 |    21 |
    |   21                     | Temperature with a DS18B20 probe.        | 2017-12-04 18:35 | 15856 |
    |   14                     | Temperature with a DS18B20 probe.        | 2017-12-04 18:36 |  1721 |
    |   13                     | Temperature with a DS18B20 probe.        | 2017-12-04 18:41 |    36 |
    |   15                     | Temperature with a DS18B20 probe.        | 2017-12-05 16:02 |    57 |

with the columns being `index`, `Description`, `Creation date`, `number of
points`.

Plot one of the series

    > python api_access.py plot 21

