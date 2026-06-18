"""Génère des données factices (PII, montants, patterns, dates) via un helper Python."""
import sys
import json
import csv
import io
import random
import datetime
import string

random.seed()

LETTERS_UPPER = string.ascii_uppercase
LETTERS_LOWER = string.ascii_lowercase
DIGITS = string.digits

FIRST_NAMES = [
    "Jean","Marie","Pierre","Sophie","Lucas","Emma","Louis","Alice","Thomas","Léa",
    "Antoine","Chloé","Alexandre","Camille","Nicolas","Sarah","Raphaël","Manon","Jules","Laura",
    "Hugo","Inès","Clément","Juliette","Maxime","Pauline","Arthur","Elise","Baptiste","Océane",
    "Jade","John","Jane","Michael","Emily","David","Jessica","Chris","Ashley","Brandon",
    "Marco","Giulia","Lorenzo","Francesca","Alessandro","Sofia","Luca","Elena","Matteo","Valentina",
    "Hans","Anna","Felix","Mia","Lukas","Emma","Noah","Sophia","Elias","Lea",
    "Pedro","Ana","Carlos","Maria","Miguel","Isabel","Jose","Carmen","Antonio","Lucia",
    "Abdou","Aïcha","Omar","Fatima","Ali","Khadija","Hassan","Mariam","Said","Amina",
    "Takashi","Yuki","Sakura","Haruki","Akiko","Ryo","Yuko","Kenji","Kaori","Daisuke"
]

LAST_NAMES = [
    "Martin","Bernard","Dubois","Thomas","Robert","Richard","Petit","Durand","Leroy","Moreau",
    "Simon","Laurent","Lefebvre","Michel","Garcia","David","Bertrand","Roux","Vincent","Fournier",
    "Morel","Girard","Andre","Mercier","Dupont","Lambert","Bonnet","Francois","Martinez","Legrand",
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
    "Rossi","Russo","Ferrari","Esposito","Bianchi","Romano","Colombo","Ricci","Marino","Greco",
    "Mueller","Schmidt","Schneider","Fischer","Weber","Wagner","Becker","Hoffmann","Schaefer","Koch",
    "Garcia","Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Perez","Sanchez","Ramirez","Torres",
    "Silva","Santos","Oliveira","Souza","Lima","Pereira","Costa","Ferreira","Almeida","Nascimento"
]

CITIES = [
    "Paris","Lyon","Marseille","Toulouse","Bordeaux","Lille","Strasbourg","Nantes","Montpellier","Rennes",
    "New York","Los Angeles","Chicago","Houston","Phoenix","Philadelphia","San Antonio","San Diego","Dallas","Austin",
    "Rome","Milan","Naples","Turin","Palerme","Genoa","Bologna","Florence","Venice","Verona",
    "Berlin","Munich","Hamburg","Cologne","Frankfurt","Stuttgart","Dusseldorf","Leipzig","Dresden","Bremen",
    "Madrid","Barcelona","Valencia","Seville","Bilbao","Malaga","Zaragoza","Murcia","Palma","Granada",
    "Casablanca","Rabat","Marrakech","Fes","Tangier","Agadir","Meknes","Oujda","Kenitra","Tetouan",
    "Tokyo","Yokohama","Osaka","Nagoya","Sapporo","Fukuoka","Kobe","Kyoto","Kawasaki","Saitama"
]

STREETS = [
    "Rue de la Paix","Rue du Faubourg Saint-Honoré","Avenue des Champs-Élysées","Boulevard Saint-Germain",
    "Rue de Rivoli","Place de la Concorde","Avenue Montaigne","Rue du Commerce","Boulevard Haussmann",
    "Place des Vosges","Main Street","Broadway","Park Avenue","Fifth Avenue","Oak Street",
    "Maple Avenue","Cedar Lane","Elm Street","Pine Drive","Washington Street",
    "Via Roma","Corso Vittorio Emanuele","Via del Corso","Via Nazionale","Piazza Navona",
    "Hauptstrasse","Bahnhofstrasse","Schlossstrasse","Kirchgasse","Marktplatz",
    "Calle Mayor","Avenida Diagonal","Gran Via","Paseo de la Castellana","Calle Serrano"
]

EMAIL_DOMAINS = ["gmail.com","yahoo.fr","orange.fr","free.fr","laposte.net","hotmail.fr","outlook.com","icloud.com"]
LOREM = "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum".split()

class GenContext:
    def __init__(self, row_idx: int):
        self.row_idx = row_idx

def _pick(seq): return random.choice(seq)
def _randint(a, b): return random.randint(a, b)
def _randfloat(a, b, dec=2): return round(random.uniform(a, b), dec)

def _expand_pattern(pattern: str) -> str:
    result = []
    for ch in pattern:
        if ch == '#': result.append(_pick(DIGITS))
        elif ch == 'A': result.append(_pick(LETTERS_UPPER))
        elif ch == 'a': result.append(_pick(LETTERS_LOWER))
        elif ch == 'X': result.append(_pick(DIGITS + LETTERS_UPPER))
        elif ch == 'x': result.append(_pick(DIGITS + LETTERS_LOWER))
        elif ch == '?': result.append(_pick(LETTERS_UPPER + LETTERS_LOWER))
        else: result.append(ch)
    return "".join(result)

GENERATORS = {
    "id": lambda c, ctx: str(int(c.get("start", 1)) + ctx.row_idx * int(c.get("step", 1))),
    "integer": lambda c, ctx: str(_randint(int(c.get("min", 0)), int(c.get("max", 99999)))),
    "float": lambda c, ctx: f"{_randfloat(float(c.get('min',0)), float(c.get('max',99999)), int(c.get('decimals',2))):.{int(c.get('decimals',2))}f}",
    "boolean": lambda c, ctx: str(random.choice([True, False])),
    "date": lambda c, ctx: (lambda fmt=c.get("format","%Y-%m-%d"), mn=datetime.date.fromisoformat(c.get("min","2020-01-01")), mx=datetime.date.fromisoformat(c.get("max",datetime.date.today().isoformat())): (mn + datetime.timedelta(days=_randint(0,max(0,(mx-mn).days)))) .strftime(fmt))(),
    "datetime": lambda c, ctx: (lambda fmt=c.get("format","%Y-%m-%d %H:%M:%S"), mn=datetime.datetime.fromisoformat(c.get("min","2020-01-01T00:00:00")), mx=datetime.datetime.fromisoformat(c.get("max",datetime.datetime.now().isoformat())): (mn + datetime.timedelta(seconds=_randint(0,max(0,int((mx-mn).total_seconds()))))) .strftime(fmt))(),
    "time": lambda c, ctx: datetime.time(_randint(int(c.get("minHour",0)),int(c.get("maxHour",23))), _randint(int(c.get("minMinute",0)),int(c.get("maxMinute",59))), _randint(0,59)).strftime(c.get("format","%H:%M:%S")),
    "first_name": lambda c, ctx: _pick(FIRST_NAMES),
    "last_name": lambda c, ctx: _pick(LAST_NAMES),
    "full_name": lambda c, ctx: f"{_pick(FIRST_NAMES)} {_pick(LAST_NAMES)}",
    "email": lambda c, ctx: (lambda fn=_pick(FIRST_NAMES).lower(), ln=_pick(LAST_NAMES).lower(): f"{fn}{_pick(['.','-','_',''])}{ln}{str(_randint(1,999)) if random.random()<0.3 else ''}@{_pick(EMAIL_DOMAINS)}")(),
    "phone": lambda c, ctx: (lambda p=c.get("prefix",_pick(["01","02","03","04","05","06","07","+331","+336","+337","+33","06","07"])): f"{p}{''.join(_pick(DIGITS) for _ in range(8))}")(),
    "country": lambda c, ctx: _pick([("France","FR"),("Belgique","BE"),("Suisse","CH"),("Canada","CA"),("Allemagne","DE"),("Espagne","ES"),("Italie","IT"),("Royaume-Uni","GB"),("États-Unis","US"),("Portugal","PT"),("Pays-Bas","NL"),("Maroc","MA"),("Tunisie","TN"),("Sénégal","SN"),("Japon","JP"),("Luxembourg","LU")])[0 if c.get("format","name")=="name" else 1],
    "city": lambda c, ctx: _pick(CITIES),
    "address": lambda c, ctx: f"{_randint(1,999)}, {_pick(STREETS)}, {_pick(CITIES)}",
    "postal_code": lambda c, ctx: _expand_pattern({"FR":"#####","BE":"####","CH":"####","CA":"A#A #A#","DE":"#####","ES":"#####","IT":"#####","GB":"??# #??","US":"#####-####","PT":"####-###","NL":"####??","MA":"#####","TN":"####","SN":"#####","JP":"###-####","LU":"####","AT":"####","IE":"??# ?#??","SE":"### ##","NO":"####"}.get(c.get("country","FR"),"#####")),
    "text": lambda c, ctx: " ".join(_pick(LOREM) for _ in range(_randint(int(c.get("minWords",5)), int(c.get("maxWords",20))))),
    "pattern": lambda c, ctx: _expand_pattern(c.get("pattern","###-AAA-###")),
    "prenom": lambda c, ctx: _pick(FIRST_NAMES),
    "nom": lambda c, ctx: _pick(LAST_NAMES),
}

def parse_columns(cols_raw):
    cols = []
    if isinstance(cols_raw, list):
        for item in cols_raw:
            cols.append(item if isinstance(item, dict) else {"name": str(item), "type": "text"})
    elif isinstance(cols_raw, str):
        for p in [p.strip() for p in cols_raw.split(",")]:
            cols.append({"name": p.split(":")[0].strip(), "type": p.split(":")[1].strip()} if ":" in p else {"name": p, "type": "text"})
    return cols

def generate_rows(columns, count, fmt):
    cols = parse_columns(columns)
    if fmt == "json":
        rows = []
        for i in range(count):
            ctx = GenContext(i)
            rows.append({c["name"]: GENERATORS.get(c.get("type","text"), GENERATORS["text"])(c, ctx) for c in cols})
        return json.dumps(rows, ensure_ascii=False, indent=2)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow([c["name"] for c in cols])
    for i in range(count):
        ctx = GenContext(i)
        w.writerow([GENERATORS.get(c.get("type","text"), GENERATORS["text"])(c, ctx) for c in cols])
    return buf.getvalue()

def main():
    if len(sys.argv) < 4:
        print(f"Usage: python fake_gen_helper.py <columns_json> <count> <format> [destination]", file=sys.stderr)
        sys.exit(1)
    columns_raw = sys.argv[1]
    count = int(sys.argv[2])
    fmt = sys.argv[3].lower()
    destination = sys.argv[4] if len(sys.argv) > 4 else ""
    try:
        columns = json.loads(columns_raw)
    except (json.JSONDecodeError, TypeError):
        columns = columns_raw
    output = generate_rows(columns, count, fmt)
    if destination:
        with open(destination, "w", encoding="utf-8") as f:
            f.write(output)
    sys.stdout.write(output)

if __name__ == "__main__":
    main()
