#!/usr/bin/env python3
import xml.etree.ElementTree as ET

from update_malayalam_airtel import XML_PATH, fetch_airtel, make_node, parse_time, ensure_channel

# Verified Airtel Xstream internal channel IDs for channels whose Tata Play
# schedule mapping did not produce usable EPG on the MAG524.
CHANNELS = [
    ('News Malayalam 24x7 HD', 'LIVETV_LIVETVCHANNEL_NEWS_MALAYALAM_24X7', 'ts1367'),
    ('Raj Music Malayalam', 'LIVETV_LIVETVCHANNEL_RAJ_MUSIX_MALAYALAM', 'rajmusixmalayalam.in'),
]


def main():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    updated = 0

    for name, airtel_id, mag_id in CHANNELS:
        try:
            programs = fetch_airtel(airtel_id)
            nodes = []
            for item in sorted(programs, key=lambda x: parse_time(x.get('startTime'))):
                node = make_node(item, mag_id)
                if node is not None:
                    nodes.append(node)

            if not nodes:
                print(f'SKIP {name}: no valid Airtel EPG')
                continue

            ensure_channel(root, name, mag_id)
            for p in list(root.findall('programme')):
                if p.get('channel') == mag_id:
                    root.remove(p)
            for node in nodes:
                root.append(node)

            updated += 1
            print(f'Updated {name} from Airtel: {len(nodes)} entries')
        except Exception as e:
            print(f'SKIP {name}: {e}')

    if updated:
        ET.indent(tree, space='  ')
        tree.write(XML_PATH, encoding='utf-8', xml_declaration=True)
        print(f'Updated {updated} Airtel fallback channels')
    else:
        print('No Airtel fallback channels updated')


if __name__ == '__main__':
    main()
