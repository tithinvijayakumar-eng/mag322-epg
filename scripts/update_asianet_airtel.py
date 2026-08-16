#!/usr/bin/env python3
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

XML_PATH = Path('MAG322_5CH_EXTERNAL_EPG_TEST.xml')
IST = timezone(timedelta(hours=5, minutes=30))

CHANNELS = [
    {
        'name': 'Asianet HD',
        'airtel_id': 'LIVETV_LIVETVCHANNEL_ASIANET_HD',
        'mag_id': 'ts292',
    },
    {
        'name': 'Mazhavil Manorama HD',
        'airtel_id': 'LIVETV_LIVETVCHANNEL_MAZHAVIL_MANORAMA_HD',
        'mag_id': 'mazhavilmanoramahd.in',
    },
    {
        'name': 'Flowers TV',
        'airtel_id': 'LIVETV_LIVETVCHANNEL_FLOWERS_TV',
        'mag_id': 'flowers.in',
    },
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/143 Safari/537.36',
    'Referer': 'https://www.airtelxstream.in/',
    'Accept': 'application/json,text/plain,*/*',
}

def fetch_airtel(channel_id):
    now = datetime.now(IST)
    start = datetime(now.year, now.month, now.day, tzinfo=IST) - timedelta(days=1)
    end = start + timedelta(days=4)
    params = urllib.parse.urlencode({
        'channelId': channel_id,
        'startTime': int(start.timestamp() * 1000),
        'endTime': int(end.timestamp() * 1000),
    })
    url = 'https://epg.airtel.tv/app/v2/content/channel/epg?' + params
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    pg = data.get('programGuide') or {}
    programs = []
    for values in pg.values():
        if isinstance(values, list):
            programs.extend(values)
    if not programs:
        raise RuntimeError(f'Airtel returned no programmes for {channel_id}')
    return programs

def xmltv_time(ms):
    d = datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).astimezone(IST)
    return d.strftime('%Y%m%d%H%M%S +0530')

def build_programme(item, mag_id):
    start = item.get('startTime')
    stop = item.get('endTime')
    title = (item.get('title') or '').strip()
    if not start or not stop or not title:
        return None
    p = ET.Element('programme', {
        'start': xmltv_time(start),
        'stop': xmltv_time(stop),
        'channel': mag_id,
    })
    ET.SubElement(p, 'title').text = title
    desc = (item.get('desc') or '').strip()
    if desc:
        ET.SubElement(p, 'desc').text = desc
    return p

def main():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    updates = []

    for cfg in CHANNELS:
        try:
            programs = fetch_airtel(cfg['airtel_id'])
            new_nodes = []
            for item in sorted(programs, key=lambda x: int(x.get('startTime', 0))):
                node = build_programme(item, cfg['mag_id'])
                if node is not None:
                    new_nodes.append(node)
            if not new_nodes:
                print(f"SKIP {cfg['name']}: no valid programme entries parsed")
                continue

            for p in list(root.findall('programme')):
                if p.get('channel') == cfg['mag_id']:
                    root.remove(p)
            for node in new_nodes:
                root.append(node)

            updates.append((cfg['name'], len(new_nodes)))
            print(f"Updated {cfg['name']} from Airtel: {len(new_nodes)} programme entries")
        except Exception as e:
            print(f"SKIP {cfg['name']}: {e}")

    if not updates:
        raise RuntimeError('No channels updated; existing XML left unchanged')

    ET.indent(tree, space='  ')
    tree.write(XML_PATH, encoding='utf-8', xml_declaration=True)
    print('Updated channels:', ', '.join(f'{name}={count}' for name, count in updates))

if __name__ == '__main__':
    main()
