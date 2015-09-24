
##A SIMPLE RESULTS AND DIVIDEND GRABBER FOR HKJC RESULTS

##HOW TO RUN IT

scrapy crawl simplehkjcspider -a racecoursecode=ST -a date=20150919

* This is what we need and nothing more?

racedate = scrapy.Field()
    racecoursecode = scrapy.Field()
    racenumber= scrapy.Field()
    raceclass = scrapy.Field()
    first= scrapy.Field()
    second= scrapy.Field()
    third= scrapy.Field()
    fourth= scrapy.Field()
    rest= scrapy.Field()
    horsecodes = scrapy.Field()
    horsetimes = scrapy.Field()
    horserps = scrapy.Field()
    horsewinodds = scrapy.Field()
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