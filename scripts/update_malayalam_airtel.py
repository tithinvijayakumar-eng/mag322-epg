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
    ('Asianet HD', 'LIVETV_LIVETVCHANNEL_ASIANET_HD', 'ts292'),
    ('Asianet Plus', 'LIVETV_LIVETVCHANNEL_ASIANET_PLUS', 'AsianetPlus.in'),
    ('Asianet Movies HD', 'LIVETV_LIVETVCHANNEL_ASIANET_MOVIES_HD', 'AsianetMovies.in'),
    ('Zee Keralam HD', 'LIVETV_LIVETVCHANNEL_ZEE_KERALAM_HD', 'ts694'),
    ('Mazhavil Manorama HD', 'LIVETV_LIVETVCHANNEL_MAZHAVIL_MANORAMA_HD', 'mazhavilmanoramahd.in'),
    ('Flowers TV', 'LIVETV_LIVETVCHANNEL_FLOWERS_TV', 'flowers.in'),
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
    req = urllib.request.Request(
        'https://epg.airtel.tv/app/v2/content/channel/epg?' + params,
        headers=HEADERS,
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    pg = data.get('programGuide') or {}
    out = []
    for values in pg.values():
        if isinstance(values, list):
            out.extend(values)
    return out

def xmltv_time(ms):
    dt = datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).astimezone(IST)
    return dt.strftime('%Y%m%d%H%M%S +0530')

def make_node(item, mag_id):
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
    updated = 0

    for name, airtel_id, mag_id in CHANNELS:
        try:
            programs = fetch_airtel(airtel_id)
            nodes = []
            for item in sorted(programs, key=lambda x: int(x.get('startTime', 0))):
                node = make_node(item, mag_id)
                if node is not None:
                    nodes.append(node)
            if not nodes:
                print(f'SKIP {name}: no valid Airtel EPG')
                continue
            for p in list(root.findall('programme')):
                if p.get('channel') == mag_id:
                    root.remove(p)
            for node in nodes:
                root.append(node)
            updated += 1
            print(f'Updated {name}: {len(nodes)} entries')
        except Exception as e:
            print(f'SKIP {name}: {e}')

    if updated == 0:
        raise RuntimeError('No Malayalam channels updated')

    ET.indent(tree, space='  ')
    tree.write(XML_PATH, encoding='utf-8', xml_declaration=True)
    print(f'Updated {updated} Malayalam channels')

if __name__ == '__main__':
    main()
