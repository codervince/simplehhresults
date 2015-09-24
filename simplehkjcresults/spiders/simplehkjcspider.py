import scrapy
import re
import logging
from datetime import datetime
from dateutil.parser import parse
from collections import defaultdict
from simplehkjcresults.utilities import *
import pprint
from simplehkjcresults import items



class Simplehkjcspider(scrapy.Spider):
	
    name = "simplehkjcspider"
    allowed_domains = ["hkjc.com"]

    def __init__(self, date, racecoursecode, *args, **kwargs):
        assert racecoursecode in ['ST', 'HV']
        super(Simplehkjcspider, self).__init__(*args, **kwargs)
        self.hkjc_domain = 'hkjc.com'
        self.racecoursecode = racecoursecode
        self.racedate = date
        self.MeetingDrawPlaceCorr = []
        self.meetingrunners = defaultdict(list)
        self.sectionalbaseurl = 'http://www.hkjc.com/english/racing/display_sectionaltime.asp?'
        self.newbaseurl =  'http://racing.hkjc.com/racing/Info/Meeting/Results/English/Local/{date}/{racecoursecode}/'.format(domain=self.hkjc_domain,date=date, racecoursecode=racecoursecode) 
        ##these have been changed
        ##new urls = http://racing.hkjc.com/racing/Info/Meeting/Results/English/Local/20150919/ST/2
        self.start_urls = [
            'http://racing.hkjc.com/racing/Info/Meeting/Results/English/Local/'
            '{date}/{racecoursecode}/1'.format(domain=self.hkjc_domain, 
                date=date, racecoursecode=racecoursecode),
        ]
    
    def parse(self, response):
        race_paths = response.xpath('//td[@nowrap="nowrap" and @width="24px"]'
            '/a/@href').extract()
        urls = ['http://{path}'.format(
                domain=self.hkjc_domain,
                path=path,
            ) for path in race_paths
        ] + [response.url]
        for url in urls:
 
            if int(url.split('/')[-1]) > 9:
                racenumber = '{}'.format(url.split('/')[-1])
            else:
                racenumber = '0{}'.format(url.split('/')[-1])
            url = self.newbaseurl + racenumber
            # print url
            request = scrapy.Request(url, callback=self.parse_race)
            request.meta['racenumber'] = racenumber
            yield request

    '''
    racedate, racenumber,
    timestats esp paceofrace
    '''
    def parse_race(self, response):
    	print "in race"
    	print response.url

    	#raceclass pain in ass
    	## get raceindex
    	## Class 5 - 1800M - (40-15)


        markets = [ 'WIN', 'PLACE', 'QUINELLA', 'QUINELLA PLACE', 'TIERCE', 'TRIO', 'FIRST 4', 'QUARTET','9TH DOUBLE', 'TREBLE', '3RD DOUBLE TRIO' , 'SIX UP', 'JOCKEY CHALLENGE',
            '8TH DOUBLE', '8TH DOUBLE', '2ND DOUBLE TRIO', '6TH DOUBLE', 'TRIPLE TRIO(Consolation)', 'TRIPLE TRIO', '5TH DOUBLE', '5TH DOUBLE', '1ST DOUBLE TRIO', '3RD DOUBLE' ,
            '2ND DOUBLE', '1ST DOUBLE']
        div_table = response.xpath("//td[@class='trBgBlue1 tdAlignL boldFont14 color_white']")
        isdividend = response.xpath("//td[text() = 'Dividend']/text()").extract()[0]

        if isdividend == u'Dividend':
            div_info = defaultdict(list)
            for m in markets:
                try:
                    xpathstr = str("//tr[td/text() = 'Dividend']/following-sibling::tr[td/text()=")
                    xpathstr2 = str("]/td/text()")
                    win_divs =response.xpath(xpathstr + "'" + str(m) + "'" + xpathstr2).extract()
                    div_info[win_divs[0]] = [ win_divs[1],win_divs[2] ] 
                    # print response.meta['racenumber']
                except:
                    div_info[m] = None
        print div_info

        sectional_time_url = response.xpath('//div[@class="rowDiv15"]/div['
            '@class="rowDivRight"]/a/@href').extract()[0]
        horsecodelist_ = response.xpath('//table[@class="tableBorder trBgBlue'
            ' tdAlignC number12 draggable"]//td[@class="tdAlignL font13'
            ' fontStyle"][1]/text()').extract()
        horsetimes_ = response.xpath('//table[@class="tableBorder trBgBlue'
            ' tdAlignC number12 draggable"]//td[11]/text()').extract()
       	winodds_ = response.xpath('//table[@class="tableBorder trBgBlue'
            ' tdAlignC number12 draggable"]//td[12]/text()').extract()
        horsecodelist = [re.match(r'^\((?P<str>.+)\)$', s).groupdict()['str'] for s in horsecodelist_]
        # print horsetimes_, winodds_
        #map process each one
        winodds = [getodds(o) for o in winodds_[1:] if o != u'---']
        horsetimes = [get_sec(s) for s in horsetimes_[1:] if s != u'---']
        # print sectional_time_url
        # pprint.pprint(horsecodelist)
        # pprint.pprint(horsetimes)
        # pprint.pprint([o for o in winodds if o is not None])
        mkt_probs =  [ dec_odds_to_pchance(o) for o in winodds ]
        print(sum( mkt_probs  ))

        racingincidentreport = response.xpath('//tr[td[contains(text(), '
            '"Racing Incident Report")]]/following-sibling::tr/td/text()'
            ).extract()[0]
        print(racingincidentreport)
        print santitizeracereport(racingincidentreport)
            # response.xpath("//tr[td/text() = 'Dividend']/following-sibling::tr[2]").extract()[0]

        # raceclass__ = response.xpath('//td[@class="divWidth"]/text()').extract()[0]
        # raceclass_ = re.match(r'^Class (?P<int>\d+) - $', raceclass__)
        # raceclass = raceclass_ and raceclass_.groupdict()['int']

    	    # _raceclass = re.match(combined, __raceclass)
    	# print _raceclass
    	# rcpat = re.compile(r'^Class|Group|Griffin \d+.{1}(?P<raceclass>.+)')
    	
    	# # rc = re.match(r'^Class \d+.{1}(?P<raceclass>.+)$', _raceclass
     # #        ).groupdict()['raceclass']
        # item['racecoursecode'] = self.racecoursecode
    
        # item['raceclass'] = _raceclass

        yield items.SimplehkjcresultsItem(
        	racenumber=response.meta['racenumber'],
            racedate=self.racedate,
            racecoursecode=self.racecoursecode,
			win_combo_div= div_info['WIN'],
            place_combo_div= div_info['PLACE'],
            qn_combo_div= div_info['QUINELLA'],
            qnp_combo_div= div_info['QUINELLA PLACE'],
            tce_combo_div= div_info['TIERCE'],
            trio_combo_div= div_info['TRIO'],
            f4_combo_div= div_info['FIRST 4'],
            qtt_combo_div= div_info['QUARTET'],
            dbl9_combo_div= div_info['9TH DOUBLE'],
            dbl8_combo_div= div_info['8TH DOUBLE'],
            dbl7_combo_div= div_info['7TH DOUBLE'],
            dbl6_combo_div= div_info['6TH DOUBLE'],
            dbl5_combo_div= div_info['5TH DOUBLE'],
            dbl4_combo_div= div_info['4TH DOUBLE'],
            dbl3_combo_div= div_info['3RD DOUBLE'],
            dbl2_combo_div= div_info['2ND DOUBLE'],
            dbl1_combo_div= div_info['1ST DOUBLE'],
            dbl10_combo_div= div_info['10TH DOUBLE'],
            dbltrio1_combo_div= div_info['1ST DOUBLE TRIO'],
            dbltrio2_combo_div= div_info['2ND DOUBLE TRIO'],
            dbltrio3_combo_div= div_info['3RD DOUBLE TRIO'],
        )


         
        # yield item
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