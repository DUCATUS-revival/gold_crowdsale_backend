from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from settings import CONFIG

Base = automap_base()
engine = create_engine(CONFIG['db']['url'])
Base.prepare(engine, reflect=True)

TokenPurchase = Base.classes.purchases_tokenpurchase
Transfers = Base.classes.transfers_tokentransfer

session = Session(engine)
