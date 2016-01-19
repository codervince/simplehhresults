import scrapy
import re
import logging
from datetime import datetime
from dateutil.parser import parse
from collections import defaultdict,OrderedDict, Counter
from simplehkjcresults.utilities import *
import pprint
from simplehkjcresults import items
import sys
import os
from simplehkjcresults import settings

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logger = logging.getLogger()

STANDARD_TIMES_T = os.path.join(settings.BASE_DIR, "standardtimes.csv")
STANDARD_TIMES_AWT = os.path.join(settings.BASE_DIR, "standardtimesawt.csv")
class Vividict(dict):
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value



'''
get correct std times file based on surface ALL WEATHER versus TURF
'''
def generatestandardtimes(surface):
    import csv
    newdict = Vividict()
    if surface == 'ALL WEATHER TRACK':
        with open(STANDARD_TIMES_AWT) as csvfile:
            reader2 = csv.DictReader(csvfile)
            for row in reader2:
                times = dict()
                finish, sec1, sec2, sec3, sec4, sec5, sec6, record, weight = row['finish'],row['sec1'],row['sec2'],row['sec3'],row['sec4'],row['sec5'],row['sec6'],row['record'],row['weight']
                racedate, racecoursecode, racedistance ,raceclass = row['racedate'], row['racecoursecode'],row['racedistance'], row['raceclass']
                times =  { 'finish':finish, 'sec1': sec1, 'sec2': sec2, 'sec3':sec3, 'sec4': sec4, 'sec5':sec5, 'sec6': sec6,'record': record,'weight': weight }
                newdict[racedate][racecoursecode][racedistance][raceclass] = times
    else:
        with open(STANDARD_TIMES_T) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                times = dict()
                finish, sec1, sec2, sec3, sec4, sec5, sec6, record, weight = row['finish'],row['sec1'],row['sec2'],row['sec3'],row['sec4'],row['sec5'],row['sec6'],row['record'],row['weight']
                racedate, racecoursecode, racedistance ,raceclass = row['racedate'], row['racecoursecode'],row['racedistance'], row['raceclass']
                times =  { 'finish':finish, 'sec1': sec1, 'sec2': sec2, 'sec3':sec3, 'sec4': sec4, 'sec5':sec5, 'sec6': sec6,'record': record,'weight': weight }
                newdict[racedate][racecoursecode][racedistance][raceclass] = times
    return newdict 

#racedate,racecoursecode,racedistance,raceclass,finish,sec1,sec2,sec3,sec4,sec5,sec6,record,weight
class Simplehkjcspider(scrapy.Spider):
	
    name = "simplehkjcresults"
    allowed_domains = ["hkjc.com", "http://www.hkjc.com", "http://racing.hkjc.com"]

    def __init__(self, date, racecoursecode, *args, **kwargs):
        assert racecoursecode in ['ST', 'HV']
        super(Simplehkjcspider, self).__init__(*args, **kwargs)
        self.hkjc_domain = 'hkjc.com'
        self.racecoursecode = racecoursecode
        self.racedate = date
        self.racedateo = datetime.strptime(self.racedate, '%Y%m%d').date()
        self.avgwinningtimes = dict()
        self.MeetingDrawPlaceCorr = []
        self.meetingrunners = defaultdict(list)
        self.sectionalbaseurl = 'http://www.hkjc.com/english/racing/display_sectionaltime.asp?'
        self.newbaseurl =  'http://racing.hkjc.com/racing/Info/Meeting/Results/English/Local/{date}/{racecoursecode}/'.format(domain=self.hkjc_domain,date=date, racecoursecode=racecoursecode) 
        ##these have been changed
        ##new urls = http://racing.hkjc.com/racing/Info/Meeting/Results/English/Local/20150919/ST/2
        # self.start_urls = [
        #     'http://racing.hkjc.com/racing/Info/Meeting/Results/English/Local/'
        #     '{date}/{racecoursecode}/1'.format(domain=self.hkjc_domain, 
        #         date=date, racecoursecode=racecoursecode),
        # ]

    def start_requests(self):
        #take initial url and extend to cover all races add to start urls
        #create list then return
        urls = list()
        for i in range(1,13):
            yield scrapy.Request( self.newbaseurl+'{0:01d}'.format(i), self.parse)
            # yield scrapy.Request( self.newbaseurl+'{0:02d}'.format(i), self.parse)
    
    # def parse(self, response):
    #     race_paths = response.xpath('//td[@nowrap="nowrap" and @width="24px"]'
    #         '/a/@href').extract()
    #     urls = ['http://{path}'.format(
    #             domain=self.hkjc_domain,
    #             path=path,
    #         ) for path in race_paths
    #     ] + [response.url]
    #     # race 1 is missing
    #     urls.append("http://racing.hkjc.com/racing/Info/Meeting/Results/English/Local/{}/{}/1".format(self.racedate, self.racecoursecode))
    #     for url in urls: 
    #         if int(url.split('/')[-1]) > 9:
    #             racenumber = '{}'.format(url.split('/')[-1])
    #         else:
    #             racenumber = '{}'.format(url.split('/')[-1])
    #         url = self.newbaseurl + racenumber
    #         # print url
    #         request = scrapy.Request(url, callback=self.parse_race)
    #         request.meta['racenumber'] = racenumber
    #         yield request

    def parse(self, response):
        skiprace = False
        norace = response.xpath("//div[@class='contentR1']//text()").extract()
        if norace and norace[0] == 'No Information.':
            skiprace = True

        logger.info('A response from %s just arrived!', response.url)
        if int(response.url.split('/')[-1]) > 9:
            self.racenumber = '{}'.format(response.url.split('/')[-1])
        else:
            self.racenumber = '{}'.format(response.url.split('/')[-1])
        #RACESTATS
        #[u'Class 4 - ', u'1650M - (60-40)', u'Going :', u'WET SLOW', u'SUNBIRD HANDICAP', u'Course :', u'ALL WEATHER TRACK', u'HK$ 800,000', u'Time :', u'(28.53)', u'(52.70)', u'(1.17.43)', u'(1.41.38)', u'\xa0', u'Sectional Time :', u'28.53', u'24.17', u'24.73', u'23.95', u'\xa0Multi Angle Race Replay', u'\xa0\xa0\xa0\xa0', u'\xa0Pass Through Analysis', u'\xa0\xa0\xa0\xa0', u'\xa0Aerial Virtual Replay']

        raceindex_path = re.compile(r'\((\d+)\)')
        #boldFont14 color_white trBgBlue
        ri = response.xpath('//div[@class="boldFont14 color_white trBgBlue"]//text()').extract()
        # newclassdistance = response.xpath('//table[@class ="tableBorder0 font13"]//td[contains(text(), "Class")]//text()').extract()[0]
        newraceinfo = response.xpath('//table[@class ="tableBorder0 font13"]//*[self::td or self::td/span]//text()').extract()
        
        logger.info("newraceinfo {}".format(newraceinfo))
        racedistance = None
        newsectionaltimes = None
        thisracefinishtime = None
        racesurface = None
        raceclass = None
        if ri:
           _raceindex = raceindex_path.findall(ri[0])[0]
        if len(newraceinfo)>0:
            # raceclass 
            raceclass = newraceinfo[0].replace('-', '').strip()
            racegoing = response.xpath('//table[@class ="tableBorder0 font13"]//td[contains(text(),"Going")]/following-sibling::*/text()').extract()[0]
            
            ## poss: "TURF - "B+2" COURSE" or "ALL WEATHER TRACK"
            oracesurface = response.xpath('//table[@class ="tableBorder0 font13"]//td[contains(text(),"Course")]/following-sibling::*/text()').extract()[0]
            newsectionaltimes = response.xpath('//table[@class ="tableBorder0 font13"]//td[text()="Sectional Time :"]/following-sibling::td/text()').extract()
            winningsecs = map(float, newsectionaltimes)
            thisracefinishtime = sum(winningsecs)
            # if len(newraceinfo[1].split(u'-'))>1:
            #     racerating = newraceinfo[1].strip(u'-')[1].strip()
            # else:
            #     racerating = None
            racedistance = newraceinfo[1].split(u'-')[0].replace(u'm', u'').replace(u'M', u'').strip()
            # newsurface, newrailtype = newraceinfo[6].split(u'-')
            
            
            ## poss: "TURF - "B+2" COURSE" or "ALL WEATHER TRACK" railtype for ALL WEATHER is None
            racesurface, railtype =  get_surface_railtype(oracesurface)
            racegoing = get_goingabb(racegoing, racesurface)
            logger.info("raceclass {} racegoing {} oracesurface {}. racesurface {} railtype {}, racedistance {}".format(\
                raceclass, racegoing, oracesurface, racesurface, railtype, racedistance))

        #### DIVIDENDS
        markets = [ 'WIN', 'PLACE', 'QUINELLA', 'QUINELLA PLACE', 'TIERCE', 'TRIO', 'FIRST 4', 'QUARTET','9TH DOUBLE', 'TREBLE', '3RD DOUBLE TRIO' , 'SIX UP', 'JOCKEY CHALLENGE',
            '8TH DOUBLE', '8TH DOUBLE', '2ND DOUBLE TRIO', '6TH DOUBLE', 'TRIPLE TRIO(Consolation)', 'TRIPLE TRIO', '5TH DOUBLE', '5TH DOUBLE', '1ST DOUBLE TRIO', '3RD DOUBLE' ,
            '2ND DOUBLE', '1ST DOUBLE']
        div_table = response.xpath("//td[@class='trBgBlue1 tdAlignL boldFont14 color_white']")
        isdividend = response.xpath("//td[text() ='Dividend']/text()").extract()
        #is isdividend false?
        div_info = defaultdict(list)
        if isdividend:
            for m in markets:
                try:
                    xpathstr = str("//tr[td/text() = 'Dividend']/following-sibling::tr[td/text()=")
                    xpathstr2 = str("]/td/text()")
                    win_divs =response.xpath(xpathstr + "'" + str(m) + "'" + xpathstr2).extract()
                    div_info[win_divs[0]] = [ win_divs[1],win_divs[2] ] 
                    # print response.meta['racenumber']
                except:
                    div_info[m] = None
        # print div_info

        #WHO WON?
        _winners = div_info['WIN']
        _winninghorsenumbers = []
        _winningdivs = []
        for i,w in enumerate(_winners):
            if i%2 ==0: #odd indices are horsenumber, even odds
            #one winner else DH
                _winninghorsenumbers.append(w)
            if i%2 ==1:
                _winningdivs.append(w)
        ##RUNNERS

        sectional_time_url_ = response.xpath('//div[@class="rowDiv15"]/div[@class="rowDivRight"]/a[@href]').extract()
        ##THIS FAILS FOR RACENO 1 why?
        assert sectional_time_url_, "Can't define sectional_time_url from xpath. Try again."

        sectional_time_url = sectional_time_url_[0]
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
        mkt_probs =  [ dec_odds_to_pchance(o) for o in winodds if o != u'---' ]
        for i,x in enumerate(mkt_probs):
            market_probs[i+1]=round(x,2) 
        race_total_prob =  round( (sum( mkt_probs  )), 2)
        # print "sum of market probs {} market_probs {}".format(race_total_prob, market_probs)
        
        # print hplaces, winodds_
        racingincidentreport_ = response.xpath('//tr[td[contains(text(), '
            '"Racing Incident Report")]]/following-sibling::tr/td/text()'
            ).extract()
        racingincidentreport = racingincidentreport_ and racingincidentreport_[0]
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
        trainercodes = OrderedDict()
        horsecode_pat = re.compile(r"horseno=(.+)")
        odd_runners = 1#  or @class='trBgWhite'
        even_runners = 2
        ### WHAT HAPPENS IF THE HORSE HAS A BLANK HORSE NUMBER WHICH MEANS SCRATCHED!?
        for row in response.xpath("//table[@class='tableBorder trBgBlue tdAlignC number12 draggable']//tr[@class='trBgGrey']"):
            horsenos_ = row.xpath('./td[2]/text()').extract()
            horsenos__ = row.xpath('./td[position()=2 and (text() or not(text()))]').extract()
            horsenos[odd_runners] = horsenos_[0] if horsenos_ else None or horsenos__[0] if horsenos__ else None

            places_ = row.xpath('./td[1]/text()').extract()
            places__ = row.xpath('./td[position()=1 and (text() or not(text()))]').extract()
            places[odd_runners] = places_[0] if places_ else None or places__[0] if places__ else None

            # places[odd_runners] = row.xpath('./td[2]/text()').extract()[0] or 99
            _runningpositions = row.xpath('./td[10]/table//td//text()').extract() or []
            _actualwts = row.xpath('./td[6]//text()').extract()[0] or 0
            _jockeycode = row.xpath('./td[4]/a/@href').extract()[0] or 0
            _trainercode = row.xpath('./td[5]/a/@href').extract()[0] or 0
            jockeycodes[odd_runners] = re.match(r'^http://www.hkjc.com/english/racing/jockeyprofile.asp?.*jockeycode=(?P<str>[^&]*)(&.*$|$)', _jockeycode).groupdict()['str']
            trainercodes[odd_runners] = re.match(r'^http://www.hkjc.com/english/racing/trainerprofile.asp?.*trainercode=(?P<str>[^&]*)(&.*$|$)', _trainercode).groupdict()['str']
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

            horsenos_ = row.xpath('./td[2]/text()').extract()
            horsenos__ = row.xpath('./td[position()=2 and (text() or not(text()))]').extract()
            horsenos[even_runners] = horsenos_[0] if horsenos_ else None or horsenos__[0] if horsenos__ else None

            places_ = row.xpath('./td[1]/text()').extract()
            places__ = row.xpath('./td[position()=1 and (text() or not(text()))]').extract()
            places[even_runners] = places_[0] if places_ else None or places__[0] if places__ else None
            # places[even_runners] = row.xpath('./td[2]/text()').extract()[0] or row.xpath('./td[position()=2 and (text() or not(text()))]').extract()[0]
            # horsenos[even_runners] = row.xpath('./td[2]/text()').extract()[0] or row.xpath('./td[position()=2 and (text() or not(text()))]').extract()[0]
            # ###THIS FAILS ON http://racing.hkjc.com/racing/Info/Meeting/Results/English/Local/20160117/ST/01 
            # places[even_runners] = row.xpath('./td[2]/text()').extract()[0] or row.xpath('./td[position()=2 and (text() or not(text()))]').extract()[0]
            #     horsenos[even_runners] = row.xpath('./td[position()=1 and (text() or not(text()))]').extract()[0] or 99
                # places[even_runners] = row.xpath('./td[position()=2 and (text() or not(text()))]').extract()[0] or 99
            _runningpositions = row.xpath('./td[10]/table//td//text()').extract() or []
            _actualwts = row.xpath('./td[6]//text()').extract()[0] or 0
            _jockeycode = row.xpath('./td[4]/a/@href').extract()[0] or 0
            _trainercode = row.xpath('./td[5]/a/@href').extract()[0] or 0
            jockeycodes[even_runners] = re.match(r'^http://www.hkjc.com/english/racing/jockeyprofile.asp?.*jockeycode=(?P<str>[^&]*)(&.*$|$)', _jockeycode).groupdict()['str']
            # [m.group(1) for l in lines for m in [regex.search(l)] if m]
            trainercodes[even_runners] = re.match(r'^http://www.hkjc.com/english/racing/trainerprofile.asp?.*trainercode=(?P<str>[^&]*)(&.*$|$)', _trainercode).groupdict()['str']
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
        winoddsranks = OrderedDict(sorted(winodds.items(), key=lambda t: t[1]))
        winoddsitemsnonulls = [ x for x in winodds.items() if x is not None]
        winoddsrankedhorsenumbers = OrderedDict(sorted(winodds.items(), key=lambda t: t[1]))
        winoddsrankedhorsenumbers = list(winoddsrankedhorsenumbers.items())
        # print "winninghorsenumbers {} _winningdivs {} and top3 horsenumbers in market {}".\
        # format(_winninghorsenumbers,_winningdivs, winoddsrankedhorsenumbers)
        sp1f2f3f_windiv = None
        sp4f5f6f_windiv = None
        sp7f8f9f_windiv = None
        sp10f11f12f_windiv = None

        winoddsrankedhorsenumbers = [ int(x[0]) for x in winoddsrankedhorsenumbers]
        sp1f2f3f = map(str, winoddsrankedhorsenumbers[:3])
        sp4f5f6f= map(str,winoddsrankedhorsenumbers[3:6])
        if len(winoddsrankedhorsenumbers)> 8:
            sp7f8f9f = map(str, winoddsrankedhorsenumbers[6:9])
            if bool(set(_winninghorsenumbers) & set(sp7f8f9f)):
                sp7f8f9f_windiv = _winningdivs
        if len(winoddsrankedhorsenumbers)> 11:   
             sp10f11f12f = map(str, winoddsrankedhorsenumbers[9:12])
             if bool(set(_winninghorsenumbers) & set(sp10f11f12f)):
                 sp10f11f12f_windiv = _winningdivs

        favs_horsenumbers = [ x for x in winoddsranks if x =='1']
        favpos = winoddsranks.keys().index(1)+1 if 1 in winoddsranks.keys() else None
        favodds = min(winodds.values()) if winodds else None
        _winningdivs = map(float, _winningdivs)
        if bool(set(_winninghorsenumbers) & set(sp1f2f3f)) :
            sp1f2f3f_windiv = _winningdivs
        if bool(set(_winninghorsenumbers) & set(sp4f5f6f)):
            sp4f5f6f_windiv = _winningdivs

        # print("_winningdivs {} _winninghorsenumbers {} sp1f2f3f{} sp4f5f6f{} sp7f8f9f{} sp10f11f12f{} sp1f2f3f_windiv{} bool(set(_winninghorsenumbers) & set(sp1f2f3f)){}").\
        # format(_winningdivs,_winninghorsenumbers, sp1f2f3f,sp4f5f6f,sp7f8f9f,sp10f11f12f, sp1f2f3f_windiv,bool(set(_winninghorsenumbers) & set(sp1f2f3f)))

        
        #used to get collections
        #  winninghorsenumbers [u'8'] _winningdivs [u'8', u'269.00'] and top3 horsenumbers in market {2: 2.1, 3: 4.4, 4: 9.6}

        racetrainers = Counter()
        for t in trainercodes.values():
            racetrainers[t] += 1

        '''
        winodds?
        winoddsranks OrderedDict([(1, 3.2), (8, 3.3), (2, 6.3), (9, 10.0), (4, 17.0), (6, 17.0), (7, 20.0), (5, 21.0), (12, 21.0), (3, 26.0), (10, 51.0), (11, 55.0), (13, 99.0)])
        take first winoddsranks.values()[0]
        '''
        print "winodds.values {} and winoddsranks {}".format(winodds.values(), winoddsranks)
        #favhorsenumber = winoddsranks.values()[0]
        #favodds = [ x[1] for x in winodds.values() if x == favhorsenumber]
        #favpos = [ x[1] for x in places.values() if x == unicode(favhorsenumber)]
        #pos of fav horsenumber

        #print "favhorsenumber, {} favodds, favpos {} x {}".format(favhorsenumber, favodds, favpos)

        horsecodes = OrderedDict(sorted(horsecodes.items(), key=lambda t: t[0]))
        trainercodes = OrderedDict(sorted(trainercodes.items(), key=lambda t: t[0]))

        winningjockeycode = jockeycodes.items()[0][1] if jockeycodes else None
        winningtrainercode = trainercodes.items()[0][1] if trainercodes else None

        finishtimes = OrderedDict(sorted(finishtimes.items(), key=lambda t: t[0]))
        print "horsenos: {}, places --> {}, winodds {} plus horsecodes {} and trainercodes {} and finishtimes {} and actualwts{} and jockeycodes{} and runningpositions {}".\
        format(horsenos, places, winodds,horsecodes, finishtimes, actualwts, jockeycodes, trainercodes, runningpositions)
        
        if racedistance and racedistance != 0:
            winningtime = finishtimes.items()[0][1]/float(racedistance) #one and only winningtime
            # self.avgwinningtimes[response.meta['racenumber']] = winningtime
            self.avgwinningtimes[int(self.racenumber)] = winningtime
        runnerslist = horsecodes.values()
        _places = places.values()
        #look for DH
        theresults = []
        ##  'f4_combo_div': [u'4,7,11,12', u'2,224.00'], what about DH?

        if u'DH' in _places:
            #need to create several strings
            theresults.append("-".join(places.values()[:4]))
            
        else:
            theresults.append("-".join(places.values()[:4]))
        print "newsectionaltimes{} thisracefinishtime {}".format(newsectionaltimes,thisracefinishtime)
        print "avgwinningtimes {}, runnerslist {}".format(self.avgwinningtimes, runnerslist)

        # [racedate][racecoursecode][racedistance][raceclass]

        #GET SPEEDS FROM FILE ##
        standardspeeds = Vividict()
        standardspeeds= generatestandardtimes(racesurface)
        # logger.info("**standardspeeds dump {}".format(standardspeeds))

        #get raceclass for speeds
        raceclass = get_raceclassforspeeds(raceclass)

        stdtime_ = standardspeeds['20150906'][self.racecoursecode][racedistance][raceclass]['finish']
        stdtime = stdtime_ or None
        recordtime_ =  standardspeeds['20150906'][self.racecoursecode][racedistance][raceclass]['record']
        recordtime = recordtime_ or None
        logger.info("racesurface {} raceclass {}, stdtime {}, recordtime {}".format(racesurface, raceclass, stdtime, recordtime))

        ##situation where no entry?
        recordtimeperlength = gettimeperlength(racedistance, recordtime)
        stdsec1 =  standardspeeds['20150906'][self.racecoursecode][racedistance][raceclass]['sec1']
        stdsec2 =  standardspeeds['20150906'][self.racecoursecode][racedistance][raceclass]['sec2']
        stdsec3 =  standardspeeds['20150906'][self.racecoursecode][racedistance][raceclass]['sec3']
        stdsec4 =  standardspeeds['20150906'][self.racecoursecode][racedistance][raceclass]['sec4']
        stdsec5 =  standardspeeds['20150906'][self.racecoursecode][racedistance][raceclass]['sec5']
        stdsec6 =  standardspeeds['20150906'][self.racecoursecode][racedistance][raceclass]['sec6']
        # racepace = stdtime = recordime = None
        racepace = None
        if thisracefinishtime and stdtime:
            stdtime = float(stdtime)
            racepace = round(float(thisracefinishtime) - stdtime,2)
        if recordtime:
            try:  
                recordtime = float(recordtime)
            except ValueError:
                recordtime = None
        stdsec1 = stdsec1 and float(stdsec1)
        stdsec2 = stdsec2 and float(stdsec2)
        stdsec3 = stdsec3 and float(stdsec3) 
        if stdsec4:
            stdsec4 = try_float(stdsec4)
        if stdsec5:
            stdsec5 = try_float(stdsec5)
        if stdsec6:
            stdsec6 = try_float(stdsec6)
        #print "standardspeeds loaded ok {}".format(standardspeeds)
        print "todays information racedate {}, racecoursecode {}, racedistance {},raceclass {}, and racepace {}, std {} and record time {}".format\
        (self.racedate,self.racecoursecode,racedistance,raceclass,racepace,stdtime,recordtime)
        ##do horse specific stuff next section

        ##convert to per lengths
        ##give each horse a speedrating horsenumber speedrating
        #rank places based on speed rating

        #THEN DO RACE PACE, 1SEC PACE 2EC PACE ETC
        # for i, row in enumerate(response.xpath("//table[@class='tableBorder trBgBlue tdAlignC number12 draggable']//tr")):
        #   thehorseno = try_int(row.xpath('./td[2]/text()').extract()[0])

        #   if thehorseno != 0:
        #   ##EXCLUDE NON NUMERS
        #       horsenos[i] = thehorseno
        #   theplace = try_int(row.xpath('./td[1]/text()').extract()[0])
        #   if theplace !=0:
        #       places[theplace] = None
        #   # print "win odds?\t"
        #   thewinodds = row.xpath('./td[12]/text()').extract()
        #   if thewinodds != []:
        #       winodds[thewinodds[0]] = None
        #   # thewinodd = row.xpath('/td[12]/text()').extract()[0]
        #   # winodds[thewinodd] = None
        #   # horsenos.add(row.xpath('./td[2]/text()').extract()[0])
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
        #what was the winning sp dividend?
        #winninghorsenumbers [u'8'] _winningdivs [u'8', u'269.00'] and top3 horsenumbers in market {2: 2.1, 3: 4.4, 4: 9.6}


        '''
        sp1f2f3f_div = scrapy.Field()
        sp4f5f6f_div = scrapy.Field()
        sp7f8f9f_div = scrapy.Field()
        sp10f11f12f_div = scrapy.Field()
        '''
        request = scrapy.Request(sectional_time_url, callback=self.parse_sectional_time)
        meta_dict = {
            'racenumber': int(self.racenumber),
            'racedate': self.racedateo,
            'racecoursecode': self.racecoursecode,
            'racedistance': int(racedistance),
            'raceclass': raceclass,
            'racegoing': racegoing,
            'racesurface': racesurface,
            'norunners': norunners,
            'runnerslist': runnerslist,
            'places': places,
            'runningpositions': runningpositions,
            'winodds': winodds,
            'winoddsranks': winoddsranks,
            'actualwts': actualwts,
            'jockeycodes': jockeycodes,
            'winningjockeycode': winningjockeycode,
            'winningtrainercode': winningtrainercode,
            'market_probs': market_probs,
            'race_total_prob': race_total_prob,
            'horsecodes': horsecodes,
            'finishtimes': finishtimes,
            'winningsecs': winningsecs,
            'theresults':theresults,
            'racepace': racepace,
            'racetrainers': racetrainers,
            'favodds': favodds,
            'favpos': favpos,
            'stdtime': stdtime,
            'recordtime': recordtime,
            'recordtimeperlength':recordtimeperlength,
            'stdsec1':stdsec1,
            'stdsec1':stdsec2,
            'stdsec1':stdsec3,
            'stdsec1':stdsec4,
            'stdsec1':stdsec5,
            'stdsec1':stdsec6,
            ##interim solution - todo: create proper sets A1, A2, A3
            'A1topfavs_windiv' : sp1f2f3f_windiv or [],
            'A2midpricers_windiv' : sp4f5f6f_windiv,
            'A3outsiders_windiv' : sp7f8f9f_windiv+ sp10f11f12f_windiv if 
                sp7f8f9f_windiv and sp10f11f12f_windiv else None,
            # 'raceindex': raceindex,
            # 'racegoing': racegoing,
            # 'raceclass': raceclass,
            'horsenos': horsenos,
            'racedistance': racedistance,
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
            'tripletriocons_combo_div': div_info['TRIPLE TRIO(Consolation)'],
            'tripletrio_combo_div': div_info['TRIPLE TRIO'],
        }
        logger.info("This is meta_Dict in parse race {}".format(meta_dict))
        request.meta.update(meta_dict)
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
            horsenos = response.meta['horsenos'].items()
            scratched_horsenos = [ x for x,y in horsenos if y != 99]
            ##Horsecodes is order of place and code includes scratched
            #need a scratched horsecode 
            for x,y in response.meta['horsecodes'].items():
            	if y == horsecode and horsecode not in scratched_horsenos:
            		_hc_idx, hc = x,y
            if _hc_idx:
            	finishtime = response.meta['finishtimes'][_hc_idx]
            	market_prob = response.meta['market_probs'].get(_hc_idx)
            	jockeycode = response.meta['jockeycodes'][_hc_idx]
            	place = response.meta['places'][_hc_idx]
            	runningpositions = response.meta['runningpositions'][_hc_idx]
            	winodds = response.meta['winodds'][_hc_idx]
            #use index to get finishtime, jockeycode, place, winodds, market_probs
            	for i,x in enumerate(response.meta['winoddsranks'].items()):
            		if x[1] == winodds:
            			winoddsrank = i+1
            #with winoddsrank reverse lookup o winodds

            ##TIMES finishtime is it float? sec_timelist_len
            ##versus recordtime
            hls = gettimeperlength(response.meta['racedistance'], finishtime)
            horsespeedrating =  getmetaspeedrank(hls,response.meta['recordtimeperlength'])


            yield items.SimplehkjcresultsItem(

            racedistance = response.meta['racedistance'],
            raceclass=  response.meta['raceclass'],
            racegoing =  response.meta['racegoing'],
            racesurface = response.meta['racesurface'],
            racenumber= int(self.racenumber),
            horsenumber=horsenumber,
            horsecode=horsecode,
            jockeycode=jockeycode,
            finishtime=finishtime,
            theresults = response.meta['theresults'],
            #runnerslist = response.meta['runnerslist'],
            runningpositions= runningpositions,
            market_prob=market_prob,
            race_total_prob =response.meta['race_total_prob'],
            place=place,
            winoddsrank=winoddsrank,
            horsereport=horsereport,
            sec_timelist = sec_timelist,
            marginsbehindleader= marginsbehindleader,
            racedate=self.racedate,
            racecoursecode=self.racecoursecode,
            # winodds = response.meta['winodds'][horsenumber],
            winodds = winodds,
            racepace =response.meta['racepace'],
            racetrainers = response.meta['racetrainers'],
            winningsecs= response.meta['winningsecs'],
            horsespeedrating= horsespeedrating,
            stdtime= response.meta['stdtime'],
            recordtime= response.meta['recordtime'],
            recordtimeperlength= response.meta['recordtimeperlength'],
            #replace these 3
            A1topfavs_windiv= response.meta['A1topfavs_windiv'],
            A2midpricers_windiv= response.meta['A2midpricers_windiv'],
            A3outsiders_windiv= response.meta['A3outsiders_windiv'],
            winningtrainercode = response.meta['winningtrainercode'],
            winningjockeycode = response.meta['winningjockeycode'],
            favpos= response.meta['favpos'],
            favodds = response.meta['favodds'],
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
            tripletriocons_combo_div=response.meta['tripletriocons_combo_div'],
            tripletrio_combo_div=response.meta['tripletrio_combo_div']
            )

			# yield response

    '''
    racedate, racenumber,
    timestats esp paceofrace
    '''



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