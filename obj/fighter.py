import datetime

FIGHTER_ELO_DEFAULT = 2000

class Fighter:
    def __init__(self, data=None, name=None):
        if data is not None:
            self.name           = data["name"]
            self.wins           = data["wins"]
            self.losses         = data["losses"]
            self.bets           = data["bets"]
            self.total_bouts    = data["total_bouts"]
            self.elo            = data["elo"]
            self.upsets         = data["upsets"]
            self.streak         = data["streak"]
            self.max_streak     = data["max_streak"]
            self.date_last_seen = data["date_last_seen"].replace(tzinfo=datetime.timezone.utc)
            self.date_of_debut  = data["date_of_debut"].replace(tzinfo=datetime.timezone.utc)
        else:
            self.name           = name
            self.wins           = 0
            self.losses         = 0
            self.bets           = 0
            self.total_bouts    = 0
            self.elo            = FIGHTER_ELO_DEFAULT
            self.upsets         = 0
            self.streak         = 0
            self.max_streak     = 0
            self.date_last_seen = datetime.datetime.now(datetime.timezone.utc)
            self.date_of_debut  = datetime.datetime.now(datetime.timezone.utc)

            