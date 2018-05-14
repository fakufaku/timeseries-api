
import argparse
import requests

URL_API = 'https://data.robinscheibler.org/api'

'''
TODO
----

API:
    Add endpoints:
        /series/<series_id>/fields -> return all fields
        /series/<series_id>/count  -> return the count

    Update endpoint
        /series/<series_id> so that it deletes all the datapoints too

    Add some arguments to the get command to limit the entries returned (number of dates, start, end, etc)
'''

def main_list(args):

    from dateutil.parser import parse as parse_date

    r = requests.get(URL_API + '/series')

    if not r.ok:
        raise ValueError('The request failed with code:', r.status_code)

    series = []
    for ID, info in r.json().items():
        date = parse_date(info['timestamp'])
        info['date'] = date.strftime('%Y-%m-%d %H:%M')
        info['id'] = ID
        series.append(info)

    # sort to get most recent at bottom
    for info in sorted(series, key=lambda x : x['date']):
        print('|   {id:<20}   | {desc:<40.40} | {date:16} | {count:5d} |'.format(**info))

def main_plot(args):

    import pandas as pd
    import matplotlib.pyplot as plt
    from dateutil.parser import parse as parse_date

    r = requests.get(URL_API + '/series/' + args.series_id)

    if not r.ok:
        raise ValueError('The request failed with code:', r.status_code)

    points = r.json()

    # get all the fields
    field_labels = set()
    for point in points:
        for field_name in point['fields'].keys():
            field_labels.add(field_name)

    # Now reorganize in a structure that can be ingested in a dataframe
    dates = []
    fields = {}
    for label in field_labels:
        fields[label] = []

    for point in points:
        dates.append(parse_date(point['timestamp']))
        for label in field_labels:
            if label in point['fields']:
                fields[label].append(point['fields'][label])
            else:
                fields[label].append(None)

    # Create the dataframe and plot the time series
    df = pd.DataFrame(data=fields, index=dates)
    df.plot()
    plt.show()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help')

    parser_list = subparsers.add_parser('list', help='List all the series available')
    parser_list.set_defaults(func=main_list)

    parser_plot = subparsers.add_parser('plot', help='Plot a time series')
    parser_plot.add_argument('series_id', type=str, help='The ID of the time series.')
    parser_plot.set_defaults(func=main_plot)

    args = parser.parse_args()
    args.func(args)
