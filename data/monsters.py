from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Monster(Base):
    __tablename__= "monsters"

    index = Column(Integer, primary_key = True)
    name = Column(String)
    Type = Column(String)
    size = Column(String)
    AC = Column(Integer)
    HP = Column(Integer)
    speed = Column(String)
    alignment = Column("align", String)
    legendary = Column(Boolean)
    source = Column(String)
    # While the actual column in the DB is listed as "str", I had to include that in the Column arguments instead of the name due to python processing "str" as a string object instead of the name. --SM
    strength = Column("str", Integer)
    dexterity = Column("dex", Integer)
    constitution = Column("con", Integer)
    intelligence = Column("int", Integer)
    wisdom = Column("wis", Integer)
    charisma = Column("cha", Integer)
    # TODO: Fix the formatting to look more presentable, currently displays as one long message. --SM
    def __repr__(self):
        return f"Name: {self.name}\nType: {self.Type}\nSize: {self.size}\nAC: {self.AC}\nHP: {self.HP}\nSpeed: {self.speed}\nAlignment: {self.alignment}\nLegendary: {self.legendary}\nSource: {self.source}\nSTR: {self.strength}\nDEX: {self.dexterity}\nCON: {self.constitution}\nINT: {self.intelligence}\nWIS: {self.wisdom}\nCHA: {self.charisma}"