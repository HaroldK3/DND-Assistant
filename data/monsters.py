from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Monster(Base):
    __tablename__= "monsters"

    index = Column(Integer, primary_key = True)
    name = Column(String)
    url = Column(String)
    CR = Column(String)
    category = Column(String)
    size = Column(String)
    AC = Column(Integer)
    HP = Column(Integer)
    speed = Column(String)
    alignment = Column("align", String)
    legendary = Column(Boolean)
    source = Column(String)
    strength = Column("str", Integer)
    dexterity = Column("dex", Integer)
    constitution = Column("con", Integer)
    intelligence = Column("int", Integer)
    wisdom = Column("wis", Integer)
    charisma = Column("cha", Integer)
    def __repr__(self):
        return f"Name: {self.name}\nPage URL: {self.url}\nChallenge Rating: {self.CR} Category: {self.category}\nSize: {self.size}\nAC: {self.AC}\nHP: {self.HP}\nSpeed: {self.speed}\nAlignment: {self.alignment}\nLegendary: {self.legendary}\nSource: {self.source}\nSTR: {self.strength}\nDEX: {self.dexterity}\nCON: {self.constitution}\nINT: {self.intelligence}\nWIS: {self.wisdom}\nCHA: {self.charisma}"
    
    # Data used for monster manual provided by Kaggle user mrpantherson: https://www.kaggle.com/datasets/mrpantherson/dnd-5e-monsters?resource=download