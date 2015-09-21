import re

from scrapy.dupefilters import RFPDupeFilter


class CustomFilter(RFPDupeFilter):

    def request_seen(self, request, *args, **kwargs):
        repeat = super(self.__class__, self).request_seen(request, *args, **kwargs)
        url_pattern = '^http://racing.hkjc.com/racing/Info/Meeting/Results/'\
            'English/Local/\d{8}/(ST|HV)/\d+$'
        dont_filter = re.match(url_pattern, request.url)
        return False if dont_filter else repeat
