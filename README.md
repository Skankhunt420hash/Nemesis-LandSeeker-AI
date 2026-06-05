# LandSeeker AI

LandSeeker AI ist eine frohe, einfache und lebendige App fuer die Recherche potenziell herrenloser Grundstuecke in der Schweiz.

## Was jetzt drin ist
- Responsive Oberflaeche fuer Smartphone und PC
- Native Android-App-Schicht ueber Capacitor
- FastAPI Backend
- Celery Worker mit lokalem SQLite-Broker
- Kartenansicht, Kandidatenliste, Briefgenerator, WFS/CSV Import

## Rechtlicher Rahmen
- Massgeblich ist `Art. 658 ZGB`
- Kein Auto-Claim
- Keine automatische Einreichung
- Jeder Kandidat muss beim zustaendigen Grundbuchamt verifiziert werden

## Wichtige Wahrheit zur nativen App
Die App ist jetzt als native Android-App vorbereitet.

Wichtig:
- Die Benutzeroberflaeche laeuft nativ im Handy-Container
- Das aktuelle Python Backend und Celery laufen nicht direkt auf Android im App-Paket
- Die native App verbindet sich deshalb mit einer erreichbaren FastAPI-Instanz, z. B. deinem Rechner im selben WLAN oder spaeter einem kleinen Server

Wenn du willst, koennen wir spaeter noch eine echte Voll-Portierung auf Android planen. Das waere aber ein groesserer Umbau, weil FastAPI + Celery + Python nicht einfach 1:1 lokal in eine klassische Handy-App eingebettet werden.

## Desktop Start
### Alles in einem
```powershell
.\start-all.ps1
```

Oder per Doppelklick:
- [Start LandSeeker AI.cmd](<C:\Users\elbbu\Documents\Nemesis Swiss Land King\Start LandSeeker AI.cmd>)

Das startet:
- Frontend-Build
- FastAPI auf Port `8000`
- Celery Worker

## Native Android vorbereiten
### Voraussetzungen
- Node.js
- Python
- Java
- Android Studio fuer spaeteren APK-Build

### Frontend und Native Shell vorbereiten
```powershell
cd frontend
npm install
npm run native:build
```

Oder ueber das Hilfsskript:
```powershell
.\build-android.ps1
```

### Android Studio oeffnen
```powershell
cd frontend
npm run native:open
```

Danach kannst du in Android Studio:
- Emulator starten
- APK bauen
- App auf dein Handy installieren

## Native Nutzung auf dem Handy
1. App auf dem Handy starten
2. In der App die Server-Adresse setzen, z. B. `http://192.168.1.20:8000`
3. Rechner mit laufendem Backend im selben WLAN lassen
4. App verbindet sich dann mit FastAPI und Celery

## Projektdateien
- [backend/app/main.py](<C:\Users\elbbu\Documents\Nemesis Swiss Land King\backend\app\main.py>)
- [frontend/src/App.jsx](<C:\Users\elbbu\Documents\Nemesis Swiss Land King\frontend\src\App.jsx>)
- [frontend/capacitor.config.ts](<C:\Users\elbbu\Documents\Nemesis Swiss Land King\frontend\capacitor.config.ts>)
- [start-all.ps1](<C:\Users\elbbu\Documents\Nemesis Swiss Land King\start-all.ps1>)
- [build-android.ps1](<C:\Users\elbbu\Documents\Nemesis Swiss Land King\build-android.ps1>)
