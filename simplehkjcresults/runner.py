from subprocess import Popen
from datetime import datetime
import time
import settings
import os

def runSpider(rc,rd):
    # scrapy crawl simpleraceday -a racecoursecode=HV -a racedate=20151007
    env_path = os.path.join(settings.ROOT_DIR, 'env', 'bin', 'scrapy')
    p = Popen([os.path.exists(env_path) and env_path or "scrapy", "crawl", 
		"simplehkjcresults", "-a", "racecoursecode={}".format(rc), "-a",
    	"date={}".format(rd)], cwd=settings.BASE_DIR)
    stdout, stderr = p.communicate()
    time.sleep(15)


hkmeetsrunners = {
	"20151004": 133, #includes 1 scratch
	"20151025": 138, #includes 1 scratch

}

##dictionary of rd:rc
hkmeets = {
"20150906": "ST",
"20150902": "HV",
"20150913": "ST",
"20150916": "HV",
"20150919": "ST",
"20150923": "HV",
"20150928": "HV",
"20151004": "ST",
"20151001": "ST",
"20151004": "ST",
"20151007": "HV",
"20151010": "ST",
"20151014": "HV",
"20151018": "ST",
"20151022": "HV", #expecting 12+12+12+12+12+12+11+1+12
"20151025": "ST", #expecting 133 runners
}

# hkmeets = {
# "20151010": "ST",
# "20151007": "HV",
# "20151004": "ST",
# "20151022": "HV"
# }

##implement as queue and return no of items returned compare 
for rd,rc in hkmeets.items():
    runSpider(rc, rd)
