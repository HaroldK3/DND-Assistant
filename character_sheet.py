import sqlite3
import json
from pathlib import Path
from PyPDF2 import PdfReader


DB_PATH = Path("DND_DB.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        discord_id TEXT,
        class_level TEXT,
        race TEXT,
        background TEXT,
        data JSON NOT NULL
    )
    """)

    conn.commit()
    conn.close()

def set_character_owner(name: str, discord_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
                UPDATE characters
                SET discord_id = ?
                WHERE name = ?
                """, (discord_id, name))
    conn.commit()
    conn.close()


def insert_character(name, data):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO characters (name, class_level, race, background, data)
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        data.get("ClassLevel", ""),
        data.get("Race ", ""),
        data.get("Background", ""),
        json.dumps(data)
    ))

    conn.commit()
    conn.close()


def update_character(name, data):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE characters
        SET class_level = ?, race = ?, background = ?, data = ?
        WHERE name = ?
    """, (
        data.get("ClassLevel", ""),
        data.get("Race ", ""),
        data.get("Background", ""),
        json.dumps(data),
        name
    ))

    conn.commit()
    conn.close()


def delete_character(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM characters WHERE name = ?", (name,))
    conn.commit()
    conn.close()


def get_character(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM characters WHERE name = ?", (name,))
    row = cur.fetchone()
    conn.close()
    return row


def parse_pdf(path: str) -> dict:
    reader = PdfReader(path)
    raw_fields = reader.get_fields()

    parsed = {}

    for key, field in raw_fields.items():
        val = field.get('/V')

        # Convert None to empty string
        if val is None:
            val = ""

        # Convert bytes to string (some PDFs do this)
        if isinstance(val, bytes):
            try:
                val = val.decode("utf-8")
            except:
                val = val.decode("latin-1")

        parsed[key] = val

    return parsed


def import_character_from_pdf(pdf_path: str):
    data = parse_pdf(pdf_path)

    # name field in your PDF
    name = data.get("CharacterName", "").strip()

    if not name:
        raise ValueError("Character sheet has no CharacterName field set!")

    existing = get_character(name)

    if existing:
        print(f"Updating existing character: {name}")
        update_character(name, data)
    else:
        print(f"Inserting new character: {name}")
        insert_character(name, data)

    return name


def remove_character(name: str):
    delete_character(name)
    print(f"Deleted character: {name}")



def get_character_by_discord(discord_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM characters WHERE discord_id = ?", (discord_id,))
    row = cur.fetchone()
    conn.close()
    return row



