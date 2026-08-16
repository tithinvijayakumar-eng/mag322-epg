#!/usr/bin/env python3
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

XML_PATH = Path('MAG322_5CH_EXTERNAL_EPG_TEST.xml')
AIR_ID = 'LIVETV_LIVETVCHANNEL_ASIANET_HD'
MAG_ID = 'ts292'
IST = timezone(timedelta(hours=5, minutes=30))

def fetch_airtel():
    now = datetime.now(IST)
    start = datetime(now.year, now.month, now.day, tzinfo=IST) - timedelta(days=1)
    end = start + timedelta(days=4)
    params = urllib.parse.urlencode({
        'channelId': AIR_ID,
        'startTime': int(start.timestamp() * 1000),
        'endTime': int(end.timestamp() * 1000),
    })
    url = 'https://epg.airtel.tv/app/v2/content/channel/epg?' + params
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/143 Safari/537.36',
        'Referer': 'https://www.airtelxstream.in/',
        'Accept': 'application/json,text/plain,*/*',
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    pg = data.get('programGuide') or {}
    programs=[]
    for values in pg.values():
        if isinstance(values,list):
            programs.extend(values)
    if not programs:
        raise RuntimeError('Airtel returned no Asianet programmes; existing XML left unchanged')
    return programs

def xmltv_time(ms):
    d=datetime.fromtimestamp(int(ms)/1000,tz=timezone.utc).astimezone(IST)
    return d.strftime('%Y%m%d%H%M%S +0530')

def main():
    programs=fetch_airtel()
    tree=ET.parse(XML_PATH)
    root=tree.getroot()
    for p in list(root.findall('programme')):
        if p.get('channel')==MAG_ID:
            root.remove(p)
    added=0
    for item in sorted(programs,key=lambda x:int(x.get('startTime',0))):
        start=item.get('startTime'); stop=item.get('endTime'); title=(item.get('title') or '').strip()
        if not start or not stop or not title: continue
        p=ET.SubElement(root,'programme',{'start':xmltv_time(start),'stop':xmltv_time(stop),'channel':MAG_ID})
        ET.SubElement(p,'title').text=title
        desc=(item.get('desc') or '').strip()
        if desc: ET.SubElement(p,'desc').text=desc
        added+=1
    if not added:
        raise RuntimeError('No valid Asianet programmes parsed; existing XML left unchanged')
    ET.indent(tree,space='  ')
    tree.write(XML_PATH,encoding='utf-8',xml_declaration=True)
    print(f'Updated Asianet from Airtel: {added} programme entries')

if __name__=='__main__': main()
