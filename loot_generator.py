import random
from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy import create_engine, Integer, String, Column, ForeignKey, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# ---------- DATA MODEL ----------

@dataclass
class Item:
    weapon_id: int          # WeaponID from the DB
    name: str
    rarity: str             # "common", "uncommon", "rare", "very-rare", "legendary"
    type: str               # "weapon", "armor", "potion", "gear", etc.
    magic: bool = False

# Open the Weapons Database 
DATABASE_URL = "sqlite:///data/Weapons.db"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


class WeaponModel(Base):
    __tablename__ = "Weapons_DB_Import"
    # Weapon ORM
    WeaponID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String)
    Rarity = Column(String)
    Type = Column(String)
    Magic = Column(Integer)


class InventoryModel(Base):
    
    # Links a Discord user to a weapon. One row = one stack of a given weapon for a given user. - AM

    __tablename__ = "Inventory"

    InventoryID = Column(Integer, primary_key=True, autoincrement=True)
    DiscordID = Column(String, nullable=False)
    WeaponID = Column(Integer, ForeignKey("Weapons_DB_Import.WeaponID"), nullable=False)
    Quantity = Column(Integer, nullable=False, default=1)
    CreatedAt = Column(DateTime, server_default=func.now())

    weapon = relationship("WeaponModel")

Base.metadata.create_all(engine)

# ---------- HELPERS TO NORMALIZE DB VALUES ----------

def _normalize_rarity(r: Optional[str]) -> str:
    if not r:
        return "common"
    r = r.strip().lower()
    return r.replace(" ", "-")  # "VERY RARE" -> "very-rare" - AM


def _normalize_type(t: Optional[str]) -> str:
    if not t:
        return "misc"
    t = t.strip().lower()
    return t.replace("_", " ")  # fix ADVENTURING_GEAR types - AM


def _load_items_from_db() -> List[Item]:
    """Load all weapons from the SQLite DB into Item dataclasses."""
    session = SessionLocal()
    try:
        rows = session.query(WeaponModel).all()
        items: List[Item] = []
        for row in rows:
            items.append(
                Item(
                    weapon_id=row.WeaponID,
                    name=row.Name,
                    rarity=_normalize_rarity(row.Rarity),
                    type=_normalize_type(row.Type),
                    magic=bool(row.Magic),
                )
            )
        return items
    finally:
        session.close()


ITEMS: List[Item] = _load_items_from_db()  


# ---------- RARITY & ARG PARSING ----------

RARITY_WEIGHTS = {
    "common": 60,
    "uncommon": 25,
    "rare": 10,
    "very-rare": 4,
    "legendary": 1,
}

RARITY_WORDS = {
    "common",
    "uncommon",
    "rare",
    "legendary",
    "any",
    "random",
    "none",
    "very-rare",
    "very_rare",
}


def parse_item_args(arg_string: str):
    
   # Parse strings like:, "common weapon", "common light armor", "any ring magic", "rare magic weapon" into (rarity, item_type, magic_only_str). - AM
    
    tokens = arg_string.strip().split()
    if not tokens:
        return "random", "any", "no"

    rarity = "random"
    magic_only = "no"
    type_words: List[str] = []

    i = 0

    # first token(s) may be rarity
    if i < len(tokens):
        t = tokens[i].lower()
        # handle "very rare"
        if t == "very" and i + 1 < len(tokens) and tokens[i + 1].lower() == "rare":
            rarity = "very-rare"
            i += 2
        elif t in RARITY_WORDS:
            rarity = t
            i += 1

    # rest = type + check for magic
    while i < len(tokens):
        t = tokens[i].lower()
        if t in ("magic", "magical"):
            magic_only = "magic"
        else:
            type_words.append(t)
        i += 1

    item_type = " ".join(type_words) if type_words else "any"
    return rarity, item_type, magic_only

# For random rarity items
def _choose_rarity() -> str:
    rarities = list(RARITY_WEIGHTS.keys())
    weights = list(RARITY_WEIGHTS.values())
    return random.choices(rarities, weights=weights, k=1)[0]


# ---------- RANDOM ITEM / LOOT ----------

def random_item(
    rarity: Optional[str] = None,
    type_: Optional[str] = None,
    magic_only: bool = False,
) -> Optional[Item]:
  # Pick one random item, filtered by rarity/type/magic-only flags. If rarity is None or 'random' RARITY_WEIGHTS is used to get a random rarity - AM
    
    if not ITEMS:
        return None
    # If no rarity given, pick a random one
    if rarity is None or rarity.lower() in ("random", "any", "none"):
        rarity = _choose_rarity()

    rarity = _normalize_rarity(rarity)
    # Throw items matching query into a pool, filter while progressing through the query - AM
    pool = [i for i in ITEMS if i.rarity == rarity]

    if type_:
        type_ = _normalize_type(type_)
        pool = [i for i in pool if i.type == type_]

    if magic_only:
        pool = [i for i in pool if i.magic]

    if not pool:
        return None
    return random.choice(pool)


def random_loot(chest_type: str = "chest", magic_only: bool = False) -> List[Item]:
    
    # Generate a small list of items. chest_type dictates how many items can be generated - AM

    chest_type = chest_type.lower()

    if chest_type in ("pouch", "small"):
        n_items = random.randint(1, 2)
    elif chest_type in ("chest", "medium"):
        n_items = random.randint(2, 4)
    elif chest_type in ("hoard", "large", "boss"):
        n_items = random.randint(4, 8)
    else:
        n_items = random.randint(1, 3)

    items: List[Item] = []
    for _ in range(n_items):
        item = random_item(magic_only=magic_only)
        if item:
            items.append(item)
    return items

# filter for possible magic flags
def _parse_magic_flag(magic_only: str) -> bool:
    return magic_only.lower() in ("magic", "magic-only", "yes", "y", "true", "t")


# ---------- INVENTORY HELPERS ----------

def save_item_to_user(discord_id: str, item: Item, quantity: int = 1) -> None:
    # Create an Inventory row for this user + item. - AM
    session = SessionLocal()
    try:
        inv = InventoryModel(
            DiscordID=str(discord_id),
            WeaponID=item.weapon_id,
            Quantity=quantity,
        )
        session.add(inv)
        session.commit()
    finally:
        session.close()


def get_items_for_user(discord_id: str) -> List[Item]:
    # Return a list of Items owned by the given Discord user. - AM
    session = SessionLocal()
    try:
        rows = (
            session.query(InventoryModel, WeaponModel)
            .join(WeaponModel, InventoryModel.WeaponID == WeaponModel.WeaponID)
            .filter(InventoryModel.DiscordID == str(discord_id))
            .order_by(InventoryModel.InventoryID)
            .all()
        )

        items: List[Item] = []
        for inv, weapon in rows:
            items.append(
                Item(
                    weapon_id=weapon.WeaponID,
                    name=weapon.Name,
                    rarity=_normalize_rarity(weapon.Rarity),
                    type=_normalize_type(weapon.Type),
                    magic=bool(weapon.Magic),
                )
            )
        return items
    finally:
        session.close()


def generate_item_for_user(discord_id: str, rarity: str = "random", item_type: str = "any", magic_only: str = "no") -> str:
    # Generate an item, save it to the user's inventory, and return text describing the item. - AM
    
    rarity_arg = None if rarity.lower() in ("random", "any", "none") else rarity
    type_arg = None if item_type.lower() in ("any", "none") else item_type
    magic_flag = _parse_magic_flag(magic_only)

    item = random_item(rarity=rarity_arg, type_=type_arg, magic_only=magic_flag)
    if not item:
        return "I couldn't find an item matching those filters."

    save_item_to_user(discord_id, item)

    magic_text = " (magic)" if item.magic else ""
    return (
        f"**Item:** {item.name}{magic_text}\n"
        f"Rarity: {item.rarity.title()} | Type: {item.type.title()}"
    )

def clear_inventory_for_user(discord_id: str) -> int:
   # Delete all inventory entries for the given user. Returns the number of rows deleted. - AM
    session = SessionLocal()
    try:
        q = session.query(InventoryModel).filter(
            InventoryModel.DiscordID == str(discord_id)
        )
        count = q.count()
        q.delete(synchronize_session=False)
        session.commit()
        return count
    finally:
        session.close()


def build_inventory_message(discord_id: str) -> str:
    # Discord message for user inventory - AM
    items = get_items_for_user(discord_id)
    if not items:
        return "You don't have any items yet."

    lines = []
    for idx, item in enumerate(items, start=1):
        magic_text = " (magic)" if item.magic else ""
        lines.append(
            f"{idx}. {item.name}{magic_text} — {item.rarity.title()} {item.type.title()}"
        )

    return "**Your inventory:**\n" + "\n".join(lines)




def build_item_message(rarity: str = "random", item_type: str = "any", magic_only: str = "no") -> str:
    # Return a Discord message for a single item (no saving). - AM
    rarity_arg = None if rarity.lower() in ("random", "any", "none") else rarity
    type_arg = None if item_type.lower() in ("any", "none") else item_type
    magic_flag = _parse_magic_flag(magic_only)

    item = random_item(rarity=rarity_arg, type_=type_arg, magic_only=magic_flag)
    if not item:
        return "I couldn't find an item matching those filters."

    magic_text = " (magic)" if item.magic else ""
    return (
        f"**Item:** {item.name}{magic_text}\n"
        f"Rarity: {item.rarity.title()} | Type: {item.type.title()}"
    )


def build_loot_message(chest_type: str = "chest") -> str:
    # Return a Discord message for a loot chest. - AM
    items = random_loot(chest_type=chest_type)
    if not items:
        return "The chest is empty..."

    lines = []
    for idx, item in enumerate(items, start=1):
        magic_text = " (magic)" if item.magic else ""
        lines.append(
            f"{idx}. {item.name}{magic_text} — {item.rarity.title()} {item.type.title()}"
        )

    return "**You open the loot and find:**\n" + "\n".join(lines)
