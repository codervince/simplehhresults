from subprocess import Popen
from datetime import datetime
import time

def runSpider(rc,rd):
	# scrapy crawl simpleraceday -a racecoursecode=HV -a racedate=20151007
    p = Popen(["scrapy", "crawl", "simplehkjcresults", "-a", "racecoursecode={}".format(rc), "-a",\
    	"date={}".format(rd)]\
    	,cwd="/home/vmac/simplehkjcresults/simplehkjcresults")
    stdout, stderr = p.communicate()
    time.sleep(15)


##dictionary of rd:rc
hkmeets = {
"20151004": "ST"
}

# hkmeets = {
# "20151010": "ST",
# "20151007": "HV",
# "20151004": "ST",
# "20151022": "HV"
# }

for rd,rc in hkmeets.items():
	runSpider(rc, rd)
