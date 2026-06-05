from .models import Canton

CANTONS = [
    ("AG","Aargau"),("AI","Appenzell Innerrhoden"),("AR","Appenzell Ausserrhoden"),("BE","Bern"),
    ("BL","Basel-Landschaft"),("BS","Basel-Stadt"),("FR","Fribourg"),("GE","Geneva"),
    ("GL","Glarus"),("GR","Graubunden"),("JU","Jura"),("LU","Lucerne"),
    ("NE","Neuchatel"),("NW","Nidwalden"),("OW","Obwalden"),("SG","St. Gallen"),
    ("SH","Schaffhausen"),("SO","Solothurn"),("SZ","Schwyz"),("TG","Thurgau"),
    ("TI","Ticino"),("UR","Uri"),("VD","Vaud"),("VS","Valais"),
    ("ZG","Zug"),("ZH","Zurich")
]

def seed_cantons(db):
    for code, name in CANTONS:
        exists = db.query(Canton).filter(Canton.code == code).first()
        if exists:
            continue
        db.add(Canton(
            code=code,
            name=name,
            geoportal_url=f"https://www.geo.admin.ch/{code.lower()}",
            cadastral_info_url="https://www.cadastre.ch/",
            owner_info_availability="Public summary varies by canton",
            grundbuch_contact="Check canton website / district registry",
            notes="Manual review required for canton-specific restrictions",
            status="not checked"
        ))
    db.commit()

