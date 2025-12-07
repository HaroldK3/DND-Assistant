import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import discord

# make sure that the data folder exists
if not os.path.exists("data"):
    os.makedirs("data")
# path to the db
DATABASE_URL = "sqlite:///data/sessions.db"
# engine session and factory
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()
# model for the database
class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
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

Base.metadata.create_all(bind=engine)

class SessionTracker:
    def __init__(self):
        self.active_sessions = {}  # key: guild_id -> session_data

    def get_active_session(self, guild_id):
        """Get the active session for a guild, if any."""
        return self.active_sessions.get(str(guild_id))

    def start_session(self, guild_id, session_number, location, level):
        guild_id = str(guild_id)
        
        # prevent starting a second session if is already active
        if guild_id in self.active_sessions:
            return None, "There's already an active session. End it first with `/session_end`"
        
        # stores all session runtime data in memory
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
        
        # embed for when we start a session
        embed = discord.Embed(
            title=f" Session {session_number} Started",
            description=f"**Location:** {location}\n**Level:** {level}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        return embed, None
    # ends active session for a guild
    # saves the session data and saves to the db
    def end_session(self, guild_id):
        guild_id = str(guild_id)
        session_data = self.active_sessions.get(guild_id)
        
        # no active session exists
        if not session_data:
            return None, "No active session found."
        
        # when the session ended
        session_data["end_time"] = datetime.now()

        # Save the session to the db
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

        # Calculate total session duration
        duration = session_data["end_time"] - session_data["start_time"]
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        # formats the time so it is accurate and nicely readable
        start_time_str = session_data["start_time"].strftime("%I:%M %p")
        end_time_str = session_data["end_time"].strftime("%I:%M %p")
        # create recap embed
        embed = discord.Embed(
            title=f" Session {session_data['session_number']} Complete",
            description=f"**Location:** {session_data['location']}\n**Level:** {session_data['level']}",
            color=discord.Color.blue(),
            timestamp=session_data["end_time"]
        )
        # footer for start and finsish time
        embed.set_footer(text=f"Started: {start_time_str} | Ended: {end_time_str}")
        
        # who played in the session
        players_text = ", ".join(session_data["players"]) if session_data["players"] else "None recorded"
        embed.add_field(name=" Players", value=players_text, inline=False)
        
        # Duration 
        embed.add_field(name=" Duration", value=f"{hours}h {minutes}m", inline=True)

        # Consumables used
        if session_data["consumables_used"]:
            consumables_text = ", ".join(session_data["consumables_used"])
            embed.add_field(name=" Consumables Used", value=consumables_text, inline=False)
        
        # show actions logged
        if session_data["actions_log"]:
            events_text = "\n".join(f"• {action}" for action in session_data["actions_log"])
            # Split if too long (Discord embed field limit is 1024 chars)
            if len(events_text) > 1024:
                events_text = events_text[:1020] + "..."
            embed.add_field(name=" Session Events", value=events_text, inline=False)
        # remove from memory after saved
        del self.active_sessions[guild_id]
        return embed, None

    def log_action(self, guild_id, action):
        # add action to the session log with timestamps
        guild_id = str(guild_id)
        session_data = self.active_sessions.get(guild_id)
        # only log when session is running
        if session_data:
            timestamp = datetime.now().strftime("%I:%M %p")
            session_data["actions_log"].append(f"[{timestamp}] {action}")
            return True
        return False
    # add a player to the session
    def add_player(self, guild_id, player_name):
        guild_id = str(guild_id)
        session_data = self.active_sessions.get(guild_id)
        if session_data and player_name not in session_data["players"]:
            session_data["players"].append(player_name)
            return True
        return False
    # logs consumable usage automatically
    def use_consumable(self, guild_id, item_name, player):
        guild_id = str(guild_id)
        session_data = self.active_sessions.get(guild_id)
        if session_data:
            session_data["consumables_used"].append(f"{player}: {item_name}")
            self.log_action(guild_id, f"{player} used **{item_name}**")
            return True
        return False
    # logs loot events automatically
    # also puts the text from the loot in the recap
    def record_loot(self, guild_id, player, loot_text):
        """Logs loot events automatically."""
        guild_id = str(guild_id)
        # Extract just the items from the loot text
        if "**You open the loot and find:**" in loot_text:
            items = loot_text.split("**You open the loot and find:**\n")[1]
            self.log_action(guild_id, f"{player} found loot: **{items}**")
            return True
        return False
    # logs monster encounters automatically
    def record_monster(self, guild_id, player, monsters):
        guild_id = str(guild_id)
        if monsters:
            names = ", ".join(m.name for m in monsters if hasattr(m, "name"))
            if names:
                self.log_action(guild_id, f"{player} encountered: **{names}**")
                return True
        return False
    
    def record_roll(self, guild_id, player, dice_notation, result):
        guild_id = str(guild_id)
        # Only log if it looks like an important roll (d20 for checks/attacks)
        if "d20" in dice_notation.lower():
            self.log_action(guild_id, f"{player} rolled {dice_notation}: **{result}**")
            return True
        return False