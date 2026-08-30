import json
import re
from datetime import datetime, timedelta


# -----------------------------
# Hindi / Roman number handling
# -----------------------------

NUMBER_WORDS = {
    "ek": 1,
    "एक": 1,
    "do": 2,
    "दो": 2,
    "teen": 3,
    "तीन": 3,
    "char": 4,
    "chaar": 4,
    "चार": 4,
    "paanch": 5,
    "पांच": 5,
    "पाँच": 5,
    "cheh": 6,
    "chhe": 6,
    "छह": 6,
    "saat": 7,
    "सात": 7,
    "aath": 8,
    "आठ": 8,
    "nau": 9,
    "नौ": 9,
    "das": 10,
    "दस": 10,
}


MEASUREMENT_WORDS = {
    "athais": 28,
    "tees": 30,
    "battis": 32,
    "chautis": 34,
    "chhattis": 36,
    "aadtis": 38,
    "chalis": 40,
    "bayalis": 42,
    "chavalis": 44,
    "chhiyalis": 46,
    "adtalis": 48,
    "saath": 60,
    "assi": 80,
    "sau": 100,
}


# -----------------------------
# Item vocabulary
# -----------------------------

ITEMS = {
    "tailor": {
        "kurta": ["kurta", "kurtha"],
        "shirt": ["shirt"],
        "pant": ["pant"],
        "pajama": ["pajama", "pyjama"],
        "blouse": ["blouse"],
        "salwar": ["salwar"],
        "suit": ["suit"],
        "waistcoat": ["koti", "waistcoat"],
    },

    "tiffin": {
        "rajma": ["rajma", "राजमा"],
        "sabzi": ["sabzi", "sabji", "सब्जी"],
        "roti": ["roti", "रोटी"],
        "dal": ["dal", "daal", "दाल"],
        "rice": ["rice", "chawal", "चावल"],
        "poha": ["poha", "पोहे"],
        "idli": ["idli", "इडली"],
        "chole": ["chole", "छोले"],
        "thali": ["thali", "थाली"],
    },

    "electrician": {
        "socket": ["socket"],
        "wiring": ["wiring", "wire", "वायरिंग"],
        "switch board": ["switchboard", "switch board"],
        "geyser": ["geyser", "gizer", "गीजर"],
        "tube light": ["tube light", "tubelight", "ट्यूब लाइट"],
        "ceiling fan": ["ceiling fan", "pankha", "पंखा"],
        "inverter": ["inverter", "invertor"],
        "doorbell": ["doorbell", "ghanti", "घंटी"],
    },

    "baker": {
        "cake": ["cake"],
        "birthday cake": ["bday cake", "birthday cake"],
        "pastry": ["pastry"],
        "cheesecake": ["cheese cake", "cheesecake"],
        "cookies": ["cookie", "cookies"],
        "brownie": ["brownie", "browni"],
        "cupcake": ["cupcake"],
        "doughnut": ["doughnut", "donut"],
        "muffin": ["muffin"],
    }
}


# -----------------------------
# Helpers
# -----------------------------

def normalize(text):
    text = text.lower()
    text = text.replace("।", ".")
    return text


def find_quantity(text, start, end):
    part = text[max(0, start - 25):end]

    # Numeric quantity
    numbers = re.findall(r"(?<!\d)(\d+)(?!\d)", part)

    if numbers:
        return int(numbers[-1])

    # Hindi/Roman quantity
    tokens = re.findall(r"[\w\u0900-\u097F]+", part.lower())

    for token in reversed(tokens):
        if token in NUMBER_WORDS:
            return NUMBER_WORDS[token]

    return 1


def clean_name(name):
    name = name.strip(" ,.-")
    name = re.sub(r"\b(ji|didi|bhai|bhaiya)\b", "", name, flags=re.I)
    return name.strip()


# -----------------------------
# Customer
# -----------------------------

def extract_customer(text):
    patterns = [
        r"\b([A-Z][a-z]+)\s+(?:ji|didi|bhai|bhaiya)\b",
        r"\b([A-Z][a-z]+)\s+ke liye\b",
        r"\b([A-Z][a-z]+)\s+bol raha",
        r"\b([A-Z][a-z]+)\s+ke liye nahi,\s*([A-Z][a-z]+)\s+ke liye\b",
    ]

    # Negated customer: A ke liye nahi, B ke liye
    m = re.search(patterns[3], text, re.I)
    if m:
        return m.group(2)

    for pattern in patterns[:3]:
        m = re.search(pattern, text)
        if m:
            return clean_name(m.group(1))

    return None


# -----------------------------
# Amount
# -----------------------------

def extract_amount(text):
    patterns = [
        r"(\d+(?:\.\d+)?)\s*(?:rs|rupees|rupaye|me|tak)",
        r"(?:rs|rupees|rupaye)\s*(\d+(?:\.\d+)?)",
    ]

    for pattern in patterns:
        m = re.search(pattern, text, re.I)
        if m:
            return float(m.group(1))

    return None


# -----------------------------
# Prior order
# -----------------------------

def extract_prior_order(text):
    positive = [
        "last time jaisa",
        "last time wala",
        "pichli baar jaisa",
        "pichli baar wala",
        "pehle jaisa",
        "jo hamesha bhejte ho",
        "wahi roz wala",
    ]

    negative = [
        "pichli baar jaisa nahi",
        "last time jaisa nahi",
        "is baar naya",
    ]

    for phrase in negative:
        if phrase in text.lower():
            return False

    for phrase in positive:
        if phrase in text.lower():
            return True

    return False


# -----------------------------
# Date extraction
# -----------------------------

def extract_due_date(text, received_at):
    base = datetime.fromisoformat(received_at).date()
    t = normalize(text)

    # Explicit relative dates
    if "parso" in t:
        return (base + timedelta(days=2)).isoformat()

    if "tarso" in t or "narsu" in t:
        return (base + timedelta(days=3)).isoformat()

    if re.search(r"\bkal\b", t):
        return (base + timedelta(days=1)).isoformat()

    if re.search(r"\baaj\b", t):
        return base.isoformat()

    # Next week
    if "agle hafte" in t or "next week" in t:
        return (base + timedelta(days=7)).isoformat()

    # N days
    m = re.search(r"(\d+)\s*din\s*(?:me|mein|ke andar)", t)
    if m:
        return (base + timedelta(days=int(m.group(1)))).isoformat()

    # Explicit date: 1 September / 1 Sep
    months = {
        "january": 1, "jan": 1,
        "february": 2, "feb": 2,
        "march": 3, "mar": 3,
        "april": 4, "apr": 4,
        "may": 5,
        "june": 6, "jun": 6,
        "july": 7, "jul": 7,
        "august": 8, "aug": 8,
        "september": 9, "sep": 9,
        "october": 10, "oct": 10,
        "november": 11, "nov": 11,
        "december": 12, "dec": 12,
    }

    for month_name, month_num in months.items():
        m = re.search(r"\b(\d{1,2})\s+" + month_name, t)
        if m:
            day = int(m.group(1))
            year = base.year

            if (month_num, day) < (base.month, base.day):
                year += 1

            try:
                return datetime(year, month_num, day).date().isoformat()
            except ValueError:
                return None

    # N tarikh / tareekh
    m = re.search(r"\b(\d{1,2})\s*(?:tarikh|tareekh)\b", t)

    if m:
        day = int(m.group(1))
        year = base.year
        month = base.month

        if day < base.day:
            month += 1
            if month == 13:
                month = 1
                year += 1

        try:
            return datetime(year, month, day).date().isoformat()
        except ValueError:
            return None

    # Today/tomorrow style
    if "aaj tak" in t:
        return base.isoformat()

    return None


# -----------------------------
# Attributes
# -----------------------------

def extract_attributes(domain, text, item_start, item_end):
    t = normalize(text[item_start:item_end])
    attrs = {}

    if domain == "tailor":

        colors = [
            "navy blue", "black", "white", "red", "blue",
            "green", "yellow", "pink"
        ]

        for color in colors:
            if color in t:
                attrs["color"] = color
                break

        fabrics = ["rayon", "cotton", "silk", "linen", "wool"]

        for fabric in fabrics:
            if fabric in t:
                attrs["fabric"] = fabric
                break

        for key in ["chest", "waist", "length"]:
            m = re.search(
                rf"\b{key}\s*(\d+)\b",
                t
            )

            if m:
                attrs[key] = int(m.group(1))
            else:
                for word, value in MEASUREMENT_WORDS.items():
                    if re.search(rf"\b{key}\s+{word}\b", t):
                        attrs[key] = value

        sizes = ["XS", "S", "M", "L", "XL", "XXL"]

        for size in sizes:
            if re.search(rf"\b{size.lower()}\b", t):
                attrs["size"] = size
                break

        for fit in ["slim", "regular", "loose"]:
            if fit in t:
                attrs["fit"] = fit
                break

        for sleeve in ["full", "half", "three-quarter"]:
            if sleeve in t:
                attrs["sleeve"] = sleeve
                break

    elif domain == "tiffin":

        meals = ["breakfast", "lunch", "dinner"]

        for meal in meals:
            if meal in t:
                attrs["meal"] = meal
                break

        for portion in ["half", "full", "extra"]:
            if portion in t:
                attrs["portion"] = portion
                break

        for spice in ["mild", "medium", "spicy"]:
            if spice in t:
                attrs["spice_level"] = spice
                break

        m = re.search(r"(\d+)\s*(?:din|days)", t)
        if m:
            attrs["days"] = int(m.group(1))

        m = re.search(r"(\d+)\s*roti", t)
        if m:
            attrs["roti_count"] = int(m.group(1))

        if "jain" in t:
            attrs["jain"] = True

    elif domain == "electrician":

        brands = ["Havells", "Anchor", "Orient", "Philips"]

        for brand in brands:
            if brand.lower() in t:
                attrs["brand"] = brand
                break

        rooms = ["kitchen", "bathroom", "bedroom", "hall", "living room"]

        for room in rooms:
            if room in t:
                attrs["room"] = room
                break

        issues = {
            "fuse ud": "fuse blown",
            "fuse gaya": "fuse blown",
            "fuse blown": "fuse blown",
            "current aa raha": "leaking current",
            "jhatka": "leaking current",
            "short": "short circuit",
            "short circuit": "short circuit",
            "spark": "spark",
            "awaaz": "noise",
            "noise": "noise",
            "dheema": "slow",
            "slow": "slow",
            "nahi chal": "not working",
        }

        for phrase, issue in issues.items():
            if phrase in t:
                attrs["issue"] = issue
                break

        m = re.search(r"(\d+)\s*watt", t)
        if m:
            attrs["wattage"] = int(m.group(1))

        appliances = [
            "geyser",
            "fridge point",
            "ac",
            "fan",
            "tv"
        ]

        for appliance in appliances:
            if appliance in t:
                attrs["appliance"] = appliance
                break

    elif domain == "baker":

        flavours = [
            "red velvet",
            "black forest",
            "chocolate",
            "vanilla",
            "pineapple",
            "butterscotch",
            "coffee",
            "strawberry"
        ]

        for flavour in flavours:
            if flavour in t:
                attrs["flavour"] = flavour
                break

        m = re.search(r"(\d+(?:\.\d+)?)\s*kg", t)
        if m:
            attrs["weight_kg"] = float(m.group(1))

        m = re.search(r"(\d+)\s*tier", t)
        if m:
            attrs["tier"] = int(m.group(1))

        if "eggless" in t or "egg free" in t:
            attrs["egg_free"] = True

        if "normal ande" in t or "egg wala" in t:
            attrs["egg_free"] = False

        for shape in ["round", "square"]:
            if shape in t:
                attrs["shape"] = shape
                break

    return attrs


# -----------------------------
# Item extraction
# -----------------------------

def extract_items(domain, text):
    t = normalize(text)
    found = []

    for canonical, variants in ITEMS[domain].items():

        positions = []

        for variant in variants:
            for m in re.finditer(
                re.escape(variant.lower()),
                t
            ):
                positions.append((m.start(), m.end()))

        for start, end in positions:

            # Skip explicitly negated items
            before = t[max(0, start - 25):start]
            after = t[end:min(len(t), end + 25)]

            if re.search(
                r"(nahi|nahin|not|sirf nahi)\s*[,.:;]?\s*$",
                before
            ):
                continue
            if re.match(r"^\s*(nahi|nahin|not|sirf nahi)\b", after):
                continue

            quantity = find_quantity(t, start, end)

            # Avoid duplicate same-position detections
            duplicate = False

            for old in found:
                if old["description"] == canonical and abs(old["_start"] - start) < 3:
                    duplicate = True
                    break

            if duplicate:
                continue

            item = {
                "description": canonical,
                "quantity": quantity,
                "attributes": {},
                "_start": start,
                "_end": end,
            }

            found.append(item)

    found.sort(key=lambda x: x["_start"])

    # Attribute region: until next item
    for i, item in enumerate(found):
        start = item["_start"]

        if i + 1 < len(found):
            end = found[i + 1]["_start"]
        else:
            end = len(t)

        item["attributes"] = extract_attributes(
            domain,
            t,
            start,
            end
        )

    for item in found:
        item.pop("_start", None)
        item.pop("_end", None)

    return found


# -----------------------------
# Clarification
# -----------------------------

def needs_clarification(domain, text, items, due_date):
    t = normalize(text)

    # No identifiable item
    if not items:
        return True

    # Unresolvable deadline was referenced
    unresolved_deadlines = [
        "jaldi",
        "asap",
        "urgent",
        "jab ho jaye",
        "festival se pehle",
        "next week kabhi bhi",
        "agle mahine",
        "mahine ke end tak",
        "diwali se pehle",
        "shaadi se pehle",
        "exam ke baad",
        "jab time mile",
    ]

    for phrase in unresolved_deadlines:
        if phrase in t and due_date is None:
            return True

    # Blocking attribute
    if domain == "electrician":
        if all("issue" not in item["attributes"] for item in items):
            return True

    if domain == "baker":
        if all("flavour" not in item["attributes"] for item in items):
            return True

    # Conflicting quantity pattern
    if re.search(
        r"\b(do|2)\s*(ya|or)\s*(teen|3)\b",
        t
    ):
        return True

    return False


# -----------------------------
# Main parser
# -----------------------------

def parse_record(record):

    text = record["message"]
    domain = record["domain"]

    items = extract_items(domain, text)

    result = {
        "id": record["id"],
        "customer": extract_customer(text),
        "items": items,
        "due_date": extract_due_date(
            text,
            record["received_at"]
        ),
        "amount": extract_amount(text),
        "references_prior_order": extract_prior_order(text),
        "confidence": 0.8,
        "needs_clarification": False,
    }

    result["needs_clarification"] = needs_clarification(
        domain,
        text,
        items,
        result["due_date"]
    )

    return result


# -----------------------------
# Process complete dataset
# -----------------------------

if __name__ == "__main__":

    with open("messages_train.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    predictions = []

    for record in data:
        predictions.append(parse_record(record))

    with open("my_output.json", "w", encoding="utf-8") as file:
        json.dump(
            predictions,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("Done!")
    print("Processed messages:", len(predictions))
    print("Output saved as: my_output.json")