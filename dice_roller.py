import re
import random

## Dice roller logic using Regex (Unfortunately) to parse the /roll 4d6+6 to be consistent with
## DND style dice input. --KH

def roll(input):

    input = input.lower().replace(' ', '')
    match = re.match(r'^(\d)d(\d+)([+-]\d)?$', input)

    if not match:
        return None, "Error, use format like '3d2+4' or 'd20'."

    num, sides, modifier = match.groups()

    try:
        num_of_die = int(num) if num else 1
        sides_of_die = int(sides)
        die_modifier = 0

        if modifier:
            die_modifier = int(modifier)

    except ValueError:
        return None, "Error: Invalid numbers in the expression."

    if num_of_die > 100 or sides_of_die > 1000:
        return None, "Error: Too many dice or sides."

    rolls = [random.randint(1, sides_of_die) for _ in range(num_of_die)]
    rolls_sum = sum(rolls)
    total = rolls_sum + die_modifier

    mod = f"{'+' if die_modifier >= 0 else '-'} {abs(die_modifier)}" if die_modifier != 0 else ""

    return f"Rolls {num_of_die}d{sides_of_die}{mod}: {rolls} Total: {total}"