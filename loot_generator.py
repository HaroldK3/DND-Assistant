import random
from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy import create_engine, Integer, String, Column
from sqlalchemy.orm import sessionmaker, declarative_base

@dataclass
class Item:
    name: str
    rarity: str   # "common", "uncommon", "rare", "very-rare", "legendary"
    type: str     # "weapon", "armor", "potion", "gear", etc.
    magic: bool = False


DATABASE_URL = "sqlite:///data/Weapons.db"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

class WeaponModel(Base):
    __tablename__ = "Weapons_DB_Import"  
    WeaponID = Column(Integer, primary_key=True, autoincrement=True)
    Name     = Column(String)
    Rarity   = Column(String)
    Type     = Column(String)
    Magic    = Column(Integer)


# ---------- HELPERS TO NORMALIZE DB VALUES ----------

def _normalize_rarity(r: Optional[str]) -> str:
    if not r:
        return "common"
    r = r.strip().lower()
    return r.replace(" ", "-")  # "VERY RARE" -> "very-rare"

def _normalize_type(t: Optional[str]) -> str:
    if not t:
        return "misc"
    return t.strip().lower()


def _load_items_from_db() -> List[Item]:
    """Load all weapons from the SQLite DB into Item dataclasses."""
    session = SessionLocal()
    try:
        rows = session.query(WeaponModel).all()
        items: List[Item] = []
        for row in rows:
            items.append(
                Item(
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
    """
    Parse things like:
      "common weapon"
      "common light armor"
      "any ring magic"
      "rare magic weapon"
    Into (rarity, item_type, magic_only_str).
    """

    tokens = arg_string.strip().split()
    if not tokens:
        return "random", "any", "no"

    rarity = "random"
    magic_only = "no"
    type_words = []

    i = 0

    # --- first token(s) = rarity? ---
    if i < len(tokens):
        t = tokens[i].lower()

        # handle "very rare" as two-word rarity
        if t == "very" and i + 1 < len(tokens) and tokens[i + 1].lower() == "rare":
            rarity = "very-rare"
            i += 2
        elif t in RARITY_WORDS:
            rarity = t
            i += 1

    # --- remaining tokens: type words and/or 'magic' flag ---
    while i < len(tokens):
        t = tokens[i].lower()
        if t in ("magic", "magical"):
            magic_only = "magic"
        else:
            type_words.append(t)
        i += 1

    item_type = " ".join(type_words) if type_words else "any"

    return rarity, item_type, magic_only


def _choose_rarity() -> str:
    rarities = list(RARITY_WEIGHTS.keys())
    weights = list(RARITY_WEIGHTS.values())
    return random.choices(rarities, weights=weights, k=1)[0]


def random_item(
    rarity: Optional[str] = None,
    type_: Optional[str] = None,
    magic_only: bool = False
) -> Optional[Item]:
    """
    Pick one random item, filtered by rarity/type/magic-only flags.
    If rarity is None or 'random', a rarity is chosen using RARITY_WEIGHTS.
    """

    
    if not ITEMS:
        return None

    if rarity is None or rarity.lower() in ("random", "any", "none"):
        rarity = _choose_rarity()

    rarity = _normalize_rarity(rarity)

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
    """
    Generate a small list of items as 'loot'.
    chest_type controls how many items: pouch < chest < hoard.
    """

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


def _parse_magic_flag(magic_only: str) -> bool:
    return magic_only.lower() in ("magic", "magic-only", "yes", "y", "true", "t")


def build_item_message(
    rarity: str = "random",
    item_type: str = "any",
    magic_only: str = "no"
) -> str:
    # Return a Discord message for a single item request.
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
    """Return a Discord message for a loot chest."""
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