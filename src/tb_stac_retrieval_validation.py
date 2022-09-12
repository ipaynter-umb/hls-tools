import t_stac_search
from random import shuffle
import datetime
import t_hls_albedo

years = list(range(2015, 2023))
shuffle(years)

doys = list(range(1, 366))
shuffle(doys)

while len(years) > 0:

    year = years.pop()
    doy = doys.pop()

    # convert datetime
    date = datetime.date(year=year, day=1, month=1) + datetime.timedelta(days=doy - 1)

    test_text = t_stac_search.get_text_from_STAC_request(f"https://cmr.earthdata.nasa.gov/stac/LPCLOUD/collections/HLSS30.v2.0/{str(date.year)}/{t_hls_albedo.zero_pad_number(str(date.month), digits=2)}/{t_hls_albedo.zero_pad_number(str(date.day), digits=2)}", attempt_limit=1)

    link_list = []

    if test_text:
        for link in test_text['links']:
            if link['rel'] == 'item':
                link_list.append(link['title'])

        print(f'{len(link_list)} files found for {date.year}, DOY {doy}:')

        for link in link_list:
            print(f'    {link}')

        print('\n============\n')