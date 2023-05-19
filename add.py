#!/usr/bin/python3
import urllib.parse
import yaml
with open('./shows.yml', 'r') as f:
    shows = yaml.safe_load(f.read())

name = input('Enter Series Name: ')
index = input('Enter Index (default tgx): ')
index = 'tgx' if index == '' else index
query_default = urllib.parse.quote_plus(f'{name} 1080p') + "&lang=0&nox=2&sort=name&sort=seeders&order=desc"
print('\nDefault search query is')
print(query_default)

query = input('\nEnter query: ')
query = query_default if query == '' else query

episodes = int(input('Enter episodes count: '))
schedule = int(input('Enter episodes schedule: '))

show_id = int(max(list(map(lambda x: int(x), list(shows.keys()))))) +1
shows[show_id] = {'name': name, 'index': index, 'search': query, 'episodes': episodes, 'schedule': schedule}

with open('./shows.yml', 'w') as f:
    yaml.safe_dump(shows, f)
