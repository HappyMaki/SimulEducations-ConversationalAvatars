#!/usr/bin/env python

from __future__ import print_function
import httplib2
import os

from apiclient import discovery


def main(key=None):
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build(
        'sheets',
        'v4',
        http=httplib2.Http(),
        discoveryServiceUrl=discoveryUrl,
        developerKey=key)

    spreadsheetId = '116V404HIRTdtGVC155SAqmo9-T6mG-ELbdIFU_6Q5Qg'
    rangeName = 'Class Data!A2:E'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        print('Name, Major:')
        for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
            print('%s, %s' % (row[0], row[4]))


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        main(key="AIzaSyD1n_p8lQh8zBk30-mF_Q6xgyXEYCjMKVs")
    else:
        main(key="AIzaSyD1n_p8lQh8zBk30-mF_Q6xgyXEYCjMKVs")