#!/usr/bin/env python3
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

XML_PATH = Path('MAG322_5CH_EXTERNAL_EPG_TEST.xml')
IST = timezone(timedelta(hours=5, minutes=30))
UAE = timezone(timedelta(hours=4))

# name, provider, provider channel id, MAG322 XMLTV id
CHANNELS = [
    ('Asianet HD', 'airtel', 'LIVETV_LIVETVCHANNEL_ASIANET_HD', 'ts292'),
    ('Asianet Plus', 'airtel', 'LIVETV_LIVETVCHANNEL_ASIANET_PLUS', 'AsianetPlus.in'),
    ('Asianet Movies HD', 'airtel', 'LIVETV_LIVETVCHANNEL_ASIANET_MOVIES_HD', 'AsianetMovies.in'),
    ('Surya TV HD', 'airtel', 'LIVETV_LIVETVCHANNEL_SURYA_HD', 'SURYA.HD.in'),
    ('Surya Movies', 'airtel', 'LIVETV_LIVETVCHANNEL_SURYA_MOVIES', 'SURYA.MOVIES.in'),
    ('Surya Comedy', 'airtel', 'LIVETV_LIVETVCHANNEL_SURYA_COMEDY', 'SURYA.COMEDY.in'),
    ('Surya Music', 'airtel', 'LIVETV_LIVETVCHANNEL_SURYA_MUSIC', 'SURYA.MUSIC.in'),
    ('Zee Keralam HD', 'airtel', 'LIVETV_LIVETVCHANNEL_ZEE_KERALAM_HD', 'ts694'),
    ('Mazhavil Manorama HD', 'airtel', 'LIVETV_LIVETVCHANNEL_MAZHAVIL_MANORAMA_HD', 'mazhavilmanoramahd.in'),
    ('Flowers TV', 'airtel', 'LIVETV_LIVETVCHANNEL_FLOWERS_TV', 'flowers.in'),
    ('Kairali TV', 'airtel', 'LIVETV_LIVETVCHANNEL_KAIRALI_TV', 'ts25'),
    ('Kairali WE', 'airtel', 'LIVETV_LIVETVCHANNEL_KAIRALI_WE', 'Kairali.WE.TV.in'),
    ('Amrita TV', 'tataplay', '178', 'AMRITA.in'),
    ('Safari TV', 'airtel', 'LIVETV_LIVETVCHANNEL_SAFARI_TV', 'SAFARI.TV.in'),
    ('Kochu TV', 'airtel', 'LIVETV_LIVETVCHANNEL_KOCHU_TV', 'KOCHU.TV.in'),
    ('24 News', 'airtel', 'LIVETV_LIVETVCHANNEL_TWENTY_FOUR', 'News.24.in'),
    ('Jeevan TV HD', 'tataplay', '1848', 'jeevantv.in'),
    ('Kaumudy TV HD', 'tataplay', '1851', 'kaumudytv.in'),
    ('Raj News Malayalam HD', 'tataplay', '1853', 'rajnewsmalayalam.in'),
    ('Shekinah TV', 'tataplay', '1856', 'ts1313'),
    ('News Malayalam 24x7 HD', 'tataplay', '1857', 'ts1367'),
    ('Raj Music Malayalam', 'tataplay', '1877', 'rajmusixmalayalam.in'),
]

AIRTEL_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/143 Safari/537.36',
    'Referer': 'https://www.airtelxstream.in/',
    'Accept': 'application/json,text/plain,*/*',
}

TATAPLAY_HEADERS = {
    'Accept': '*/*',
    'Origin': 'https://watch.tataplay.com',
    'Referer': 'https://watch.tataplay.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/143 Safari/537.36',
    'Content-Type': 'application/json',
    'locale': 'ENG',
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
        headers=AIRTEL_HEADERS,
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    pg = data.get('programGuide') or {}
    out = []
    for values in pg.values():
        if isinstance(values, list):
            out.extend(values)
    return out


def fetch_tataplay(channel_id):
    now = datetime.now(IST)
    out = []
    for offset in (-1, 0, 1, 2):
        day = now + timedelta(days=offset)
        date_text = day.strftime('%d-%m-%Y')
        url = (
            'https://tm.tapi.videoready.tv/content-detail/pub/api/v2/'
            f'channels/schedule?date={date_text}'
        )
        body = json.dumps({'id': channel_id}).encode('utf-8')
        req = urllib.request.Request(url, data=body, headers=TATAPLAY_HEADERS, method='POST')
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        epg = ((data.get('data') or {}).get('epg') or [])
        for item in epg:
            out.append({
                'title': item.get('title'),
                'desc': item.get('desc'),
                'startTime': item.get('startTime'),
                'endTime': item.get('endTime'),
            })
    return out


def parse_time(value):
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value) / 1000, tz=timezone.utc).astimezone(IST)
    if isinstance(value, str):
        text = value.strip()
        if text.endswith('Z'):
            text = text[:-1] + '+00:00'
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IST)
        return dt.astimezone(IST)
    raise ValueError('unsupported time value')


def xmltv_time(value):
    # Preserve the programme instant, but serialize XMLTV timestamps in UAE time.
    return parse_time(value).astimezone(UAE).strftime('%Y%m%d%H%M%S +0400')


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


def ensure_channel(root, name, mag_id):
    for ch in root.findall('channel'):
        if ch.get('id') == mag_id:
            return
    ch = ET.Element('channel', {'id': mag_id})
    ET.SubElement(ch, 'display-name').text = name
    first_programme = root.find('programme')
    if first_programme is None:
        root.append(ch)
    else:
        root.insert(list(root).index(first_programme), ch)
    print(f'Added channel declaration: {name} ({mag_id})')


def main():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    updated = 0

    for name, provider, provider_id, mag_id in CHANNELS:
        try:
            if provider == 'airtel':
                programs = fetch_airtel(provider_id)
            elif provider == 'tataplay':
                programs = fetch_tataplay(provider_id)
            else:
                raise ValueError(f'unknown provider: {provider}')

            nodes = []
            for item in sorted(programs, key=lambda x: parse_time(x.get('startTime'))):
                node = make_node(item, mag_id)
                if node is not None:
                    nodes.append(node)
            if not nodes:
                print(f'SKIP {name}: no valid {provider} EPG')
                continue

            ensure_channel(root, name, mag_id)

            for p in list(root.findall('programme')):
                if p.get('channel') == mag_id:
                    root.remove(p)
            for node in nodes:
                root.append(node)
            updated += 1
            print(f'Updated {name} from {provider}: {len(nodes)} entries')
        except Exception as e:
            print(f'SKIP {name}: {e}')

    if updated == 0:
        raise RuntimeError('No Malayalam channels updated')

    ET.indent(tree, space='  ')
    tree.write(XML_PATH, encoding='utf-8', xml_declaration=True)
    print(f'Updated {updated} Malayalam channels')


if __name__ == '__main__':
    main()
