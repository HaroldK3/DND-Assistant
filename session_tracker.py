import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import discord

# make sure that the data folder exists, if it doesn't then make it -NM
if not os.path.exists("data"):
    os.makedirs("data")
# path to the db
DATABASE_URL = "sqlite:///data/sessions.db"
# creating the engine, echo false to disable sql logging, and future true to make sure SQL alchemy is the modern version -NM
engine = create_engine(DATABASE_URL, echo=False, future=True)
# session maker, binds engine, autoflush false disables automatic flush, autocommit false disables automatic commits -NM
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()
# sessionmodel class, inherits the base from sqlalchemy -NM
class SessionModel(Base):
    __tablename__ = "sessions"
    # primary key, primary key true lets that be known, autoincrement true means that it will automaticallly increase the id  -NM
    id = Column(Integer, primary_key=True, autoincrement=True)
    # each table column with their data type -NM
    session_number = Column(Integer)
    guild_id = Column(String)
    location = Column(String)
    level = Column(Integer)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    players = Column(Text)
    actions_log = Column(Text)
    xp_given = Column(Integer)
    consumables_used = Column(Text)
# creates the table in the database if it does not exist already -NM
Base.metadata.create_all(bind=engine)
# session tracker class, init is a constructor, every session tracker object will have its own active sessions dictionary -NM
class SessionTracker:
    def __init__(self):
        self.active_sessions = {}  
    # get the active sessions,  parameter self is refferring to current object or instance of the session tracker, which id to check -NM
    def get_active_session(self, guild_id):
        return self.active_sessions.get(str(guild_id))
    # start a session, making guild a string -NM
    def start_session(self, guild_id, session_number, location, level):
        guild_id = str(guild_id)
        
        # prevents starting a session if one is already active, with no embed and a message alerting us -NM
        if guild_id in self.active_sessions:
            return None, "There's already an active session. End it first with `/session_end`"
        
        # stores all session runtime data in memory, stores session number guild id location and level, empty list for players actions log and consumables used -NM
        self.active_sessions[guild_id] = {
            "session_number": session_number,
            "guild_id": guild_id,
            "location": location,
            "level": level,
            "start_time": datetime.now(),
            "end_time": None,
            "players": [],
            "actions_log": [],
            "consumables_used": []
        }
        
        # embed for when we start a session with the location level and time, f string to to put varaibles in our string, ** makes things bold -NM
        embed = discord.Embed(
            title=f" Session {session_number} Started",
            description=f"**Location:** {location}\n**Level:** {level}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        # returns embed, no error message yet -NM
        return embed, None
    # end a session
    def end_session(self, guild_id):
        guild_id = str(guild_id)
        session_data = self.active_sessions.get(guild_id)
        
        # no active session exists -NM
        if not session_data:
            return None, "No active session found."
        
        # when the session ended, put to now so time is accurate -NM
        session_data["end_time"] = datetime.now()

        # creates a new db session, creating a instance of session model, each parameter fills data for this specific session, db session object gets added to the database saves all the infor to the database then closes the db session -NM
        db = SessionLocal()
        db_session = SessionModel(
            session_number=session_data["session_number"],
            guild_id=session_data["guild_id"],
            location=session_data["location"],
            level=session_data["level"],
            start_time=session_data["start_time"],
            end_time=session_data["end_time"],
            players=", ".join(session_data["players"]),
            actions_log="\n".join(session_data["actions_log"]),
            consumables_used=", ".join(session_data["consumables_used"])
        )
        db.add(db_session)
        db.commit()
        db.close()

        # Calculate total session duration, subtracts start time from end time which results in datetime object which represents a duration of time, 3600 = number of seconds in an hour -NM
        duration = session_data["end_time"] - session_data["start_time"]
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        # formats the time so it is accurate and nicely readable, I for hours M for minutes and p for am and pm -NM
        start_time_str = session_data["start_time"].strftime("%I:%M %p")
        end_time_str = session_data["end_time"].strftime("%I:%M %p")
        # creating a embed for the recap, ** for bold letters -NM
        embed = discord.Embed(
            title=f" Session {session_data['session_number']} Complete",
            description=f"**Location:** {session_data['location']}\n**Level:** {session_data['level']}",
            color=discord.Color.blue(),
            timestamp=session_data["end_time"]
        )
        # footer for start and finsish time -NM
        embed.set_footer(text=f"Started: {start_time_str} | Ended: {end_time_str}")
        
        # adding player to the embed, join all players names with commas if they exist -NM
        players_text = ", ".join(session_data["players"]) if session_data["players"] else "None recorded"
        embed.add_field(name=" Players", value=players_text, inline=False)
        
        # how long the session lasted, inline true allows multiple fields in the same row -NM
        embed.add_field(name=" Duration", value=f"{hours}h {minutes}m", inline=True)

        # check if any consumables were used in the first place, if there was join them all into a single string and add the field to the embed -NM
        if session_data["consumables_used"]:
            consumables_text = ", ".join(session_data["consumables_used"])
            embed.add_field(name=" Consumables Used", value=consumables_text, inline=False)
        
        # same concept as consumables, joins all actions as string, bullet point before each one so it is cleaner visually -NM
        if session_data["actions_log"]:
            events_text = "\n".join(f"• {action}" for action in session_data["actions_log"])
            # split the embed fields if they are too long max is 1024, slicing the 1020 with : making sure dont go over 1024, and making sure there is room so we can put ... so the person knows there is more, value = events_text contains all events logged during the session, make sure rows are not inline/blocky and appears in its own line -NM
            if len(events_text) > 1024:
                events_text = events_text[:1020] + "..."
            embed.add_field(name=" Session Events", value=events_text, inline=False)
        # removes the session fromm the active session dictionary after saved, makes sure session is no longer active -NM
        del self.active_sessions[guild_id]
        return embed, None
    # add action to the session log with timestamps, self refers to current session tracker -NM
    def log_action(self, guild_id, action):
        guild_id = str(guild_id)
        session_data = self.active_sessions.get(guild_id)
        # only log when session is running, I for hour M for minutes and p for am and pm -NM
        if session_data:
            timestamp = datetime.now().strftime("%I:%M %p")
            session_data["actions_log"].append(f"[{timestamp}] {action}")
            return True
        return False
    # add a player to the session if not already added, append player = add player -NM
    def add_player(self, guild_id, player_name):
        guild_id = str(guild_id)
        session_data = self.active_sessions.get(guild_id)
        if session_data and player_name not in session_data["players"]:
            session_data["players"].append(player_name)
            return True
        return False
    # logs consumable usage automatically -NM
    def use_consumable(self, guild_id, item_name, player):
        guild_id = str(guild_id)
        session_data = self.active_sessions.get(guild_id)
        if session_data:
            session_data["consumables_used"].append(f"{player}: {item_name}")
            self.log_action(guild_id, f"{player} used **{item_name}**")
            return True
        return False
    # logs loot events automatically -NM
    # also puts the text from the loot in the recap, making sure we get the loot message -NM
    def record_loot(self, guild_id, player, loot_text):
        guild_id = str(guild_id)
        # Extract just the items from the loot text
        if "**You open the loot and find:**" in loot_text:
            items = loot_text.split("**You open the loot and find:**\n")[1]
            self.log_action(guild_id, f"{player} found loot: **{items}**")
            return True
        return False
    # logs monster encountered by a player during the session, hasattr makes sure the monster has a name -NM
    def record_monster(self, guild_id, player, monsters):
        guild_id = str(guild_id)
        if monsters:
            names = ", ".join(m.name for m in monsters if hasattr(m, "name"))
            if names:
                self.log_action(guild_id, f"{player} encountered: **{names}**")
                return True
        return False
    # logs dice rolls but only important ones -NM
    def record_roll(self, guild_id, player, dice_notation, result):
        guild_id = str(guild_id)
       
        if "d20" in dice_notation.lower():
            self.log_action(guild_id, f"{player} rolled {dice_notation}: **{result}**")
            return True
        return False
