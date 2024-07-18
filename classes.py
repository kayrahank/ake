class Personel():
    def __init__(self, name, surname, place, lastEdit, team, mission):
        self.name = name
        self.surname = surname
        self.place = place
        self.lastEdit = lastEdit
        self.team = team
        self.mission = mission
    
    def getName(self): return self.name

    def getSurname(self): return self.surname

    def getPlace(self): return self.place

    def getLastEdit(self): return self.lastEdit

    def getMission(self): return self.mission
