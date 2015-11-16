# -*- coding: utf-8 -*-
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, scoped_session,exc, create_session
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy import *
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import settings
import items
import sqlalchemy
from collections import *
# from simplehkresultd.items import *
#from simplehkresultd.models import *
from simplehkjcresults import models
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
ENGINE = models.get_engine()

def get_or_create_pl(model, item):

    '''
    indexfields should be a dict of the uniqur fields for lookup
    '''

    get_params = lambda model, item: {c.name: item.get(c.name) 
        for c in model.__table__.columns if c.name != 'id'}
    get_unique = lambda model, item: {c.name: item.get(c.name) 
        for c in model.__table__.columns if c.name != 'id' and getattr(c, 'unique')}
    get_unique_together = lambda model, item: [{c.name: item.get(c.name) 
        for c in model.__table_args__[0].columns} 
        for targ in model.__table_args__ if isinstance(
        targ, sqlalchemy.UniqueConstraint)]

    session = Session(bind=ENGINE)

    instance = None
    unique = get_unique(model, item)
    for k, v in unique.iteritems():
        query = session.query(model).filter_by(**{k: v})
        instance = query.first()
        if instance:
            break

    if not instance:
        unique_together = get_unique_together(model, item)
        for params in unique_together:
            query = session.query(model).filter_by(**params)
            instance = query.first()
            if instance:
                break

    created = False
    kwargs = get_params(model, item)
    params = dict(
        (k, v) for k, v in kwargs.iteritems()
        if not isinstance(v, ClauseElement))
    if not instance:
        #params.update(defaults)
        instance = model(**params)
    else:
        for k, v in params.iteritems():
            setattr(instance, k, v)

    try:
        session.add(instance)
        session.commit()
        created = True
    except Exception:
        session.close()
        raise

    session.refresh(instance)  # Refreshing before session close
    session.close()
    return instance


class SimpleHKJCResultsPipelineTemp(object):

    def __init__(self, *args, **kwargs):
        super(SimpleHKJCResultsPipelineTemp, self).__init__(*args, **kwargs)
        engine = create_engine(URL(**settings.DATABASE))
        models.Base.metadata.create_all(engine)

    def process_item(self, item, spider):

        if not isinstance(item, items.SimplehkjcresultsItem):
            return

        horse = get_or_create_pl(models.Horse, item)
        jockey = get_or_create_pl(models.Jockey, item)
        raceday = get_or_create_pl(models.Raceday, item)
 
        item['raceday_id'] = raceday.id
        race = get_or_create_pl(models.Race, item)

        item['jockey_id'] = jockey.id
        item['horse_id'] = horse.id
        item['race_id'] = race.id
        get_or_create_pl(models.Runner, item)


class SimpleHKJCResultsPipeline(object):

    def __init__(self):
        Base = automap_base()
        engine = create_engine(URL(**settings.DATABASE))
        # create_tables(engine)    
        Base.prepare(engine, reflect=True)

        Raceday = Base.classes.raceday
        Race = Base.classes.race
        Runner = Base.classes.runner
        Owner = Base.classes.owner
        Trainer = Base.classes.trainer
        Jockey = Base.classes.jockey
        Horse = Base.classes.horse

        self.Session = sessionmaker(bind=engine)
        self.cache = defaultdict(lambda: defaultdict(lambda: None)) #necessary?
        session = create_session(bind=engine)
        
        testlist = session.query(Raceday).all()     
        for test in testlist:  
            print test.racedate

    # write to rd_race
    def process_item(self, item, spider):
        session = self.Session()
        #which item?
        # if isinstance(item, HorseItem):
            # iscreated = False
        '''
        horsenumber = db.Column(db.Integer)
	    todaysrating = db.Column(db.Integer)
	    lastwonat= db.Column(db.Integer)
	    isMaiden = db.Column(db.Boolean)
	    seasonstakes =db.Column(db.Float)
	    draw = db.Column(db.Integer)
	    isScratched = db.Column(db.Boolean)
	    priority = db.Column(db.String(100))
	    gear = db.Column(db.String(20))
        '''
        #creating runner object nested
        #or dictionary

        #get racedays
        raceday_id = get_or_create_pl(
                Raceday,{racedate:item.get("racedate", None),racecoursecode:item.get("racecoursecode", None)}  ,
                    racedate= item.get("racedate", None),
                    racecoursecode= item.get("RacecourseCode", None),
                    runnerslist=RaceSpider.code_set
                   )
        print raceday_id
        return item
