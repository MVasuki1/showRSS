import os
import requests
import subprocess
import pytz
from datetime import datetime

date_format = "%a, %d %b %Y %H:%M:%S %z"
today = datetime.now(pytz.utc)
shows = []
for i in range(1,100):
    os.system('rm out.html')
    try:
        _ = subprocess.check_output(f'wget -cq -O out.html https://showrss.info/show/{i}.rss', shell=True).decode().strip()
    except:
        continue
    
    pub_date = subprocess.check_output('cat out.html | grep -oP "(?<=<pubDate>).*?(?=</pub)" | head -n 1', shell=True).decode().strip()
    
    parsed_datetime = datetime.strptime(pub_date, date_format)
    print(i, " " ,(today - parsed_datetime).days)
    if (today - parsed_datetime).days < 7:
        shows.append(f'https://showrss.info/browse/{i}')

for show in shows:
    print(show)
