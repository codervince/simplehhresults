# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SimplehkjcresultsItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    racedate = scrapy.Field()
    racecoursecode = scrapy.Field()
    racenumber= scrapy.Field()
    theresults= scrapy.Field()
    race_total_prob = scrapy.Field()
    runnerslist = scrapy.Field()
    raceclass = scrapy.Field()
    norunners =  scrapy.Field()
    horsecode = scrapy.Field()
    horsenumber = scrapy.Field()
    horsereport= scrapy.Field()
    finishtime=scrapy.Field()
    market_prob=scrapy.Field()
    place=scrapy.Field()
    jockeycode=scrapy.Field()
    winodds=scrapy.Field()
    winoddsrank=scrapy.Field()
    sec_timelist= scrapy.Field()
    marginsbehindleader= scrapy.Field()
    runningpositions= scrapy.Field()

    win_combo_div = scrapy.Field()
    place_combo_div = scrapy.Field()
    qn_combo_div = scrapy.Field()
    qnp_combo_div = scrapy.Field()
    tce_combo_div = scrapy.Field()
    trio_combo_div = scrapy.Field()
    f4_combo_div = scrapy.Field()
    qtt_combo_div = scrapy.Field()
    dbl9_combo_div = scrapy.Field()
    dbl8_combo_div = scrapy.Field()
    dbl7_combo_div = scrapy.Field()
    dbl6_combo_div = scrapy.Field()
    dbl5_combo_div = scrapy.Field()
    dbl4_combo_div = scrapy.Field()
    dbl3_combo_div = scrapy.Field()
    dbl2_combo_div = scrapy.Field()
    dbl1_combo_div = scrapy.Field()
    dbl10_combo_div = scrapy.Field()
    dbltrio1_combo_div = scrapy.Field()
    dbltrio2_combo_div = scrapy.Field()
    dbltrio3_combo_div = scrapy.Field()
    sixup_combo_div = scrapy.Field()
    jockeychallenge_combo_div = scrapy.Field()


