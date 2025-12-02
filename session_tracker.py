import sqlite3
import os
from datetime import datetime

# make sure data folder is there so we know we can make the database
if not os.path.exists("data"):
    os.makedirs("data")

# path to the db
DB_PATH = "data/sessions.db"

# making sure the db exists
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

# creating sessions table that will store things for the summary
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_number INTEGER,
            location TEXT,
            level INTEGER,
            start_time TEXT,
            end_time TEXT,
            players TEXT,
            actions_log TEXT,
            xp_given INTEGER,
            consumables_used TEXT
        )
    """)

    conn.commit()
    conn.close()

# run the database wehn we start the code
init_db()


# session tracker
class SessionTracker:
    def __init__(self):
        self.active_sessions = {}

    # starting sessions
    # must use a session number location and level to start  (as of now)
    # returns a message that confirms it is started
    def start_session(self, session_number, location, level):
        # sesion state dictionary
        self.active_sessions[session_number] = {
            "session_number": session_number,
            "location": location,
            "level": level,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "players": [],
            "actions_log": [],
            "xp_given": 0,
            "consumables_used": []
        }
        return f"Session {session_number} started at {location}, Level {level}"

    # end session with session number
    def end_session(self, session_number):
        session = self.active_sessions.get(session_number)
        # if no session is found with that number return no session found
        if not session:
            return f"No active session {session_number}."

        # record the end time for the session
        session["end_time"] = datetime.utcnow().isoformat()

        # send info from sessions to db
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO sessions 
            (session_number, location, level, start_time, end_time, players, actions_log, xp_given, consumables_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["session_number"],
            session["location"],
            session["level"],
            session["start_time"],
            session["end_time"],
            ", ".join(session["players"]),
            "\n".join(session["actions_log"]),
            session["xp_given"],
            ", ".join(session["consumables_used"])
        ))

        conn.commit()
        conn.close()

        # recap that will display
        recap = (
            f"Session {session['session_number']} Recap:\n"
            f"Location: {session['location']}\n"
            f"Level: {session['level']}\n"
            f"Duration: {session['start_time']} -> {session['end_time']}\n"
            f"Players: {', '.join(session['players'])}\n"
            f"Actions:\n{chr(10).join(session['actions_log']) if session['actions_log'] else 'No actions recorded.'}\n"
            f"XP Given: {session['xp_given']}\n"
            f"Consumables Used: {', '.join(session['consumables_used']) if session['consumables_used'] else 'None'}"
        )

        del self.active_sessions[session_number]
        return recap

    def log_action(self, session_number, action):
        session = self.active_sessions.get(session_number)
        if session:
            session["actions_log"].append(action)
    # add players to a session
    def add_player(self, session_number, player_name):
        session = self.active_sessions.get(session_number)
        if session and player_name not in session["players"]:
            session["players"].append(player_name)
    # add XP to the session
    def add_xp(self, session_number, xp):
        session = self.active_sessions.get(session_number)
        if session:
            session["xp_given"] += xp
    # use a consumable 
    def use_consumable(self, session_number, item_name):
        session = self.active_sessions.get(session_number)
        if session:
            session["consumables_used"].append(item_name)