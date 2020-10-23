# -*- coding: utf-8 -*-
import re

import scrapy
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

DAYS = {
    "0": "Mo",
    "1": "Tu",
    "2": "We",
    "3": "Th",
    "4": "Fr",
    "5": "Sa",
    "6": "Su"
}

class FarmersHomeFurnitureSpider(scrapy.Spider):
    name = 'farmershomefurniture'
    item_attributes = {'brand': 'Farmers Home Furniture'}
    allowed_domains = ['www.farmershomefurniture.com']
    start_urls = ['https://www.farmershomefurniture.com/store-list.inc']

    def parse(self, response):
        for store in response.xpath('//tr'):
            store_data = store.xpath('./td/text()').getall()
            if store_data:
                properties={ ['city', 'state', 'address', 'phone'][i]: store_data[i]
                                                        for i in range(len(store_data)) }

                store_link = store.xpath('./@onclick').re_first('/stores/[0-9a-z-]+.inc')
                store_url = 'https://www.farmershomefurniture.com/{}'.format(store_link)

                yield scrapy.Request(store_url, callback=self.parse_store, cb_kwargs=properties)


    def parse_store(self, response, city, state, address, phone):
        opening_hours = OpeningHours()
        store_hours = response.xpath('//div[@class="workspacearea"]/div/div/p/text()').extract()[2:]

        for hours in store_hours:
            day = hours.strip().split(':')[0]
            if day != 'Sun':
                time_range= hours.strip().split(':')[1].split('-')
                if time_range[0] != 'Closed':
                    opening_hours.add_range(day=DAYS[str(store_hours.index(hours))],
                                        open_time=time_range[0].strip()+":00",
                                        close_time=time_range[1].strip()+":00"
                                        )

        store_coordinates= response.xpath('//script/text()').re_first('lat .*[\n].*').split(';')[:2]

        properties = {
                'addr_full': address,
                'city': city,
                'phone': phone,
                'state': state,
                'lat': store_coordinates[0].split('"')[1],
                'lon': store_coordinates[1].split('"')[1],
                'opening_hours': opening_hours.as_opening_hours(),
                'ref': re.search(r'.+/(.+?)/?(?:\.inc|$)', response.url).group(1)
        }

        yield GeojsonPointItem(**properties)
