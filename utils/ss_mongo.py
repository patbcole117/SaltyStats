from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.results import InsertOneResult
from enum import Enum

DB_TYPE = Enum('DB_TYPE', ['PRODUCTION', 'DEVELOPMENT'])
DB_LOCALE = Enum('DB_LOCALE', ['LOCAL', 'REMOTE'])

class SaltyDB:
    def __init__(self, db_locale, db_type, db_user, db_pw, db_url):
        self.client = MongoClient(f'mongodb+srv://{db_user}:{db_pw}@{db_url}.4sgvde0.mongodb.net/?retryWrites=true&w=majority', server_api=ServerApi('1')) if db_locale == DB_LOCALE.REMOTE.name else MongoClient('mongodb://localhost:27017/', server_api=ServerApi('1'))
        self.db_type = db_type
        try:
            self.client.admin.command('ping')
            print(f'Connected to MongoDB!')
        except Exception as e:
            print(f'Failed to connect to MongoDB!')

    def get_all_bouts(self, filter={}):
        if self.db_type == DB_TYPE.PRODUCTION.name:
            return self.client.SaltyStats.bouts.find(filter)
        elif self.db_type == DB_TYPE.DEVELOPMENT.name:
            return self.client.SaltyStatsDev.bouts.find(filter)

    def get_all_fighters(self, filter={}):
        if self.db_type == DB_TYPE.PRODUCTION.name:
            return self.client.SaltyStats.fighters.find(filter)
        elif self.db_type == DB_TYPE.DEVELOPMENT.name:
            return self.client.SaltyStatsDev.fighters.find(filter)

    def get_bout(self, bout: dict):
        if self.db_type == DB_TYPE.PRODUCTION.name:
            return self.client.SaltyStats.bouts.find_one({"$and": [{"p1name": bout["p1name"]}, {"p2name": bout["p2name"]}, {"p1total": bout["p1total"]}, {"p2total": bout["p2total"]}]})
        elif self.db_type == DB_TYPE.DEVELOPMENT.name:
            return self.client.SaltyStatsDev.bouts.find_one({"$and": [{"p1name": bout["p1name"]}, {"p2name": bout["p2name"]}, {"p1total": bout["p1total"]}, {"p2total": bout["p2total"]}]})
        
    def get_fighter(self, name: str):
        if self.db_type == DB_TYPE.PRODUCTION.name:
            return self.client.SaltyStats.fighters.find_one({"name": name})
        elif self.db_type == DB_TYPE.DEVELOPMENT.name:
            return self.client.SaltyStatsDev.fighters.find_one({"name": name})

    def insert_bout(self, bout: dict) -> InsertOneResult:
        try:
            if self.db_type == DB_TYPE.PRODUCTION.name:
                self.client.SaltyStats.bouts.insert_one(bout)
            elif self.db_type == DB_TYPE.DEVELOPMENT.name:
                self.client.SaltyStatsDev.bouts.insert_one(bout)
            return True
        except Exception as e:
            print(f'MongoDB Exception!\n{e}')
            return False

    def update_bout(self, p1name: str, p2name: str, p1total: int, p2total: int, bout: dict):
        try:
            if self.db_type == DB_TYPE.PRODUCTION.name:
                self.client.SaltyStats.bouts.update_one({"$and": [{"p1name": p1name}, {"p2name": p2name}, {"p1total": p1total}, {"p2total": p2total}]}, {"$set": bout}, upsert=False)
            elif self.db_type == DB_TYPE.DEVELOPMENT.name:
                self.client.SaltyStatsDev.bouts.update_one({"$and": [{"p1name": p1name}, {"p2name": p2name}, {"p1total": p1total}, {"p2total": p2total}]}, {"$set": bout}, upsert=False)
            return True
        except Exception as e:
            print(f'MongoDB Exception!\n{e}')
            return False
        
    def upsert_fighter(self, name: str, fighter: dict):
        try:
            if self.db_type == DB_TYPE.PRODUCTION.name:
                self.client.SaltyStats.fighters.update_one({"name": name}, {"$set": fighter}, upsert=True)
            elif self.db_type == DB_TYPE.DEVELOPMENT.name:
                self.client.SaltyStatsDev.fighters.update_one({"name": name}, {"$set": fighter}, upsert=True)
            return True
        except Exception as e:
            print(f'MongoDB Exception!\n{e}')
            return False
        
    def upsert_fighter_streak(self, name: str, fighter: dict):
        try:
            if self.db_type == DB_TYPE.PRODUCTION.name:
                self.client.SaltyStats.fighters.update_one({"name": name}, {"$set": {"streak": fighter["streak"], "max_streak": fighter["max_streak"]}}, upsert=True)
            elif self.db_type == DB_TYPE.DEVELOPMENT.name:
                self.client.SaltyStatsDev.fighters.update_one({"name": name}, {"$set": fighter}, upsert=True)
            return True
        except Exception as e:
            print(f'MongoDB Exception!\n{e}')
            return False