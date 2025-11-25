import random
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Item:
    name: str
    rarity: str   # "common", "uncommon", "rare", "very-rare", "legendary"
    type: str     # "weapon", "armor", "potion", "gear", etc.
    magic: bool = False


# Example item pool 
ITEMS: List[Item] = [
    Item("Healing Potion", "common", "potion", True),
    Item("Dagger", "common", "weapon", False),
    Item("Leather Armor", "common", "armor", False),

    Item("+1 Longsword", "uncommon", "weapon", True),
    Item("Cloak of Protection", "uncommon", "wondrous", True),

    Item("Bag of Holding", "rare", "wondrous", True),
    Item("Ring of Protection", "rare", "ring", True),

    Item("Flame Tongue", "very-rare", "weapon", True),

    Item("Vorpal Sword", "legendary", "weapon", True),
]

# How likely each rarity is when item is random rarity
RARITY_WEIGHTS = {
    "common": 60,
    "uncommon": 25,
    "rare": 10,
    "very-rare": 4,
    "legendary": 1,
}


def _choose_rarity() -> str:
    rarities = list(RARITY_WEIGHTS.keys())
    weights = list(RARITY_WEIGHTS.values())
    return random.choices(rarities, weights=weights, k=1)[0]


def random_item(rarity: Optional[str] = None,type_: Optional[str] = None,magic_only: bool = False) -> Optional[Item]:
    
    ## Pick one random item, filtered by rarity/type/magic-only flags.
    ## If rarity is None or 'random', a rarity is chosen using RARITY_WEIGHTS.
    
    if rarity is None or rarity.lower() == "random":
        rarity = _choose_rarity()
    rarity = rarity.lower()

    pool = [i for i in ITEMS if i.rarity == rarity]

    if type_:
        type_ = type_.lower()
        pool = [i for i in pool if i.type == type_]

    if magic_only:
        pool = [i for i in pool if i.magic]

    if not pool:
        return None
    return random.choice(pool)


def random_loot(chest_type: str = "chest",magic_only: bool = False) -> List[Item]:
    
    ## Generate a small list of items as 'loot'.
    ## chest_type controls how many items: pouch < chest < hoard.
    
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


def build_item_message(rarity: str = "random", item_type: str = "any",magic_only: str = "no") -> str:
    # Return a Discord message for a single item request.
    # Normalize args
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
    ## Return a Discord message for a loot chest
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