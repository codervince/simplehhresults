import scrapy
import re
import logging
from datetime import datetime
from dateutil.parser import parse
from collections import defaultdict,OrderedDict
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
        self.avgwinningtimes = dict()
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

    def parse_sectional_time(self, response):		
		'''
		horsenumber, horsename, horsecode
		marginsbehindleader = db.Column(postgresql.ARRAY(Float)) #floats
		sec_timelist= db.Column(postgresql.ARRAY(Float))
		'''
		horse_lines_selector = response.xpath('//table[@class="bigborder"]//table//a/../../..')
		sectional_time_selector = response.xpath('//table[@class='
		'"bigborder"]//table//a/../../../following-sibling::tr[1]')
		for line_selector, time_selector in zip(horse_lines_selector,sectional_time_selector):

			horsenumber = try_int(line_selector.xpath('td[1]/div/text()').extract()[0].strip())
			horse_name_cell = line_selector.xpath('td[3]/div/a/text()').extract()[0]
			horse_name_regexp = '^(?P<name>[^\(]+)\((?P<code>[^\)]+)\)$'
			horse_name_dict = re.match(horse_name_regexp, horse_name_cell).groupdict()
			horsename = horse_name_dict['name']
			horsecode = horse_name_dict['code']
			horsereport = getHorseReport(response.meta['racingincidentreport'], horsename)
			sec_timelist = [time.strip() for time in time_selector.xpath('td/text()').extract()]
			sec_timelist_len = len(sec_timelist)
			sec_timelist.extend([None for i in xrange(6-sec_timelist_len)])
			sec_timelist = map(get_sec_in_secs, sec_timelist)
			horse_path = line_selector.xpath('td[3]/div/a/@href').extract()[0]
			# horse_url = 'http://www.{domain}/english/racing/{path}&Option=1#htop'.format(domain=self.domain, path=horse_path)
			horse_smartform_url = 'http://racing.hkjc.com/racing/info/horse/smartform/english/{hcode}'.format(hcode=horsecode)
			marginsbehindleader = [s.strip('\t\n\r ') for s in line_selector.xpath('td//table//td/text()').extract()]
			marginsbehindleader.extend([None]*(6 - len(marginsbehindleader)))
			marginsbehindleader = map(horselengthprocessor, marginsbehindleader)
			# request = scrapy.Request(response.meta['results_url'],callback=self.parse_results)
			# meta_dict = response.meta
			# meta_dict.update({
			# 'horsenumber': horsenumber,
			# 'horsename': horsename,
			# 'horsecode': horsecode,
			# 'horsereport': horsereport,
			# 'sec_timelist': sec_timelist,
			# # 'horse_url': horse_url,
			# 'horse_smartform_url': horse_smartform_url,
			# 'marginsbehindleader': marginsbehindleader,
			# })
			# print meta_dict
			# request.meta.update(meta_dict)
			# print meta_dict

			##get data from ordered dict
			#get index from horsecodes
			_hc_idx = None
			winoddsrank = 0.0
			for x,y in response.meta['horsecodes'].items():
				if y == horsecode:
					_hc_idx, hc = x,y
			if _hc_idx:
				finishtime = response.meta['finishtimes'][_hc_idx]
				market_prob = response.meta['market_probs'][_hc_idx]
				jockeycode = response.meta['jockeycodes'][_hc_idx]
				place = response.meta['places'][_hc_idx]
				runningpositions = response.meta['runningpositions'][_hc_idx]
				winodds = response.meta['winodds'][_hc_idx]
			#use index to get finishtime, jockeycode, place, winodds, market_probs
				for i,x in enumerate(response.meta['winoddsranks'].items()):
					if x[1] == winodds:
						winoddsrank = i
			#with winoddsrank reverse lookup o winodds

			yield items.SimplehkjcresultsItem(
        	racenumber=response.meta['racenumber'],
        	horsenumber=horsenumber,
        	horsecode=horsecode,
        	jockeycode=jockeycode,
        	finishtime=finishtime,
        	theresults = response.meta['theresults'],
        	runnerslist = response.meta['runnerslist'],
        	runningpositions= runningpositions,
        	market_prob=market_prob,
        	race_total_prob =response.meta['race_total_prob'],
        	place=place,
        	winodds=winodds,
        	winoddsrank=winoddsrank,
        	horsereport=horsereport,
        	sec_timelist = sec_timelist,
        	marginsbehindleader= marginsbehindleader,
            racedate=self.racedate,
            racecoursecode=self.racecoursecode,
			win_combo_div= response.meta['win_combo_div'],
            place_combo_div= response.meta['place_combo_div'],
            qn_combo_div= response.meta['qn_combo_div'],
            qnp_combo_div= response.meta['qnp_combo_div'],
            tce_combo_div= response.meta['tce_combo_div'],
            trio_combo_div=response.meta['trio_combo_div'],
            f4_combo_div= response.meta['f4_combo_div'],
            qtt_combo_div= response.meta['qtt_combo_div'],
            dbl9_combo_div= response.meta['dbl9_combo_div'],
            dbl8_combo_div= response.meta['dbl8_combo_div'],
            dbl7_combo_div= response.meta['dbl7_combo_div'],
            dbl6_combo_div= response.meta['dbl6_combo_div'],
            dbl5_combo_div=response.meta['dbl5_combo_div'],
            dbl4_combo_div= response.meta['dbl4_combo_div'],
            dbl3_combo_div= response.meta['dbl3_combo_div'],
            dbl2_combo_div= response.meta['dbl2_combo_div'],
            dbl1_combo_div= response.meta['dbl1_combo_div'],
            dbl10_combo_div= response.meta['dbl10_combo_div'],
            dbltrio1_combo_div= response.meta['dbltrio1_combo_div'],
            dbltrio2_combo_div= response.meta['dbltrio2_combo_div'],
            dbltrio3_combo_div= response.meta['dbltrio3_combo_div'],
        )

			# yield response

    '''
    racedate, racenumber,
    timestats esp paceofrace
    '''
    def parse_race(self, response):

    	# print response.url

    	#RACESTATS
    	raceindex_path = re.compile(r'\((\d+)\)')
    	ri = response.xpath('//div[@class="boldFont14 color_white trBgBlue"]//text()').extract()[0]
    	_raceindex = raceindex_path.findall(ri)[0]
    	going = response.xpath("//table[@class='tableBorder0 font13']//td[contains(text(),'Going')]/following-sibling::td/text()").extract()[0]
    	# prizemoney = re.sub("\D", "", response.xpath('//td[@class="number14"]/text()').extract()[0])
    	raceclass = response.xpath('//table[contains(@class, \"tableBorder0 font13\")]/tr[1]/td[1]/text()').extract()[0].split('-')[0].strip()
    	_distance = response.xpath('//table[contains(@class, \"tableBorder0 font13\")]/tbody//tr//td[1]//text()').extract()
    	# [1].split('-')[0].strip()
    	# raceindex = self.racedate + "_"+ str(_raceindex)
    	###FIX DISTANCE!!
    	distance = _distance
    	# distance = (_distance.replace('m', ''))
    	raceinfo_ = response.xpath('//table[@class="font13 lineH20 tdAlignL"]//descendant::text()[ancestor::td and normalize-space(.) != ""][position()>=2]').extract()
     	print "raceinfo_".format(raceinfo_)
     #    date_racecourse_localtime = cleanstring(raceinfo_[0])
     #    surface_distance = raceinfo_[1].encode('utf-8').strip()
     #    try:
     #    	_surface, _trackvariant, _distance, _going = surface_distance.split(u',')
     #    except ValueError:
     #    	_surface, _trackvariant, _distance = surface_distance.split(u',')
    	# print going, raceclass, raceindex, _distance

    	#### DIVIDENDS
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
        ##RUNNERS


        sectional_time_url = response.xpath('//div[@class="rowDiv15"]/div['
            '@class="rowDivRight"]/a/@href').extract()[0]
        horsecodelist_ = response.xpath('//table[@class="tableBorder trBgBlue'
            ' tdAlignC number12 draggable"]//td[@class="tdAlignL font13'
            ' fontStyle"][1]/text()').extract()
        horsetimes_ = response.xpath('//table[@class="tableBorder trBgBlue'
            ' tdAlignC number12 draggable"]//td[11]/text()').extract()
       	hplaces = response.xpath('//table[@class="tableBorder trBgBlue'
            ' tdAlignC number12 draggable"]//td[2]/text()').extract()
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
        market_probs = OrderedDict()
        mkt_probs =  [ dec_odds_to_pchance(o) for o in winodds ]
        for i,x in enumerate(mkt_probs):
        	market_probs[i+1]=round(x,2) 
        race_total_prob =  round( (sum( mkt_probs  )), 2)
        print "sum of market probs {} market_probs {}".format(race_total_prob, market_probs)
        
        # print hplaces, winodds_
        racingincidentreport = response.xpath('//tr[td[contains(text(), '
            '"Racing Incident Report")]]/following-sibling::tr/td/text()'
            ).extract()[0]
        # print(racingincidentreport)
        # print santitizeracereport(racingincidentreport)

# l.add_xpath('FinishTime', './td[11]/text()')
        horsenos = OrderedDict()
        places = OrderedDict()
        winodds = OrderedDict()
        horsecodes = OrderedDict()
        rps = OrderedDict()
        finishtimes = OrderedDict()
        runningpositions = OrderedDict()
        actualwts =  OrderedDict()
        jockeycodes = OrderedDict()
        horsecode_pat = re.compile(r"horseno=(.+)")
        odd_runners = 1#  or @class='trBgWhite'
      	even_runners = 2
      	for row in response.xpath("//table[@class='tableBorder trBgBlue tdAlignC number12 draggable']//tr[@class='trBgGrey']"):
      		horsenos[odd_runners] = row.xpath('./td[1]/text()').extract()[0] or 0
      		places[odd_runners] = row.xpath('./td[2]/text()').extract()[0] or 0
      		_runningpositions = row.xpath('./td[10]/table//td//text()').extract() or 0
      		_actualwts = row.xpath('./td[6]//text()').extract()[0] or 0
      		_jockeycode = row.xpath('./td[4]/a/@href').extract()[0] or 0
        	jockeycodes[odd_runners] = re.match(r'^http://www.hkjc.com/english/racing/jockeyprofile.asp?.*jockeycode=(?P<str>[^&]*)(&.*$|$)', _jockeycode).groupdict()['str']
        	# [m.group(1) for l in lines for m in [regex.search(l)] if m]
        	runningpositions[odd_runners] = _runningpositions
        	actualwts[odd_runners] = int(_actualwts)
        	_winodds = row.xpath('./td[12]/text()').extract()[0] or 0
      		winodds[odd_runners] = getodds(_winodds)
      		horsecode = horsecode_pat.findall(row.xpath('./td[3]/a/@href').extract()[0]) or None
      		horsecodes[odd_runners] = horsecode[0] or None
      		_finishtime= row.xpath('./td[11]/text()').extract()[0] or None
      		finishtimes[odd_runners] = get_sec(_finishtime)
      		odd_runners +=2
        for row in response.xpath("//table[@class='tableBorder trBgBlue tdAlignC number12 draggable']//tr[@class='trBgWhite']"):
      		horsenos[even_runners] = row.xpath('./td[1]/text()').extract()[0] or 0
      		places[even_runners] = row.xpath('./td[2]/text()').extract()[0] or 0
      		_runningpositions = row.xpath('./td[10]/table//td//text()').extract() or 0
      		_actualwts = row.xpath('./td[6]//text()').extract()[0] or 0
      		_jockeycode = row.xpath('./td[4]/a/@href').extract()[0] or 0
        	jockeycodes[even_runners] = re.match(r'^http://www.hkjc.com/english/racing/jockeyprofile.asp?.*jockeycode=(?P<str>[^&]*)(&.*$|$)', _jockeycode).groupdict()['str']
        	# [m.group(1) for l in lines for m in [regex.search(l)] if m]
        	runningpositions[even_runners] = _runningpositions
        	actualwts[even_runners] = int(_actualwts)
      		_winodds = row.xpath('./td[12]/text()').extract()[0] or 0
      		winodds[even_runners] = getodds(_winodds)
      		horsecode = horsecode_pat.findall(row.xpath('./td[3]/a/@href').extract()[0]) or None
      		horsecodes[even_runners] = horsecode[0] or None
      		_finishtime= row.xpath('./td[11]/text()').extract()[0] or None
      		finishtimes[even_runners] = get_sec(_finishtime)
      		even_runners +=2
      		# print row.xpath('./td[1]/text()').extract()[0]
        norunners = len(horsenos.items())
        horsenos = OrderedDict(sorted(horsenos.items(), key=lambda t: t[0]))
        places = OrderedDict(sorted(places.items(), key=lambda t: t[0]))
        winodds = OrderedDict(sorted(winodds.items(), key=lambda t: t[0]))
    	winodds_ranks = OrderedDict(sorted(winodds.items(), key=lambda t: t[1]))
        horsecodes = OrderedDict(sorted(horsecodes.items(), key=lambda t: t[0]))
        finishtimes = OrderedDict(sorted(finishtimes.items(), key=lambda t: t[0]))
        print "horsenos: {}, places --> {}, winodds {} plus horsecodes {} and finishtimes {} and actualwts{} and jockeycodes{} and runningpositions {}".\
        format(horsenos, places, winodds,horsecodes, finishtimes, actualwts, jockeycodes, runningpositions)
        print "winoddsranks {}".format(winodds_ranks)
        if distance and distance != 0:
            winningtime = finishtimes.items()[0][1]/float(distance) #one and only winningtime
            self.avgwinningtimes[response.meta['racenumber']] = winningtime
        runnerslist = horsecodes.values()
        _places = places.values()
        #look for DH
        theresults = []
        if u'DH' in _places:
        	#need to create several strings
        	theresults.append("-".join(places.values()[:4]))
        	pass
        else:
        	theresults.append("-".join(places.values()[:4]))
       	print "avgwinningtimes {}, runnerslist {}".format(self.avgwinningtimes, runnerslist)
        
        # for i, row in enumerate(response.xpath("//table[@class='tableBorder trBgBlue tdAlignC number12 draggable']//tr")):
        # 	thehorseno = try_int(row.xpath('./td[2]/text()').extract()[0])

        # 	if thehorseno != 0:
        # 	##EXCLUDE NON NUMERS
        # 		horsenos[i] = thehorseno
        # 	theplace = try_int(row.xpath('./td[1]/text()').extract()[0])
        # 	if theplace !=0:
        # 		places[theplace] = None
        # 	# print "win odds?\t"
        # 	thewinodds = row.xpath('./td[12]/text()').extract()
        # 	if thewinodds != []:
        # 		winodds[thewinodds[0]] = None
        # 	# thewinodd = row.xpath('/td[12]/text()').extract()[0]
        # 	# winodds[thewinodd] = None
        # 	# horsenos.add(row.xpath('./td[2]/text()').extract()[0])
        # print "horsenos: {}, places --> {}, winodds {}".format(horsenos, places, winodds)
        	# rps += row.xpath('./td[10]//text()').extract()[0] + "-"
        	# winodds += row.xpath('./td[12]/text()').extract()[0] + "-"
        # print horsenos.rstrip('-'), places.rstrip('-')
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
        request = scrapy.Request(sectional_time_url, callback=self.parse_sectional_time)
        meta_dict = {
            'racenumber': response.meta['racenumber'],
            'racedate': self.racedate,
            'racecoursecode': self.racecoursecode,
            'noruners': norunners,
            'runnerslist': runnerslist,
            'places': places,
            'runningpositions': runningpositions,
            'winodds': winodds,
            'winoddsranks': winodds_ranks,
            'actualwts': actualwts,
            'jockeycodes': jockeycodes,
            'market_probs': market_probs,
            'race_total_prob': race_total_prob,
            'horsecodes': horsecodes,
            'finishtimes': finishtimes,
            'theresults':theresults,
            # 'raceindex': raceindex,
            # 'racegoing': racegoing,
            # 'raceclass': raceclass,
            # 'racedistance': racedistance,
            'racingincidentreport': racingincidentreport,
            'win_combo_div': div_info['WIN'],
            'place_combo_div': div_info['PLACE'],
            'qn_combo_div' : div_info['QUINELLA'],
            'qnp_combo_div' : div_info['QUINELLA PLACE'],
            'tce_combo_div' : div_info['TIERCE'],
            'trio_combo_div' : div_info['TRIO'],
            'f4_combo_div' : div_info['FIRST 4'],
            'qtt_combo_div' : div_info['QUARTET'],
            'dbl9_combo_div' : div_info['9TH DOUBLE'],
            'dbl8_combo_div' : div_info['8TH DOUBLE'],
            'dbl7_combo_div' : div_info['7TH DOUBLE'],
            'dbl6_combo_div' : div_info['6TH DOUBLE'],
            'dbl5_combo_div' : div_info['5TH DOUBLE'],
            'dbl4_combo_div' : div_info['4TH DOUBLE'],
            'dbl3_combo_div' : div_info['3RD DOUBLE'],
            'dbl2_combo_div' : div_info['2ND DOUBLE'],
            'dbl1_combo_div' : div_info['1ST DOUBLE'],
            'dbl10_combo_div' : div_info['10TH DOUBLE'],
            'dbltrio1_combo_div' : div_info['1ST DOUBLE TRIO'],
            'dbltrio2_combo_div' : div_info['2ND DOUBLE TRIO'],
            'dbltrio3_combo_div' : div_info['3RD DOUBLE TRIO'],
        }
        
        request.meta.update(meta_dict)
        yield request


   #      yield items.SimplehkjcresultsItem(
   #      	racenumber=response.meta['racenumber'],
   #          racedate=self.racedate,
   #          racecoursecode=self.racecoursecode,
			# win_combo_div= div_info['WIN'],
   #          place_combo_div= div_info['PLACE'],
   #          qn_combo_div= div_info['QUINELLA'],
   #          qnp_combo_div= div_info['QUINELLA PLACE'],
   #          tce_combo_div= div_info['TIERCE'],
   #          trio_combo_div= div_info['TRIO'],
   #          f4_combo_div= div_info['FIRST 4'],
   #          qtt_combo_div= div_info['QUARTET'],
   #          dbl9_combo_div= div_info['9TH DOUBLE'],
   #          dbl8_combo_div= div_info['8TH DOUBLE'],
   #          dbl7_combo_div= div_info['7TH DOUBLE'],
   #          dbl6_combo_div= div_info['6TH DOUBLE'],
   #          dbl5_combo_div= div_info['5TH DOUBLE'],
   #          dbl4_combo_div= div_info['4TH DOUBLE'],
   #          dbl3_combo_div= div_info['3RD DOUBLE'],
   #          dbl2_combo_div= div_info['2ND DOUBLE'],
   #          dbl1_combo_div= div_info['1ST DOUBLE'],
   #          dbl10_combo_div= div_info['10TH DOUBLE'],
   #          dbltrio1_combo_div= div_info['1ST DOUBLE TRIO'],
   #          dbltrio2_combo_div= div_info['2ND DOUBLE TRIO'],
   #          dbltrio3_combo_div= div_info['3RD DOUBLE TRIO'],
   #      )


	


         
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