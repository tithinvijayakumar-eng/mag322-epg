#!/usr/bin/env python3
import copy
import gzip
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

XML_PATH = Path('MAG322_5CH_EXTERNAL_EPG_TEST.xml')
BASE_URL = 'https://epgshare01.online/epgshare01/epg_ripper_{tag}.xml.gz'
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Playlist channel name, EPGShare feed tag, XMLTV id used by the MAG playlist.
MAPPINGS = [
    ('Asianet 4K', 'IN4', 'ASIANET.HD.in'),
    ('Asianet Plus', 'IN4', 'ASIANET.PLUS.in'),
    ('Asianet Movies 4K', 'IN4', 'ASIANET.MOVIES.HD.in'),
    ('Surya TV 4K', 'IN4', 'SURYA.HD.in'),
    ('Surya Movies HD', 'IN4', 'SURYA.MOVIES.in'),
    ('Surya Comedy HD', 'IN4', 'SURYA.COMEDY.in'),
    ('Zee Keralam 4K', 'IN4', 'ZEE.KERALAM.HD.in'),
    ('Mazhavil Manorama 4K', 'IN4', 'MAZHAVIL.MANORAMA.HD.in'),
    ('Flowers TV HD', 'IN4', 'FLOWERS.in'),
    ('Kairali HD', 'IN4', 'KAIRALI.in'),
    ('Kairali WE', 'IN1', 'Kairali.WE.TV.in'),
    ('Amrita TV', 'IN4', 'AMRITA.in'),
    ('Safari TV', 'IN4', 'SAFARI.TV.in'),
    ('Kochu TV', 'IN4', 'KOCHU.TV.in'),
    ('Surya Music', 'IN4', 'SURYA.MUSIC.in'),
    ('Kappa TV', 'IN1', 'Kappa.TV.in'),
    ('Asianet News HD', 'IN4', 'ASIANET.NEWS.in'),
    ('Manorama News HD', 'IN4', 'MANORAMA.NEWS.in'),
    ('24 News HD', 'IN1', 'News.24.in'),
    ('Reporter TV HD', 'IN4', 'REPORTER.in'),
    ('Mathrubhumi News HD', 'IN4', 'MATHRUBHUMI.NEWS.in'),
    ('MediaOne HD', 'IN1', 'Media.One.TV.in'),
    ('Kairali News HD', 'IN4', 'KAIRALI.NEWS.in'),
    ('News18 Kerala HD', 'IN1', 'News.18.Kerala.in'),
    ('Janam TV HD', 'IN4', 'JANAM.TV.in'),
    ('Jai Hind TV HD', 'IN1', 'Jaihind.tv.in'),
    ('DD Malayalam HD', 'IN4', 'DD.MALAYALAM.in'),
    ('Star Vijay 4K', 'IN1', 'Star.Vijay.HD.in'),
    ('Vijay Super 4K', 'IN4', 'VIJAY.SUPER.HD.in'),
    ('Sun TV 4K', 'IN4', 'SUN.TV.HD.in'),
    ('KTV 4K', 'IN1', 'KTV.HD.in'),
    ('Zee Tamil 4K', 'IN4', 'ZEE.TAMIL.HD.in'),
    ('Colors Tamil 4K', 'IN4', 'COLORS.TAMIL.HD.in'),
    ('Jaya TV 4K', 'IN1', 'Jaya.TV.HD.in'),
    ('Sun Music 4K', 'IN4', 'SUN.MUSIC.HD.in'),
    ('Sun Life HD', 'IN4', 'SUN.LIFE.in'),
    ('Raj TV HD', 'IN4', 'RAJ.TV.in'),
    ('Kalaignar TV', 'IN4', 'KALAIGNAR.in'),
    ('Puthu Yugam', 'IN4', 'PUTHU.YUGAM.in'),
    ('Polimer TV', 'IN4', 'POLIMER.in'),
    ('Mega TV', 'IN4', 'MEGA.TV.in'),
    ('TravelXP Tamil', 'IN1', 'Travelxp.Tamil.in'),
    ('Sony BBC Earth Tamil HD', 'IN4', 'SONY.BBC.EARTH.HD.in'),
    ('Chutti TV', 'IN4', 'CHUTTI.TV.in'),
    ('Isai Aruvi', 'IN4', 'ISAI.ARUVI.in'),
    ('Sun News', 'IN4', 'SUN.NEWS.in'),
    ('Polimer News', 'IN4', 'POLIMER.NEWS.in'),
    ('News18 Tamil Nadu HD', 'IN1', 'News.18.Tamilnadu.in'),
    ('News 7 Tamil HD', 'IN1', 'News7.Tamil.in'),
    ('Thanthi TV', 'IN4', 'THANTHI.TV.in'),
    ('News Tamil 24x7', 'IN4', 'News.Tamil.24x7.in'),
    ('Raj News Tamil', 'IN4', 'RAJ.NEWS.TAMIL.in'),
    ('Star Plus 4K', 'IN4', 'STAR.PLUS.HD.in'),
    ('Zee TV 4K', 'IN4', 'ZEE.TV.HD.in'),
    ('Colors 4K', 'IN4', 'COLORS.HD.in'),
    ('Sony Entertainment 4K', 'IN1', 'SET.HD.in'),
    ('Sony SAB 4K', 'IN1', 'Sony.SAB.HD.in'),
    ('Star Bharat 4K', 'IN4', 'STAR.BHARAT.HD.in'),
    ('&TV 4K', 'IN1', '&amp;TV.HD.in'),
    ('Sony MAX 4K', 'IN1', 'Sony.Max.HD.in'),
    ('Star Gold 4K', 'IN4', 'STAR.GOLD.HD.in'),
    ('Star Gold 2 4K', 'IN1', 'Star.Gold.2.HD.in'),
    ('Star Gold Select 4K', 'IN4', 'Star.Gold.Select.HD.in'),
    ('Zee Cinema 4K', 'IN4', 'ZEE.CINEMA.HD.in'),
    ('&Pictures 4K', 'IN4', 'and.PICTURES.HD.in'),
    ('Colors Cineplex 4K', 'IN1', 'Colors.Cineplex.HD.in'),
    ('&Xplor 4K', 'IN1', '&amp;Xplor.HD.in'),
    ('Sony MAX 2', 'IN4', 'SONY.MAX.2.in'),
    ('Zee Bollywood', 'IN4', 'ZEE.Bollywood.in'),
    ('B4U Movies', 'IN4', 'B4U.Movies.in'),
    ('Zee Action', 'IN4', 'ZEE.ACTION.in'),
    ('EPIC HD', 'IN4', 'EPIC.TV.in'),
    ('Food Food', 'IN1', 'Food.Food.in'),
    ('MTV HD+ 4K', 'IN1', 'MTV.HD.in'),
    ('9XM', 'IN4', '9XM.in'),
    ('B4U Music', 'IN4', 'B4U.MUSIC.in'),
    ('Zoom', 'IN4', 'ZOOM.in'),
    ('Aaj Tak 4K', 'IN4', 'AAJ.TAK.in'),
    ('Times Now Navbharat 4K', 'IN4', 'TIMES.NOW.NAVBHARAT.in'),
    ('DD News 4K', 'IN4', 'DD.NEWS.in'),
    ('Republic Bharat', 'IN4', 'REPUBLIC.BHARAT.in'),
    ('Zee News', 'IN4', 'Zee.News.in'),
    ('ABP News', 'IN1', 'ABP.News.India.in'),
    ('India TV', 'IN4', 'INDIA.TV.in'),
    ('NDTV India', 'IN4', 'NDTV.INDIA.in'),
    ('WION', 'IN4', 'WION.in'),
    ('India Today', 'IN4', 'INDIA.TODAY.in'),
    ('CNN News18', 'IN1', 'CNN.NEWS.18.in'),
    ('Star Movies 4K', 'IN4', 'STAR.MOVIES.HD.in'),
    ('Star Movies Select 4K', 'IN4', 'STAR.MOVIES.SELECT.HD.in'),
    ('Sony PIX 4K', 'IN4', 'SONY.PIX.HD.in'),
    ('Movies Now 4K', 'IN1', 'Movies.Now.HD.in'),
    ('MNX 4K', 'IN1', 'MNX.HD.in'),
    ('MN+ 4K', 'IN4', 'MN+.HD.in'),
    ('&Prive 4K', 'IN1', 'And.Prive.HD.in'),
    ('&Flix 4K', 'IN1', 'AndFlix.HD.in'),
    ('Romedy Now HD', 'IN1', 'Romedy.Now.HD.in'),
    ('Zee Cafe 4K', 'IN4', 'ZEE.CAFE.HD.in'),
    ('Colors Infinity 4K', 'IN4', 'COLORS.INFINITY.HD.in'),
    ('TLC 4K', 'IN4', 'TLC.HD.in'),
    ('Zee Zest 4K', 'IN1', 'Zee.Zest.HD.in'),
    ('Times Now World HD', 'IN1', 'Times.Now.World.in'),
    ('CNN News18 English', 'IN1', 'CNN.NEWS.18.in'),
    ('BBC News HD', 'UK1', 'BBC.NEWS.HD.uk'),
    ('CNN HD', 'UK1', 'CNN.HD.uk'),
    ('CNBC HD', 'UK1', 'CNBC.HD.uk'),
    ('Sky News', 'UK1', 'Sky.News.HD.uk'),
    ('Republic TV English', 'IN1', 'Republic.TV.in'),
    ('Cartoon Network HD+ 4K', 'IN4', 'CARTOON.NETWORK.in'),
    ('Nick 4K', 'IN4', 'NICK.HD+.in'),
    ('Disney Channel 4K', 'IN4', 'DISNEY.CHANNEL.in'),
    ('Disney International 4K', 'IN1', 'Disney.International.HD.in'),
    ('Pogo Hindi', 'IN1', 'Pogo.Hindi.in'),
    ('Sony YAY Hindi', 'IN1', 'Sony.Yay.Hindi.in'),
    ('Sonic Hindi', 'IN1', 'Sonic.Hindi.in'),
    ('Discovery Kids', 'IN4', 'DISCOVERY.KIDS.in'),
    ('Super Hungama', 'IN4', 'SUPER.HUNGAMA.in'),
    ('Disney Junior Multi Audio', 'IN1', 'Disney.Junior.in'),
    ('Nick Junior', 'IN1', 'Nick.Junior.in'),
    ('Hungama', 'IN4', 'HUNGAMA.in'),
    ('ETV Bal Bharat HD', 'IN4', 'ETV.BAL.BHARAT.in'),
    ('CBeebies', 'IN1', 'CBeeBies.in'),
    ('Star Sports 1 English 4K', 'IN4', 'STAR.SPORTS.1.HD.in'),
    ('Star Sports 2 English 4K', 'IN4', 'STAR.SPORTS.2.HD.in'),
    ('Star Sports 1 Hindi 4K', 'IN4', 'STAR.SPORTS.1.HD.HINDI.in'),
    ('Star Sports 2 Hindi FHD', 'IN1', 'Star.Sports.2.Hindi.HD.in'),
    ('Star Sports Select 1 4K', 'IN4', 'STAR.SPORTS.SELECT.1.HD.in'),
    ('Star Sports Select 2 4K', 'IN4', 'STAR.SPORTS.SELECT.2.HD.in'),
    ('Star Sports 1 Tamil 4K', 'IN4', 'STAR.SPORTS.1.TAMIL.HD.in'),
    ('Star Sports 2 Tamil 4K', 'IN4', 'STAR.SPORTS.2.TAMIL.HD.in'),
    ('Sony Sports Ten 1 4K', 'IN4', 'SONY.SPORTS.TEN.1.HD.in'),
    ('Sony Sports Ten 2 4K', 'IN4', 'SONY.SPORTS.TEN.2.HD.in'),
    ('Sony Sports Ten 3 4K', 'IN4', 'SONY.SPORTS.TEN.3.HD.in'),
    ('Sony Sports Ten 5 4K', 'IN4', 'SONY.SPORTS.TEN.5.HD.in'),
    ('Sony Sports 4 Tamil', 'IN1', 'Sony.Ten.4.HD.Tamil.in'),
    ('Eurosport 4K', 'IN4', 'Eurosport.in'),
    ('Sky Sports Cricket 4K', 'UK1', 'SkySp.Cricket.uk'),
    ('Sky Sports F1 4K', 'UK1', 'SkySp.F1.HD.uk'),
    ('Sky Sports Premier League FHD', 'UK1', 'SkySp.PL.HD.uk'),
    ('Sky Sports Football FHD', 'UK1', 'SkySp.Fball.HD.uk'),
    ('Sky Sports Golf FHD', 'UK1', 'SkySp.Golf.HD.uk'),
    ('Sky Sports News FHD', 'UK1', 'SkySp.News.HD.uk'),
    ('TNT Sports 1 HD', 'UK1', 'TNT.Sports.1.HD.uk'),
    ('TNT Sports 2 FHD', 'UK1', 'TNT.Sports.2.HD.uk'),
    ('TNT Sports 3 FHD', 'UK1', 'TNT.Sports.3.HD.uk'),
    ('Willow Sports HD', 'US2', 'Willow.Cricket.HD.us2'),
    ('Willow 2 HD', 'US2', 'Willow.2.Xtra.us2'),
    ('DD Sports 4K', 'IN1', 'DD.Sports.HD.in'),
    ('Discovery 4K', 'IN4', 'DISCOVERY.CHANNEL.in'),
    ('Animal Planet 4K', 'IN1', 'Animal.Planet.HD.in'),
    ('National Geographic 4K', 'IN4', 'NATIONAL.GEOGRAPHIC.HD.in'),
    ('Nat Geo Wild 4K', 'IN4', 'NAT.GEO.WILD.HD.in'),
    ('History TV18 4K', 'IN4', 'HISTORY.TV18.HD.in'),
    ('Sony BBC Earth 4K', 'IN4', 'SONY.BBC.EARTH.HD.in'),
    ('Investigation Discovery 4K', 'IN4', 'Investigation.Discovery.in'),
    ('TravelXP 4K', 'IN1', 'Travelxp.HD.in'),
    ('Discovery Science', 'IN4', 'Discovery.Science.in'),
    ('Discovery Turbo', 'IN4', 'Discovery.Turbo.in'),
]


def fetch_feed(tag):
    req = urllib.request.Request(BASE_URL.format(tag=tag), headers=HEADERS)
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read()
    return ET.fromstring(gzip.decompress(raw))


def main():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    by_tag = {}
    for tag in sorted({x[1] for x in MAPPINGS}):
        print(f'Downloading {tag}...')
        by_tag[tag] = fetch_feed(tag)

    existing_channels = {c.get('id'): c for c in root.findall('channel')}
    updated = 0
    missing = []
    for name, tag, xmltv_id in MAPPINGS:
        src_root = by_tag[tag]
        src_channel = next((c for c in src_root.findall('channel') if c.get('id') == xmltv_id), None)
        src_programmes = [p for p in src_root.findall('programme') if p.get('channel') == xmltv_id]
        if not src_programmes:
            missing.append((name, tag, xmltv_id))
            print(f'SKIP {name}: no programmes in {tag} for {xmltv_id}')
            continue

        if xmltv_id not in existing_channels:
            if src_channel is not None:
                new_ch = copy.deepcopy(src_channel)
            else:
                new_ch = ET.Element('channel', {'id': xmltv_id})
                ET.SubElement(new_ch, 'display-name').text = name
            first_programme = root.find('programme')
            if first_programme is None:
                root.append(new_ch)
            else:
                root.insert(list(root).index(first_programme), new_ch)
            existing_channels[xmltv_id] = new_ch

        for p in list(root.findall('programme')):
            if p.get('channel') == xmltv_id:
                root.remove(p)
        for p in src_programmes:
            root.append(copy.deepcopy(p))
        updated += 1
        print(f'Updated {name} from {tag}: {len(src_programmes)} entries')

    if updated == 0:
        raise RuntimeError('No mapped channels were updated')

    ET.indent(tree, space='  ')
    tree.write(XML_PATH, encoding='utf-8', xml_declaration=True)
    print(f'Updated {updated} / {len(MAPPINGS)} mapped channels')
    if missing:
        print(f'No current source data for {len(missing)} mapped channels; previous XML was preserved for those channels.')


if __name__ == '__main__':
    main()
