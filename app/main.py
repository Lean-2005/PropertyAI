from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3, re, json
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "property_ai.db"

app = FastAPI(title="PropertyAI - WildCatter MVP")
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

class SearchRequest(BaseModel):
    query: str
    user_type: str = "buyer"

class EnquiryRequest(BaseModel):
    project_id: int
    name: str
    phone: str = ""
    email: str = ""
    user_type: str = "buyer"

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS developers(
        id INTEGER PRIMARY KEY, name TEXT, score REAL, projects_count INTEGER,
        completion_record REAL, track_record REAL, data_confidence REAL
    );
    CREATE TABLE IF NOT EXISTS projects(
        id INTEGER PRIMARY KEY, name TEXT, developer_id INTEGER, location TEXT,
        property_type TEXT, bedrooms INTEGER, price_cr REAL, completion_date TEXT,
        lat REAL, lng REAL, rera_number TEXT,
        FOREIGN KEY(developer_id) REFERENCES developers(id)
    );
    CREATE TABLE IF NOT EXISTS searches(
        id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT, user_type TEXT,
        parsed_filters TEXT, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS enquiries(
        id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER,
        name TEXT, phone TEXT, email TEXT, user_type TEXT, created_at TEXT
    );
    """)
    if cur.execute("SELECT COUNT(*) FROM developers").fetchone()[0] == 0:
        developers = [
            (1,"Apex Urban Developers",8.7,12,9.0,8.5,8.6),
            (2,"Harbourline Realty",8.1,8,8.0,8.2,8.1),
            (3,"MetroNest Developers",7.8,6,7.6,8.0,7.8),
            (4,"BlueStone Homes",8.4,10,8.5,8.1,8.5),
        ]
        cur.executemany("INSERT INTO developers VALUES (?,?,?,?,?,?,?)", developers)
        projects = [
            (1,"Apex Lokhandwala Heights",1,"Lokhandwala, Andheri West","Residential",2,6.25,"2027-05-31",19.1364,72.8240,"P51800000001"),
            (2,"Apex Lokhandwala Residences",1,"Lokhandwala, Andheri West","Residential",2,7.80,"2027-06-30",19.1390,72.8262,"P51800000002"),
            (3,"Harbourline One",2,"Lokhandwala, Andheri West","Residential",2,5.95,"2027-04-30",19.1328,72.8214,"P51800000003"),
            (4,"MetroNest Sky Gardens",3,"Lokhandwala, Andheri West","Residential",3,7.25,"2027-08-31",19.1412,72.8290,"P51800000004"),
            (5,"BlueStone Urbania",4,"Lokhandwala, Andheri West","Residential",2,7.40,"2027-06-15",19.1348,72.8277,"P51800000005"),
            (6,"Harbourline Park View",2,"Andheri West","Residential",2,6.90,"2027-03-31",19.1240,72.8350,"P51800000006"),
            (7,"BlueStone Central",4,"Bandra West","Residential",2,7.95,"2027-06-30",19.0607,72.8362,"P51800000007"),
            (8,"MetroNest Andheri Central",3,"Andheri West","Residential",1,4.25,"2027-05-31",19.1197,72.8468,"P51800000008"),
        ]
        cur.executemany("INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?,?,?)", projects)
    con.commit()
    con.close()

def parse_query(q: str):
    s = q.lower()
    bedrooms = None
    m = re.search(r'(\d+)\s*(?:bedroom|bedrooms|bhk|bhk)', s)
    if m: bedrooms = int(m.group(1))

    max_price = None
    m = re.search(r'(?:below|under|less than|upto|up to|maximum|max)\s*(?:rs\.?|₹)?\s*([\d.]+)\s*(cr|crore|crores|lakh|lakhs)?', s)
    if m:
        val = float(m.group(1)); unit = m.group(2) or "cr"
        max_price = val / 100 if "lakh" in unit else val

    location = None
    locations = ["lokhandwala", "andheri west", "bandra west", "borivali", "malad", "powai", "thane", "mumbai"]
    for loc in locations:
        if loc in s:
            location = loc.title()
            break

    completion = None
    months = {
        "january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
        "july":7,"august":8,"september":9,"october":10,"november":11,"december":12
    }
    m = re.search(r'(?:by|before|completed by|completion by)\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})', s)
    if m:
        completion = f"{m.group(2)}-{months[m.group(1)]:02d}-30"
    elif "june 2027" in s:
        completion = "2027-06-30"

    prop_type = "Residential" if "residential" in s else None
    return {
        "property_type": prop_type,
        "bedrooms": bedrooms,
        "max_price_cr": max_price,
        "location": location,
        "completion_by": completion
    }

def project_dict(row):
    d = dict(row)
    d["developer_score"] = d.pop("score", None)
    return d

@app.on_event("startup")
def startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE / "templates" / "index.html").read_text(encoding="utf-8")

@app.post("/api/search")
def search(req: SearchRequest):
    filters = parse_query(req.query)
    con = db()
    where, params = [], []
    if filters["property_type"]:
        where.append("p.property_type = ?"); params.append(filters["property_type"])
    if filters["bedrooms"]:
        where.append("p.bedrooms = ?"); params.append(filters["bedrooms"])
    if filters["max_price_cr"] is not None:
        where.append("p.price_cr <= ?"); params.append(filters["max_price_cr"])
    if filters["location"] and filters["location"].lower() != "mumbai":
        where.append("LOWER(p.location) LIKE ?"); params.append("%"+filters["location"].lower()+"%")
    if filters["completion_by"]:
        where.append("p.completion_date <= ?"); params.append(filters["completion_by"])
    sql = """SELECT p.*, d.name developer_name, d.score, d.completion_record,
             d.track_record, d.data_confidence
             FROM projects p JOIN developers d ON p.developer_id=d.id"""
    if where: sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY d.score DESC, p.price_cr ASC"
    rows = con.execute(sql, params).fetchall()
    con.execute("INSERT INTO searches(query,user_type,parsed_filters,created_at) VALUES(?,?,?,?)",
                (req.query, req.user_type, json.dumps(filters), datetime.now().isoformat()))
    con.commit(); con.close()
    return {"filters": filters, "count": len(rows), "projects": [project_dict(r) for r in rows]}

@app.post("/api/enquiry")
def enquiry(req: EnquiryRequest):
    con = db()
    con.execute("""INSERT INTO enquiries(project_id,name,phone,email,user_type,created_at)
                   VALUES(?,?,?,?,?,?)""",
                (req.project_id,req.name,req.phone,req.email,req.user_type,datetime.now().isoformat()))
    con.commit(); con.close()
    return {"ok": True, "message": "Developer contact request recorded."}

@app.get("/api/dashboard/{user_type}")
def dashboard(user_type: str):
    con = db()
    searches = con.execute("SELECT * FROM searches WHERE user_type=? ORDER BY id DESC LIMIT 10",(user_type,)).fetchall()
    enquiries = con.execute("""SELECT e.*, p.name project_name, d.name developer_name
                               FROM enquiries e JOIN projects p ON e.project_id=p.id
                               JOIN developers d ON p.developer_id=d.id
                               ORDER BY e.id DESC LIMIT 10""").fetchall()
    con.close()
    return {"searches":[dict(x) for x in searches], "enquiries":[dict(x) for x in enquiries]}

@app.get("/api/developers")
def developers():
    con=db()
    rows=con.execute("SELECT * FROM developers ORDER BY score DESC").fetchall()
    con.close()
    return {"developers":[dict(x) for x in rows]}

@app.get("/api/projects")
def projects():
    con=db()
    rows=con.execute("""SELECT p.*, d.name developer_name, d.score
                        FROM projects p JOIN developers d ON p.developer_id=d.id""").fetchall()
    con.close()
    return {"projects":[project_dict(x) for x in rows]}
