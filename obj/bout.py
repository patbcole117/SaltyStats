from enum import Enum
import datetime

DataSource = Enum('DataSource', ['SALTY', 'TYLER', 'OTHER'])
BoutStatus = Enum('BoutStatus', ['RED_WIN', 'BLUE_WIN', 'OPEN', 'LOCKED', 'UNDEFINED'])
BoutMode = Enum('BoutMode', ['NORMAL', 'TOURNAMENT', 'EXHIBITION'])

class Bout:
    def __init__(self, saltydata=None, sideload=None):
        if saltydata is None:
            self.p1name     = sideload["p1name"]
            self.p2name     = sideload["p2name"]
            self.p1total    = sideload["p1total"]
            self.p2total    = sideload["p2total"]
            self.status     = sideload["status"]
            self.alert      = sideload["alert"]
            self.x          = sideload["x"]
            self.remaining  = sideload["remaining"]
            self.mode       = self.init_mode(sideload)
            self.is_upset   = self.init_upset()
            self.is_final   = self.init_final()
            self.data_src   = sideload["data_src"]   
            self.timestamp  = sideload["timestamp"].replace(tzinfo=datetime.timezone.utc)
        else:
            self.p1name     = saltydata["p1name"]
            self.p2name     = saltydata["p2name"]
            self.p1total    = int(saltydata["p1total"].replace(",", ""))
            self.p2total    = int(saltydata["p2total"].replace(",", ""))
            self.status     = saltydata["status"]
            self.alert      = saltydata["alert"]
            self.x          = saltydata["x"]
            self.remaining  = saltydata["remaining"]
            self.mode       = self.init_mode() 
            self.is_upset   = self.init_upset()
            self.is_final   = self.init_final()
            self.data_src   = DataSource.SALTY.name
            self.timestamp  = datetime.datetime.now(datetime.timezone.utc)

    def __eq__(self, bout):
        if isinstance(bout, Bout):
            return(self.p1name, self.p2name, self.p1total, self.p2total) == (bout.p1name, bout.p2name, bout.p1total, bout.p2total)
        return False

    def init_mode(self, data=None):
        if "16 characters are left in the bracket!" in self.remaining: return BoutMode.NORMAL.name
        if "characters are left in the bracket!" in self.remaining: return BoutMode.TOURNAMENT.name
        if "FINAL ROUND! Stay tuned for exhibitions after the tournament!" in self.remaining: return BoutMode.TOURNAMENT.name
        if "25 exhibition matches left!" in self.remaining: return BoutMode.TOURNAMENT.name
        if "exhibition matches left!" in self.remaining: return BoutMode.EXHIBITION.name
        if "Matchmaking mode will be activated" in self.remaining: return BoutMode.EXHIBITION.name
        return BoutMode.NORMAL.name
    
    def init_upset(self):
        if self.p1total > self.p2total and self.get_status() is BoutStatus.BLUE_WIN:
            return True
        if self.p2total > self.p1total and self.get_status() is BoutStatus.RED_WIN:
            return True
        return False
        
    def init_final(self):
        return "Exhibition mode start!" in self.alert

    def get_status(self) -> BoutStatus:
        match self.status:
            case "1": return BoutStatus.RED_WIN
            case "2": return BoutStatus.BLUE_WIN
            case "open": return BoutStatus.OPEN
            case "locked": return BoutStatus.LOCKED
            case _: return BoutStatus.UNDEFINED
