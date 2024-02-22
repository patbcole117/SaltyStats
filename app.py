import json
from obj.bout import Bout, BoutStatus, DataSource
from obj.fighter import Fighter
from utils.ss_conf import Config
from utils.ss_mongo import SaltyDB
import time
import sqlite3
import datetime
from gpt.predictor import PredictorFactory
import requests

ELO_K_VALUE = 80

c = Config()
db = SaltyDB(c.db_locale, c.db_type, c.db_user, c.db_pw, c.db_url)
pf = PredictorFactory()

def main():
    run()

def run():    
    #pmodels = []
    pmodels = [pf.create_predictor('Elo', 'Elo'), pf.create_predictor('Gpt', '20240219_salty_gpt_full')]
    while True:
        time.sleep(c.sleep)
        data = requests.get(c.saltyurl)
        c.log.debug(f'Status Code: {data.status_code}')
        if data.status_code == 200:
            bout = Bout(saltydata=json.loads(data.content))
            c.log.debug(f'bout.__dict__: {bout.__dict__}')
            status = bout.get_status()
            if status == BoutStatus.OPEN:
                prom = format_prompt(bout)
                print(prom)
                for p in pmodels:
                    p.predict(prom) if not p.ready else c.log.debug(f'Prediction {p.name}: {p.pred} {(p.confidence):.2f}%')
            elif status == BoutStatus.LOCKED:
                continue
            elif status == BoutStatus.UNDEFINED:   
                continue      
            else:
                if ingest_bout(bout):
                    p1r, p2r, p1, p2 = ingest_fighters(bout)
                    if p1r and p2r:
                        c.log.info(f'New Bout! ***[ {bout.p1name} ]*** vs {bout.p2name}') if bout.get_status() == BoutStatus.RED_WIN else c.log.info(f'New Bout! {bout.p1name} vs ***[ {bout.p2name} ]***')
                        for p in pmodels:
                            if p.ready:
                                p.bout, p.p1, p.p2 = bout, p1, p2
                                #ingest_pred(p)
                                c.log.info(f'Prediction {p.name}: {p.pred} {(p.confidence):.2f}%')
                p.flush()

def ingest_bout(bout: Bout) -> bool:
    if  db.get_bout(bout.__dict__) is None:
        return db.insert_bout(bout.__dict__)

def ingest_fighters(bout: Bout):
    p1_data = db.get_fighter(name=bout.p1name)
    p2_data = db.get_fighter(name=bout.p2name)
    c.log.debug(f'p1_data: {p1_data}')
    c.log.debug(f'p2_data: {p2_data}')

    p1 = Fighter(name=bout.p1name) if p1_data is None else Fighter(p1_data)
    p2 = Fighter(name=bout.p2name) if p2_data is None else Fighter(p2_data)
    c.log.debug(f'FIGHTER BEFORE p1 = {p1.__dict__}')
    c.log.debug(f'FIGHTER BEFORE p2 = {p2.__dict__}')
    p1_old_elo = p1.elo
    p2_old_elo = p2.elo

    if bout.get_status() == BoutStatus.RED_WIN:
        elos = calculate_elos(p1.elo, p2.elo)
        p1.wins += 1
        p2.losses += 1
        p1.elo = elos[0]
        p2.elo = elos[1]
        p2.streak = 0
        p1.streak += 1
        if bout.p2total > bout.p1total:
            p1.upsets += 1
        if p1.streak > p1.max_streak:
            p1.max_streak = p1.streak  
    elif bout.get_status() == BoutStatus.BLUE_WIN:
        elos = calculate_elos(p2.elo, p1.elo)
        p2.wins += 1
        p1.losses += 1
        p2.elo = elos[0]
        p1.elo = elos[1]
        p1.streak = 0
        p2.streak += 1
        if bout.p1total > bout.p2total:
            p2.upsets += 1
        if p2.streak > p2.max_streak:
            p2.max_streak = p2.streak

    p1.bets += bout.p1total
    p2.bets += bout.p2total
    p1.total_bouts += 1
    p2.total_bouts += 1
    p1.date_last_seen = bout.timestamp
    p2.date_last_seen = bout.timestamp
    if bout.timestamp < p1.date_of_debut:
            p1.date_of_debut = bout.timestamp
    if bout.timestamp < p2.date_of_debut:
            p2.date_of_debut = bout.timestamp

    c.log.debug(f'FIGHTER AFTER p1 = {p1.__dict__}')
    c.log.debug(f'FIGHTER AFTER p2 = {p2.__dict__}')

    p1_res = db.upsert_fighter(p1.name, p1.__dict__)
    if p1_res and p1_data is None:
         c.log.debug(f'NEW FIGHTER: {p1.name} {p1_old_elo} -> {p1.elo}')
    elif p1_res and p1_data is not None:
         c.log.debug(f'UPDATED FIGHTER: {p1.name} {p1_old_elo} -> {p1.elo}')
    else:
        c.log.error(f'p1_res: {p1_res}')
    
    p2_res = db.upsert_fighter(p2.name, p2.__dict__)
    if p2_res and p2_data is None:
         c.log.debug(f'NEW FIGHTER: {p2.name} {p2_old_elo} -> {p2.elo}')
    elif p2_res and p2_data is not None:
         c.log.debug(f'UPDATED FIGHTER: {p2.name} {p2_old_elo} -> {p2.elo}')
    else:
        c.log.error(f'p2_res: {p2_res}')

    return p1_res, p2_res, p1, p2


def calculate_elos(winner_elo, loser_elo) -> list[int]:
    rw = 10**(winner_elo/400)
    rl = 10**(loser_elo/400)

    ew = rw/(rw+rl)
    el = rl/(rw+rl)

    winner_elo += ELO_K_VALUE*(1-ew)
    loser_elo += ELO_K_VALUE*(0-el)

    return [round(winner_elo, 2), round(loser_elo, 2)]

def format_prompt(bout: Bout):
    p1_data = db.get_fighter(name=bout.p1name)
    p2_data = db.get_fighter(name=bout.p2name)

    p1 = Fighter(name=bout.p1name) if p1_data is None else Fighter(p1_data)
    p2 = Fighter(name=bout.p2name) if p2_data is None else Fighter(p2_data)

    data = {}
    data["p1name"]          = p1.name
    data["p1elo"]           = p1.elo
    data["p1wins"]          = p1.wins
    data["p1losses"]        = p1.losses
    data["p1streak"]        = p1.streak
    data["p1upsets"]        = p1.upsets
    data["p1total_bouts"]   = p1.total_bouts

    data["p2name"]          = p2.name
    data["p2elo"]           = p2.elo
    data["p2wins"]          = p2.wins
    data["p2losses"]        = p2.losses
    data["p2streak"]        = p2.streak
    data["p2upsets"]        = p2.upsets
    data["p2total_bouts"]   = p2.total_bouts

    data["mode"] = bout.mode

    return data

'''
BEGIN Fix streak miscalculation.
'''
def reset_streak():
    fighters = db.get_all_fighters()
    for f in fighters:
        c.log.debug(f'BEGIN {f}')
        fighter = Fighter(f)
        fighter.streak = 0
        fighter.max_streak = 0
        db.upsert_fighter(fighter.name, fighter.__dict__)

def fix_streak(b: Bout):
    c.log.debug(f'BEGIN INGEST {b.__dict__}')
    p1_data = db.get_fighter(name=b.p1name)
    p2_data = db.get_fighter(name=b.p2name)
    c.log.debug(f'SELECT {b.p1name} FROM FIGHTERS -> {p1_data}')
    c.log.debug(f'SELECT {b.p2name} FROM FIGHTERS -> {p2_data}')

    p1 = Fighter(p1_data)
    p2 = Fighter(p2_data)

    if b.get_status() is BoutStatus.RED_WIN:
        p2.streak = 0
        p1.streak += 1
        if p1.streak > p1.max_streak:
            p1.max_streak = p1.streak  
    elif b.get_status() is BoutStatus.BLUE_WIN:
        p1.streak = 0
        p2.streak += 1
        if p2.streak > p2.max_streak:
            p2.max_streak = p2.streak

    db.upsert_fighter_streak(p1.name, p1.__dict__)
    db.upsert_fighter_streak(p2.name, p2.__dict__)
'''
END Fix streak miscalculation.
'''
'''
BEGIN Sideload from another MongoDB.
'''
def sideload_mongo():
    bouts = db.get_all_bouts()
    for b in bouts:
        bout = Bout(b)
        if bout.is_valid():
            ingest_bout(bout)
            #fix_streak(bout)
'''
END Sideload from another MongoDB.
'''
'''
BEGIN Tyler's dataset import functions.
'''
def ingest_tylers_data():
    con = sqlite3.connect("saltydbbackup.db")
    cur = con.cursor()
    res = cur.execute("SELECT * FROM matchTable")
    rows = res.fetchall()
    threads = []
    for i in range(len(rows)):
        try:
            row_next = rows[i+1]
        except:
            row_next = None
        bout_data = tyler_ingest(rows[i], row_next)
        if bout_data is not None:
            b = Bout(bout_data)
            c.log.debug(f'TYLER 2. {bout_data}')
            c.log.debug(f'TYLER 3. {b.__dict__}')
            ingest_bout(b)
        else:
            print(c.banner)
            print(c.banner)
            print(c.banner)
        
def tyler_ingest(row, row_next):
    c.log.debug(f'TYLER 1. {row}')
    if tyler_row_is_valid(row):
        bout_data = {
            "p1name": row[0],
            "p2name": row[1],
            "p1total": row[2],
            "p2total": row[3],
            "status": tyler_init_status(row),
            "alert": tyler_init_alert(row, row_next),
            "x": 1,
            "remaining": "",
            "mode": tyler_init_mode(row),
            "is_upset": "NaN",
            "is_final": "NaN",
            "data_src": DataSource.TYLER.name,
            "timestamp": datetime.datetime.strptime(row[6], '%m/%d/%Y, %I:%M:%S %p')
        }
        return bout_data
    return None

def tyler_init_status(row):
    return "1" if row[4] == row[0] else "2"

def tyler_init_alert(row, row_next):
    if row[5] == "Tournament Final":
        return "Exhibition mode start!"
    if (row_next is not None) and (row_next[5] == "Tournament") and (row[5] == "Matchmaking"):
        return "Tournament mode start!"
    return ""

def tyler_init_mode(row):
    return "NORMAL" if row[5] == "Matchmaking" else "TOURNAMENT"

def tyler_row_is_valid(row):
    for i in range(6):
        if row[i] is None:
            return False
    return True
'''
ENDTyler's dataset import functions.
'''

if __name__ == "__main__":
    main()