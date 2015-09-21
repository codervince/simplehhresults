import scrapy
import re
import logging
from datetime import datetime
from dateutil.parser import parse
from collections import defaultdict
from simplehkjcresults.utilities import cleanstring
import pprint



class Simplehkjcspider(scrapy.Spider):
	
    name = "simplehkjcspider"

    def __init__(self, date, racecoursecode, *args, **kwargs):
        assert racecoursecode in ['ST', 'HV']
        super(Simplehkjcspider, self).__init__(*args, **kwargs)
        self.hkjc_domain = 'hkjc.com'
        self.racecoursecode = racecoursecode
        self.racedate = date
        self.MeetingDrawPlaceCorr = []
        self.meetingrunners = defaultdict(list)
        self.sectionalbaseurl = 'http://www.hkjc.com/english/racing/display_sectionaltime.asp?'
        self.start_urls = [
            'http://racing.{domain}/racing/Info/Meeting/Results/English/Local/'
            '{date}/{racecoursecode}/1'.format(domain=self.hkjc_domain, 
                date=date, racecoursecode=racecoursecode),
        ]
    
    def parse(self, response):
        race_paths = response.xpath('//div[@class="raceNum clearfix"]//'
            'td[position()!=last()]/a/@href').extract()
        ##exclude S1 S1 Simulcast
        ## http://racing.hkjc.com/racing/Info/Meeting/Results/English/Simulcast/20150607/S2/1
        race_paths = response.xpath('//td[@nowrap="nowrap" and @width="24px"]'
            '/a/@href').extract()
        urls = ['http://{domain}{path}'.format(
                domain=self.hkjc_domain,
                path=path,
            ) for path in race_paths
        ] + [response.url]
        for url in urls:
            if int(url.split('/')[-1]) > 9:
                racenumber = '{}'.format(url.split('/')[-1])
            else:
                racenumber = '0{}'.format(url.split('/')[-1])
            request = scrapy.Request(url, callback=self.parse_race)
            request.meta['racenumber'] = racenumber
    '''
    raceclass dividends

    '''
    def parse_race(self, response):
    	print "in race"
    	racetypes_regexes = [
    	"Class\s(\d+).*",
    	"Griffin.*",
    	"Group.*",
    	]
    	combined = "(" + ")|(".join(regexes) + ")"
    	__raceclass = response.xpath("//td[@class='divWidth']/text()").extract()
    	_raceclass = re.match(combined, __raceclass)
    	# rcpat = re.compile(r'^Class|Group|Griffin \d+.{1}(?P<raceclass>.+)')
    	
    	# rc = re.match(r'^Class \d+.{1}(?P<raceclass>.+)$', _raceclass
     #        ).groupdict()['raceclass']
        item['racecoursecode'] = self.racecoursecode
        item['racedate'] = self.racedate
        item['raceclass'] = _raceclass

        yield item
        # raceclass__ = unicode.strip(response.xpath('//td[@class="divWidth"]/text()').extract()[0])
        
        # raceclass_ = re.match(r'^Class (?P<int>\d+)', raceclass__)
        # raceclass_ = re.match(r'^Class (?P<int>\d+) - $', raceclass__)

        
        # raceclass = raceclass_ and raceclass_.groupdict()['int']
   

        # racedistance_ = response.xpath('//td[@class="divWidth"]/span/text()').extract()[0]
        # racedistance = re.match(r'^(?P<int>\d+)M.*$', racedistance_).groupdict()['int']

        # racegoing = response.xpath('//td[text() = "Going :"]/'
        #     'following-sibling::td/text()').extract()[0]

        # racetrack = response.xpath('//td[text() = "Course :"]/'
        #     'following-sibling::td/text()').extract()[0]
        # if u'-' in racetrack: 
        #     _racetrack = unicode.strip( racetrack.split('-')[1].replace(u'COURSE', '').replace(u'"', u"'"))
        # else:
        #     _racetrack = racetrack

        ##process this

#         racetime = None
#         _racetimes = response.xpath('//td[text() = "Time :"]/'
#             'following-sibling::td/text()').extract()[0]
#         if len(_racetimes) > 1:
#             racetime = get_hkjc_ftime(_racetimes.split("\t")[-1:][0].replace("(", "").replace(")", ""))


#         # horsecodelist_ = response.xpath('//table[@class="tableBorder trBgBlue'
#         #     ' tdAlignC number12 draggable"]//td[@class="tdAlignL font13'
#         #     ' fontStyle"][1]/text()').extract()
#         # # horsecodelist = [re.match(r'^\((?P<str>.+)\)$', s).groupdict()['str'] for s in horsecodelist_]
#         # pprint.pprint(horsecodelist_)
#         ## add to meeting 
#         # self.meetingrunners[racenumber].append(horsecodelist)
#         # pprint.pprint(self.meetingrunners[racenumber] )
#         # horsecodelist = horsecodelist_
#         racingincidentreport = response.xpath('//tr[td[contains(text(), '
#             '"Racing Incident Report")]]/following-sibling::tr/td/text()'
#             ).extract()[0]

#         sectional_time_url = response.xpath('//div[@class="rowDiv15"]/div['
#             '@class="rowDivRight"]/a/@href').extract()[0]
#         request = scrapy.Request(sectional_time_url, callback=
#             self.parse_sectional_time)
#         meta_dict = {
#             'racecoursecode': racecoursecode,
#             'racedate': racedate,
#             'racetime': racetime,
#             'racenumber': racenumber,
#             'raceindex': raceindex,
#             'racename': racename[0] if racename else None,
#             'raceclass': raceclass,
#             'racedistance': racedistance,
#             'racegoing': racegoing,
#             'racetrack': _racetrack,
#             'racesurface': unicode.strip( racetrack.split('-')[0]),
#             # 'horsecodelist': horsecodelist,
#             'racingincidentreport': racingincidentreport,
#             'results_url': response.url,
#         }
#         request.meta.update(meta_dict)

#         yield request