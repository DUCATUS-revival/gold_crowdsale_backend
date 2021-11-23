from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from settings import CONFIG

Base = automap_base()
engine = create_engine(CONFIG['db']['url'])
Base.prepare(engine, reflect=True)

BlockchainAccount = Base.classes.accounts_blockchainaccount
# Transfers = Base.classes.transfers_

session = Session(engine)
