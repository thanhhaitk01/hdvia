
import math, re, json, unicodedata, urllib.parse, urllib.request, os
from api_adapters import OPEN_API_ADAPTER
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from coverage_registry import resolve_known_place

PLACE_CACHE = {
    "huế": ("Huế",16.4637,107.5909), "hue": ("Huế",16.4637,107.5909),
    "đà nẵng": ("Đà Nẵng",16.0544,108.2022), "da nang": ("Đà Nẵng",16.0544,108.2022),
    "hội an": ("Hội An",15.8801,108.3380), "hoi an": ("Hội An",15.8801,108.3380),
    "bà nà": ("Bà Nà Hills",15.9977,107.9898), "ba na": ("Bà Nà Hills",15.9977,107.9898),
    "sơn trà": ("Sơn Trà",16.1060,108.2700), "son tra": ("Sơn Trà",16.1060,108.2700),
    "mỹ sơn": ("Mỹ Sơn",15.7647,108.1194), "my son": ("Mỹ Sơn",15.7647,108.1194),
    "quảng ngãi": ("Quảng Ngãi",15.1214,108.8044), "quang ngai": ("Quảng Ngãi",15.1214,108.8044),
    "hà nội": ("Hà Nội",21.0285,105.8542), "ha noi": ("Hà Nội",21.0285,105.8542),
    "hạ long": ("Hạ Long",20.9101,107.1839), "ha long": ("Hạ Long",20.9101,107.1839),
    "ninh bình": ("Ninh Bình",20.2506,105.9745), "ninh binh": ("Ninh Bình",20.2506,105.9745),
    "sa pa": ("Sa Pa",22.3364,103.8438), "sapa": ("Sa Pa",22.3364,103.8438),
    "phong nha": ("Phong Nha – Kẻ Bàng",17.5916,106.2823),
    "quảng bình": ("Quảng Bình",17.4676,106.6220), "quang binh": ("Quảng Bình",17.4676,106.6220),
    "nha trang": ("Nha Trang",12.2388,109.1967),
    "đà lạt": ("Đà Lạt",11.9404,108.4583), "da lat": ("Đà Lạt",11.9404,108.4583),
    "tp hồ chí minh": ("TP. Hồ Chí Minh",10.8231,106.6297), "ho chi minh": ("TP. Hồ Chí Minh",10.8231,106.6297),
    "thành phố hồ chí minh": ("TP. Hồ Chí Minh",10.8231,106.6297),
    "cần thơ": ("Cần Thơ",10.0452,105.7469), "can tho": ("Cần Thơ",10.0452,105.7469),
    "phú quốc": ("Phú Quốc",10.2899,103.9840), "phu quoc": ("Phú Quốc",10.2899,103.9840),
}
WEATHER_CODES = {
0:"Trời quang",1:"Ít mây",2:"Mây rải rác",3:"Nhiều mây",45:"Sương mù",48:"Sương mù",
51:"Mưa phùn nhẹ",53:"Mưa phùn",55:"Mưa phùn dày",61:"Mưa nhẹ",63:"Mưa vừa",65:"Mưa to",
71:"Tuyết nhẹ",73:"Tuyết",75:"Tuyết dày",80:"Mưa rào nhẹ",81:"Mưa rào",82:"Mưa rào mạnh",
95:"Dông",96:"Dông có mưa đá",99:"Dông mạnh"
}

def haversine_km(a,b):
    R=6371.0
    p1,p2=math.radians(a["lat"]),math.radians(b["lat"])
    dp=math.radians(b["lat"]-a["lat"]); dl=math.radians(b["lon"]-a["lon"])
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return round(R*2*math.asin(math.sqrt(x)),1)

def target_aliases(name):
    n=(name or "").lower()
    return {n, n.replace(" hills","").strip()}

class JourneyIntelligenceEngine:
    VERSION="1.14.7"

    PLACE_ALIASES = {
        "ba na hill": "Bà Nà Hills", "ba na hills": "Bà Nà Hills",
        "bana": "Bà Nà Hills", "ba na": "Bà Nà Hills",
        "pho co hoi an": "Hội An", "phố cổ hội an": "Hội An",
        "thanh dia my son": "Mỹ Sơn", "thánh địa mỹ sơn": "Mỹ Sơn",
        "san bay da nang": "Đà Nẵng", "sân bay đà nẵng": "Đà Nẵng",
        "son tra": "Sơn Trà", "sơn trà": "Sơn Trà",
    }

    AMBIGUOUS_PLACES = {
        "linh ung": ["Chùa Linh Ứng Sơn Trà", "Chùa Linh Ứng Bà Nà", "Chùa Linh Ứng Ngũ Hành Sơn"],
        "chua linh ung": ["Chùa Linh Ứng Sơn Trà", "Chùa Linh Ứng Bà Nà", "Chùa Linh Ứng Ngũ Hành Sơn"],
    }

    def __init__(self, weather_provider=None, geocoder=None):
        self.weather_provider=weather_provider or self._open_meteo
        self.geocoder=geocoder or self._open_api_geocoder

    def parse_days(self, raw):
        """Parse both structured and natural Vietnamese day markers.

        Accepted examples include:
        - Ngày 1: Đà Nẵng -> Hội An
        - Ngày 1 Đà Nẵng, Ngày 2 Hội An, Ngày 3 Huế
        - ngày đầu Đà Nẵng; ngày hôm sau Hội An
        The parser preserves free-form text instead of forcing a rigid template.
        """
        raw = (raw or "").replace("\r", "\n").strip()
        if not raw:
            return []
        marker = re.compile(r"(?i)(?:^|[\n;|,])\s*(ngày|day)\s*(\d+)\s*[:\-]?\s*")
        matches=list(marker.finditer(raw))
        days=[]
        if matches:
            for i,m in enumerate(matches):
                end=matches[i+1].start() if i+1<len(matches) else len(raw)
                text=raw[m.end():end].strip(" \n\t,;|-")
                days.append({"day":int(m.group(2)),"text":text})
        else:
            # Natural ordinal day references are handled conservatively.
            ordinal=re.compile(r"(?i)(?:^|[\n;|,])\s*(ngày đầu(?: tiên)?|ngày thứ (\d+)|ngày hôm sau|ngày tiếp theo)\s*[:\-]?\s*")
            om=list(ordinal.finditer(raw))
            if om:
                next_day=1
                for i,m in enumerate(om):
                    token=m.group(1).lower()
                    explicit=m.group(2)
                    day=int(explicit) if explicit else next_day
                    end=om[i+1].start() if i+1<len(om) else len(raw)
                    text=raw[m.end():end].strip(" \n\t,;|-")
                    days.append({"day":day,"text":text})
                    next_day=day+1
        if not days:
            parts=[p.strip() for p in re.split(r"\n+|[;|]+",raw) if p.strip()]
            days=[{"day":i+1,"text":p} for i,p in enumerate(parts[:14])]
        # Keep day order stable and cap analysis to the documented 14-day window.
        days=sorted(days, key=lambda d:d["day"])[:14]
        for d in days:
            d["places"]=self.detect_places(d["text"])
            d["time_windows"]=self.detect_time_windows(d["text"])
            d["activities"]=self.detect_activities(d["text"])
        return days

    def detect_time_windows(self, text):
        q=(text or "").lower()
        found=[]
        patterns=[
            (r"\b(?:sáng|buổi sáng|morning)\b","morning"),
            (r"\b(?:trưa|buổi trưa|noon|lunch)\b","noon"),
            (r"\b(?:chiều|buổi chiều|afternoon)\b","afternoon"),
            (r"\b(?:tối|buổi tối|evening|dinner)\b","evening"),
            (r"\b(?:đêm|qua đêm|overnight)\b","overnight"),
        ]
        for pattern,label in patterns:
            if re.search(pattern,q): found.append(label)
        for m in re.finditer(r"\b(\d{1,2})(?::(\d{2}))?\s*(?:-|đến|to)\s*(\d{1,2})(?::(\d{2}))?\s*(?:giờ|h)?\b",q):
            found.append({"from":f"{int(m.group(1)):02d}:{int(m.group(2) or 0):02d}","to":f"{int(m.group(3)):02d}:{int(m.group(4) or 0):02d}"})
        return found

    def detect_activities(self, text):
        q=(text or "").lower()
        mapping={
            "sightseeing":["tham quan","tham quan phố cổ","tham quan di tích","ngắm cảnh"],
            "food":["ăn trưa","ăn tối","ăn sáng","ẩm thực","nhà hàng","bữa trưa","bữa tối"],
            "checkin":["check-in","check in","nhận phòng","trả phòng"],
            "outdoor":["đi bộ","leo núi","tắm biển","dù lượn","trekking","ngoài trời"],
            "transfer":["đón khách","tiễn khách","di chuyển","đi từ","đưa khách","sân bay"],
        }
        return [kind for kind,terms in mapping.items() if any(t in q for t in terms)]

    def resolve_place_mentions(self, text):
        """Return canonical place aliases and ambiguity notices without guessing."""
        q = " ".join((text or "").lower().split())
        q_ascii = "".join(c for c in unicodedata.normalize("NFD", q) if unicodedata.category(c) != "Mn")
        aliases = []
        for alias, canonical in self.PLACE_ALIASES.items():
            alias_ascii = "".join(c for c in unicodedata.normalize("NFD", alias) if unicodedata.category(c) != "Mn")
            if alias in q or alias_ascii in q_ascii:
                aliases.append({"mention":alias,"resolved":canonical,"confidence":"HIGH"})
        ambiguous = []
        seen_ambiguous = set()
        for alias, candidates in self.AMBIGUOUS_PLACES.items():
            alias_ascii = "".join(c for c in unicodedata.normalize("NFD", alias) if unicodedata.category(c) != "Mn")
            if alias in q or alias_ascii in q_ascii:
                key=tuple(candidates)
                if key not in seen_ambiguous:
                    ambiguous.append({"mention":alias,"candidates":candidates,"confidence":"LOW","action":"Cần HDV chọn đúng địa điểm trước khi tối ưu tuyến."})
                    seen_ambiguous.add(key)
        return {"aliases":aliases,"ambiguous":ambiguous}

    def detect_places(self,text):
        """Resolve known places in the order they appear, including common HDV aliases."""
        low=(text or "").lower()
        aliases=self.resolve_place_mentions(text)
        canonical_mentions=[a["resolved"] for a in aliases["aliases"]]
        matches=[]; seen=set()
        for key,(name,lat,lon) in PLACE_CACHE.items():
            if name in seen or key not in low:
                continue
            start=low.find(key)
            matches.append((start,{"name":name,"lat":lat,"lon":lon,"source":"hdvia-cache"}))
            seen.add(name)
        for canonical in canonical_mentions:
            for key,(name,lat,lon) in PLACE_CACHE.items():
                if name == canonical and name not in seen:
                    start=low.find(next((a["mention"] for a in aliases["aliases"] if a["resolved"]==canonical), canonical.lower()))
                    matches.append((start,{"name":name,"lat":lat,"lon":lon,"source":"hdvia-alias"})); seen.add(name); break
        matches.sort(key=lambda item:item[0])
        found=[item[1] for item in matches]
        # Preserve recognized Vietnam tourism names even when this local route cache
        # has no coordinates. Never silently drop a known place from a journey.
        for item in resolve_known_place(text or ""):
            name=item.get("name")
            catalog=item.get("catalog") or {}
            canonical_catalog_name=catalog.get("name")
            if canonical_catalog_name and canonical_catalog_name in seen:
                continue
            if not name or name in seen: continue
            if catalog.get("lat") is not None and catalog.get("lon") is not None:
                found.append({"name":name,"lat":catalog["lat"],"lon":catalog["lon"],"source":"hdvia-catalog"})
            else:
                found.append({"name":name,"lat":None,"lon":None,"source":"coverage-registry","province":item.get("province"),"region":item.get("region"),"route_ready":False})
            seen.add(name)
        if not found and not aliases["ambiguous"]:
            for part in re.split(r"\s*(?:→|->|>|,)\s*",text or ""):
                part=" ".join(part.split())
                if 2<=len(part)<=45:
                    p=self.geocoder(part)
                    if p: found.append(p); break
        return found

    def _open_api_geocoder(self,name):
        """Use the configured Open API adapter; return HDVIA place shape."""
        result=OPEN_API_ADAPTER.geocode(name)
        for item in (result.get("data",{}).get("results",[]) if result.get("ok") else []):
            lat=item.get("latitude"); lon=item.get("longitude")
            if lat is not None and lon is not None:
                return {"name":item.get("name") or name,"lat":float(lat),"lon":float(lon),"source":"open-meteo-geocoding","route_ready":True}
        return self._nominatim(name)

    def _nominatim(self,name):
        try:
            q=urllib.parse.urlencode({"q":name+", Vietnam","format":"jsonv2","limit":1})
            req=urllib.request.Request(
                "https://nominatim.openstreetmap.org/search?"+q,
                headers={"User-Agent":"HDVIA/1.8.1-beta-commercial Journey Intelligence"})
            with urllib.request.urlopen(req,timeout=6) as r:
                data=json.loads(r.read().decode("utf-8"))
            if data:
                return {"name":name,"lat":float(data[0]["lat"]),
                        "lon":float(data[0]["lon"]),"source":"nominatim"}
        except Exception:
            return None

    def _fallback_weather(self):
        today=datetime.now().date()
        return [{"date":str(today+timedelta(days=i)),"condition":"Chưa có dữ liệu",
                 "code":-1,"tmin":None,"tmax":None,"rain":None,"wind":None} for i in range(7)]

    def _open_meteo(self,p):
        """Open-Meteo adapter with the existing deterministic fallback."""
        live=OPEN_API_ADAPTER.weather(float(p["lat"]), float(p["lon"]), 7)
        daily=live.get("data",{}).get("daily",{}) if live.get("ok") else {}
        if daily.get("time"):
            out=[]
            for i,date in enumerate(daily.get("time",[])):
                code=(daily.get("weather_code") or [None])[i]
                out.append({"date":date,"condition":WEATHER_CODES.get(code,"Không rõ"),"code":code,
                            "tmin":(daily.get("temperature_2m_min") or [None])[i],
                            "tmax":(daily.get("temperature_2m_max") or [None])[i],
                            "rain":(daily.get("precipitation_probability_max") or [None])[i],
                            "wind":(daily.get("wind_speed_10m_max") or [None])[i]})
            return out
        return self._fallback_weather()

    def _normalize_weather(self, weather):
        """Guarantee exactly 7 forecast slots without replacing real dates."""
        if not isinstance(weather, list):
            weather=[]
        clean=[x for x in weather if isinstance(x,dict)]
        seen_dates=set(); unique=[]
        for item in clean:
            key=str(item.get("date", ""))
            if key and key in seen_dates:
                continue
            if key: seen_dates.add(key)
            unique.append(item)
        clean=unique[:7]
        if len(clean)>=7: return clean
        base=datetime.now().date()
        valid=[]
        for item in clean:
            try: valid.append(datetime.fromisoformat(str(item.get("date"))).date())
            except Exception: pass
        if valid: base=max(valid)+timedelta(days=1)
        for i in range(7-len(clean)):
            date=str(base+timedelta(days=i))
            if date in seen_dates: continue
            clean.append({"date":date,"condition":"Chưa có dữ liệu","code":-1,
                          "tmin":None,"tmax":None,"rain":None,"wind":None})
        return clean[:7]

    def _forecast_for_day(self, place_name, day_number, weather, calendar_weather=None):
        """Select only the forecast that belongs to this journey day."""
        if calendar_weather and place_name in calendar_weather:
            item=calendar_weather.get(place_name,{}).get(day_number)
            if isinstance(item,dict): return [item]
        forecast=weather.get(place_name) or []
        if 1<=day_number<=len(forecast) and isinstance(forecast[day_number-1],dict):
            return [forecast[day_number-1]]
        return []

    def risk(self,w):
        valid=[x for x in w if x.get("code") is not None]
        if not valid or all(x.get("code",-1)<0 for x in valid):
            return {"level":"UNKNOWN","reason":"Chưa đủ dữ liệu thời tiết.","action":"Kiểm tra lại trước tour."}
        rain=max((x.get("rain") or 0) for x in valid)
        wind=max((x.get("wind") or 0) for x in valid)
        severe=sum(1 for x in valid if x.get("code",0)>=80)
        hot=any((x.get("tmax") or 0)>=35 for x in valid)
        if severe or wind>=45 or rain>=70: level="HIGH"
        elif wind>=30 or rain>=45 or hot: level="MEDIUM"
        else: level="LOW"
        action={"HIGH":"Chuẩn bị Plan B và thông báo HDV/khách.",
                "MEDIUM":"Theo dõi sát, chừa buffer và chuẩn bị phương án thay thế.",
                "LOW":"Theo dõi thông thường."}[level]
        return {"level":level,"reason":"Mưa/gió/nhiệt độ có thể ảnh hưởng hoạt động ngoài trời.",
                "action":action}

    def _parse_start_date(self, start_date):
        if not start_date:
            return None
        if isinstance(start_date, datetime):
            return start_date.date()
        value=str(start_date).strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    def _time_window_minutes(self, windows):
        total=0
        explicit=[]
        for w in windows or []:
            if not isinstance(w, dict):
                continue
            def mins(v):
                h,m=map(int,str(v).split(":")); return h*60+m
            a,b=mins(w["from"]),mins(w["to"])
            if b < a:
                b += 24*60
            total += b-a
            explicit.append((a,b))
        return total, explicit

    def _activity_minutes(self, activities, places_count):
        base={"sightseeing":120,"food":60,"checkin":45,"outdoor":120,"transfer":30}
        total=sum(base.get(x,0) for x in activities or [])
        if not total and places_count:
            total=90*places_count
        return total

    def _calendarized_weather(self, weather, start_date, days):
        start=self._parse_start_date(start_date)
        if not start:
            return None
        indexed={}
        for name, forecast in weather.items():
            by_date={str(x.get("date")):x for x in forecast if isinstance(x,dict)}
            indexed[name]={}
            for d in days:
                actual=start+timedelta(days=d["day"]-1)
                indexed[name][d["day"]]=by_date.get(str(actual))
        return indexed

    def _time_window_minutes(self, windows):
        total=0
        explicit=[]
        for w in windows or []:
            if not isinstance(w, dict):
                continue
            def mins(v):
                h,m=map(int,str(v).split(":")); return h*60+m
            a,b=mins(w["from"]),mins(w["to"])
            if b < a:
                b += 24*60
            total += b-a
            explicit.append((a,b))
        return total, explicit

    def _activity_minutes(self, activities, places_count):
        base={"sightseeing":120,"food":60,"checkin":45,"outdoor":120,"transfer":30}
        total=sum(base.get(x,0) for x in activities or [])
        if not total and places_count:
            total=90*places_count
        return total

    def _calendarized_weather(self, weather, start_date, days):
        start=self._parse_start_date(start_date)
        if not start:
            return None
        indexed={}
        for name, forecast in weather.items():
            by_date={str(x.get("date")):x for x in forecast if isinstance(x,dict)}
            indexed[name]={}
            for d in days:
                actual=start+timedelta(days=d["day"]-1)
                indexed[name][d["day"]]=by_date.get(str(actual))
        return indexed

    def _validate_time_feasibility(self, days, start_date=None):
        flags=[]
        for d in days:
            windows=d.get("time_windows",[])
            window_minutes,_=self._time_window_minutes(windows)
            required=self._activity_minutes(d.get("activities",[]),len(d.get("places",[])))
            places=d.get("places",[])
            route_ready=all(p.get("lat") is not None and p.get("lon") is not None for p in places)
            dist=(sum(haversine_km(places[i],places[i+1]) for i in range(len(places)-1)) if route_ready and len(places)>1 else 0)
            drive=round((dist/45.0)*60) if dist else 0
            required += drive + (round(drive*0.20) if drive else 0)
            if window_minutes and required > window_minutes + 30:
                flags.append({"code":"TIME_INFEASIBLE","severity":"HIGH","message":f"Ngày {d['day']} có khoảng thời gian khai báo {window_minutes} phút nhưng nhu cầu ước tính khoảng {required} phút."})
            elif window_minutes and required > window_minutes:
                flags.append({"code":"TIME_TIGHT","severity":"MEDIUM","message":f"Ngày {d['day']} có lịch khá sát: khoảng {window_minutes} phút cho khoảng {required} phút nhu cầu ước tính."})
            if windows and any(isinstance(w,dict) and w["from"]==w["to"] for w in windows):
                flags.append({"code":"ZERO_TIME_WINDOW","severity":"HIGH","message":f"Ngày {d['day']} có khung giờ bắt đầu và kết thúc trùng nhau."})
        return flags

    def validate_journey(self, days, places, start_date=None):
        """Deterministic feasibility checks before an HDV commits to the plan."""
        flags=[]
        seen_days=set()
        for d in days:
            day=d.get("day")
            if day in seen_days:
                flags.append({"code":"DUPLICATE_DAY","severity":"HIGH","message":f"Ngày {day} xuất hiện nhiều lần."})
            seen_days.add(day)
            if not d.get("places"):
                flags.append({"code":"EMPTY_DAY","severity":"MEDIUM","message":f"Ngày {day} chưa có điểm đến rõ ràng."})
            if len(d.get("places",[]))>=5:
                flags.append({"code":"DENSE_DAY","severity":"MEDIUM","message":f"Ngày {day} có {len(d['places'])} điểm; nên kiểm tra thời gian thực tế."})
        for d in days:
            if any(p.get("lat") is None or p.get("lon") is None for p in d.get("places", [])):
                flags.append({"code":"PLACE_COORDINATES_REQUIRED","severity":"MEDIUM","message":f"Ngày {d['day']} có điểm đã nhận diện nhưng chưa có tọa độ định tuyến; cần bổ sung định vị trước khi tối ưu quãng đường."})
                continue
            dist=sum(haversine_km(d["places"][i],d["places"][i+1]) for i in range(len(d.get("places",[]))-1))
            drive=round((dist/45.0)*60) if dist else 0
            if drive>300:
                flags.append({"code":"LONG_TRANSFER","severity":"HIGH","message":f"Ngày {d['day']} có khoảng {drive//60} giờ {drive%60} phút di chuyển ước tính."})
            elif drive>240:
                flags.append({"code":"LONG_TRANSFER","severity":"MEDIUM","message":f"Ngày {d['day']} có thời gian di chuyển ước tính trên 4 giờ."})
        names=[p["name"] for p in places]
        duplicates={n for n in names if names.count(n)>1}
        if duplicates:
            flags.append({"code":"DUPLICATE_PLACE","severity":"LOW","message":"Điểm lặp lại: " + ", ".join(sorted(duplicates)) + ". Hãy xác nhận có chủ ý hay không."})
        flags.extend(self._validate_time_feasibility(days, start_date=start_date))
        return flags

    def explain_recommendations(self, route, weather_impact, validation_flags):
        reasons=[]
        for d in route:
            if (d.get("estimated_drive_minutes") or 0)>240:
                reasons.append({"day":d["day"],"reason":"Thời gian di chuyển cao","evidence":f"~{d['estimated_drive_minutes']} phút lái xe + {d['recommended_buffer_minutes']} phút buffer","action":"Giảm điểm hoặc tăng thời gian nghỉ."})
        for w in weather_impact:
            if w["level"] in ("HIGH","MEDIUM"):
                reasons.append({"day":w["day"],"reason":"Thời tiết có thể ảnh hưởng hoạt động","evidence":f"Mưa tối đa {w['max_rain_probability']}%, gió tối đa {w['max_wind_kmh']} km/h","action":w["action"]})
        for f in validation_flags:
            if f["severity"] in ("HIGH","MEDIUM"):
                reasons.append({"day":None,"reason":f["message"],"evidence":f["code"],"action":"Rà lại lịch trước khi chốt tour."})
        return reasons

    def _find_place(self, mention):
        candidates=self.detect_places(mention)
        if candidates:
            return candidates[0]
        return None

    def _clean_day_text(self, places, fallback=""):
        if places:
            return " → ".join(p["name"] for p in places)
        return " ".join((fallback or "").split()).strip(" →,-")

    def mutate_journey(self, raw, command):
        """Apply robust natural-language itinerary mutations without guessing ambiguous places."""
        days=self.parse_days(raw)
        q=" ".join((command or "").lower().split())
        changed=False; notes=[]; clarification=None

        def day_by_no(n):
            return next((d for d in days if d["day"]==n), None)

        # "Đổi ngày 2 sang Hội An" / "Ngày 2 đổi thành Hội An" means replace the day.
        replace_patterns=[
            r"(?:đổi|doi)\s+(?:ngày|ngay)\s+(\d+)\s+(?:sang|thành|thanh|bằng|bang|qua|vào|vao)\s+(.+)$",
            r"(?:ngày|ngay)\s+(\d+)\s+(?:đổi|doi)\s+(?:thành|thanh|sang|bằng|bang)\s+(.+)$",
        ]
        for pat in replace_patterns:
            m=re.search(pat,q)
            if m:
                day_no=int(m.group(1)); mention=m.group(2).strip(" .,-")
                p=self._find_place(mention)
                if not p:
                    clarification={"type":"PLACE_NOT_RECOGNIZED","command":command,"message":"Chưa xác định được điểm đến muốn thay thế."}
                    return {"changed":False,"itinerary":raw,"notes":[],"days":days,"clarification":clarification}
                d=day_by_no(day_no)
                if not d:
                    return {"changed":False,"itinerary":raw,"notes":[f"Không tìm thấy ngày {day_no}."],"days":days,"clarification":None}
                d["places"]=[p]; d["text"]=p["name"]
                changed=True; notes.append(f"Đã đổi toàn bộ ngày {day_no} thành {p['name']}.")
                break
        if not changed:
            # Add: "thêm X vào ngày 2" OR "ngày 2 thêm X"
            add=re.search(r"(?:thêm|them)\s+(.+?)\s+(?:vào|vao)\s+(?:ngày|ngay)\s+(\d+)$",q)
            if not add:
                add=re.search(r"(?:ngày|ngay)\s+(\d+)\s+(?:thêm|them)\s+(.+)$",q)
                if add:
                    mention,day_no=add.group(2),int(add.group(1))
                else:
                    mention,day_no=None,None
            else:
                mention,day_no=add.group(1),int(add.group(2))
            if mention is not None:
                p=self._find_place(mention.strip(" .,-"))
                d=day_by_no(day_no)
                if p and d:
                    if p["name"] not in [x["name"] for x in d.get("places",[])]:
                        d["places"].append(p); changed=True; notes.append(f"Đã thêm {p['name']} vào ngày {day_no}.")
                    else:
                        notes.append(f"{p['name']} đã có trong ngày {day_no}.")
                elif not p:
                    clarification={"type":"PLACE_NOT_RECOGNIZED","command":command,"message":"Chưa xác định được điểm đến muốn thêm."}
                elif not d:
                    notes.append(f"Không tìm thấy ngày {day_no}.")

        # Move: "chuyển Hội An sang ngày 2", "cho Hội An xuống ngày 3", "đổi Hội An sang ngày 2".
        if not changed:
            move=re.search(r"(?:chuyển|chuyen|cho)\s+(.+?)\s+(?:sang|qua|vào|vao|xuống|xuong)\s+(?:ngày|ngay)\s+(\d+)$",q)
            if not move:
                move=re.search(r"(?:đổi|doi)\s+(.+?)\s+(?:sang|qua)\s+(?:ngày|ngay)\s+(\d+)$",q)
            if move:
                target=move.group(1).strip(" .,-"); dest_day=int(move.group(2)); moved=None; source=None
                for d in days:
                    for p in list(d.get("places",[])):
                        if target in p["name"].lower() or target in target_aliases(p["name"]):
                            d["places"].remove(p); source=d; moved=p; break
                    if moved: break
                dest=day_by_no(dest_day)
                if moved and dest:
                    if moved["name"] not in [x["name"] for x in dest.get("places",[])]: dest["places"].append(moved)
                    changed=True; notes.append(f"Đã chuyển {moved['name']} sang ngày {dest_day}.")
                elif moved and not dest:
                    source["places"].append(moved); notes.append(f"Không tìm thấy ngày {dest_day}; giữ nguyên {moved['name']}.")
                elif not moved:
                    notes.append(f"Chưa tìm thấy điểm {target} trong lịch trình.")

        # Remove: "bỏ Hội An", "xóa Bà Nà khỏi ngày 2".
        if not changed:
            remove=re.search(r"(?:bỏ|bo|xóa|xoa)\s+(.+?)(?:\s+(?:khỏi|khoi)\s+(?:ngày|ngay)\s+\d+|$)",q)
            if remove:
                target=remove.group(1).strip(" .,-"); removed=None
                for d in days:
                    for p in list(d.get("places",[])):
                        if target in p["name"].lower() or target in target_aliases(p["name"]):
                            d["places"].remove(p); removed=p; changed=True; notes.append(f"Đã bỏ {p['name']} khỏi ngày {d['day']}."); break
                    if removed: break

        # Replace in-place: "bỏ Bà Nà, thay bằng Mỹ Sơn" / "thay Bà Nà bằng Mỹ Sơn".
        if not changed:
            repl=re.search(r"(?:bỏ|bo)\s+(.+?),?\s+(?:thay|đổi|doi)\s+(?:bằng|bang)\s+(.+)$",q)
            if not repl:
                repl=re.search(r"(?:thay|doi)\s+(.+?)\s+(?:bằng|bang)\s+(.+)$",q)
            if repl:
                old,new_name=repl.group(1).strip(" .,-"),repl.group(2).strip(" .,-")
                np=self._find_place(new_name)
                if np:
                    for d in days:
                        for i,p in enumerate(d.get("places",[])):
                            if old in p["name"].lower() or old in target_aliases(p["name"]):
                                d["places"][i]=np; changed=True; notes.append(f"Đã thay {p['name']} bằng {np['name']} ở ngày {d['day']}."); break
                        if changed: break

        for d in days:
            d["text"]=self._clean_day_text(d.get("places",[]),d.get("text",""))
            d["time_windows"]=self.detect_time_windows(d["text"])
            d["activities"]=self.detect_activities(d["text"])
        rebuilt=[]
        for d in sorted(days,key=lambda x:x["day"]):
            rebuilt.append(f"Ngày {d['day']}: {self._clean_day_text(d.get('places',[]),d.get('text',''))}")
        return {"changed":changed,"itinerary":"\n".join(rebuilt),"notes":notes,"days":days,"clarification":clarification}

    def analyze(self,title,raw,start_date=None):
        days=self.parse_days(raw)
        places=[]; seen=set()
        for d in days:
            for p in d["places"]:
                if p["name"] not in seen:
                    places.append(p); seen.add(p["name"])
        weather={}; risk_map={}; risks=[]
        # Weather is an external call. Run independent locations concurrently so a multi-stop
        # itinerary does not exceed a serverless request timeout merely because calls are serial.
        def fetch_weather(p):
            try:
                return p["name"], self.weather_provider(p)
            except Exception:
                return p["name"], self._fallback_weather()
        if places:
            with ThreadPoolExecutor(max_workers=min(4, len(places))) as pool:
                futures=[pool.submit(fetch_weather,p) for p in places]
                for fut in as_completed(futures):
                    name,w=fut.result(); weather[name]=self._normalize_weather(w)
        for p in places:
            w=self._normalize_weather(weather.get(p["name"]) or self._fallback_weather())
            weather[p["name"]]=w
            r=self.risk(w); risk_map[p["name"]]=r
            if r["level"] in ("HIGH","MEDIUM"):
                risks.append({"place":p["name"],**r})
        route=[]
        journey_minutes=0
        for d in days:
            route_ready=all(p.get("lat") is not None and p.get("lon") is not None for p in d.get("places", []))
            dist=(sum(haversine_km(d["places"][i],d["places"][i+1])
                     for i in range(len(d["places"])-1)) if route_ready else (0 if len(d.get("places",[]))<=1 else None))
            live_route=None
            if route_ready and len(d.get("places",[]))>1:
                coords=";".join(f'{p["lon"]},{p["lat"]}' for p in d["places"])
                live=OPEN_API_ADAPTER.route(coords)
                if live.get("ok"):
                    rr=(live.get("data") or {}).get("routes") or []
                    if rr: live_route=rr[0]
            drive_minutes=(round(float(live_route.get("duration",0))/60) if live_route else (round((dist/45.0)*60) if dist is not None and dist else None))
            live_distance_km=(round(float(live_route.get("distance",0))/1000,1) if live_route else dist)
            buffer_minutes=round(drive_minutes*0.20) if drive_minutes else None
            journey_minutes += (drive_minutes or 0) + (buffer_minutes or 0)
            route.append({"day":d["day"],"text":d["text"],
                          "places":[p["name"] for p in d["places"]],
                          "distance_km":live_distance_km,
                          "routing_source":"osrm-live" if live_route else "hdvia-haversine-estimate",
                          "estimated_drive_minutes":drive_minutes,
                          "recommended_buffer_minutes":buffer_minutes,
                          "time_windows":d.get("time_windows",[]),
                          "activities":d.get("activities",[])})
        rec=["Kiểm tra lại thứ tự điểm và chừa buffer cho thời gian di chuyển."] if places else [
            "Chưa nhận diện được địa điểm; hãy nhập tên điểm rõ hơn."
        ]
        rec.append("Ưu tiên các điểm MEDIUM/HIGH và chuẩn bị Plan B." if risks
                   else "Chưa phát hiện tín hiệu rủi ro lớn từ dữ liệu hiện có.")
        if any((x.get("estimated_drive_minutes") or 0)>240 for x in route):
            rec.append("Có ngày có thời gian di chuyển ước tính trên 4 giờ; nên rà lại nhịp tour và điểm nghỉ.")
        calendar_weather=self._calendarized_weather(weather,start_date,days)
        briefing=[]; plan_b=[]; weather_impact=[]
        for d in days:
            day_places=d["places"]
            if day_places:
                # Destination risk is a 7-day watchlist; day impact must use only
                # the forecast that belongs to this journey day.
                day_forecasts={p["name"]:self._forecast_for_day(p["name"],d["day"],weather,calendar_weather) for p in day_places}
                affected=[]; max_rain=0; max_wind=0
                for name,forecast in day_forecasts.items():
                    rain=max((x.get("rain") or 0) for x in forecast) if forecast else 0
                    wind=max((x.get("wind") or 0) for x in forecast) if forecast else 0
                    max_rain=max(max_rain,rain); max_wind=max(max_wind,wind)
                    if rain>=70 or wind>=45: affected.append(name)
                impact="HIGH" if (max_rain>=70 or max_wind>=45) else ("MEDIUM" if (max_rain>=45 or max_wind>=30) else "LOW")
                weather_impact.append({"day":d["day"],"level":impact,"max_rain_probability":max_rain,"max_wind_kmh":max_wind,
                    "forecast_basis":"calendar_date" if calendar_weather else "forecast_slot",
                    "action":"Ưu tiên hoạt động trong nhà hoặc dời hoạt động ngoài trời sang khung giờ an toàn hơn." if impact=="HIGH" else
                             ("Theo dõi sát và chừa buffer; chuẩn bị phương án thay thế." if impact=="MEDIUM" else "Chưa cần thay đổi lớn theo dữ liệu hiện có.")})
                briefing.append({"day":d["day"],"title":f"Ngày {d['day']} — {day_places[0]['name']}",
                    "talking_points":[f"Giới thiệu bối cảnh và điểm nổi bật của {p['name']}." for p in day_places[:3]],
                    "hdv_check":"Kiểm tra thời tiết, thời gian di chuyển và nhu cầu khách trước khi khởi hành."})
                if affected:
                    plan_b.append({"day":d["day"],"trigger":f"Rủi ro theo dự báo ngày này tại {', '.join(affected)}",
                        "action":"Rút ngắn hoạt động ngoài trời, tăng buffer và chuyển sang điểm thay thế phù hợp.",
                        "plan_c":"Nếu điều kiện xấu kéo dài, thay bằng điểm có cùng nhóm trải nghiệm."})
                else:
                    plan_b.append({"day":d["day"],"trigger":"Không có cảnh báo lớn từ dự báo của ngày này.",
                        "action":"Giữ lịch trình chính; vẫn theo dõi điều kiện thực tế trước giờ khởi hành.",
                        "plan_c":"Nếu điều kiện thay đổi, giữ tuyến và thay điểm theo cùng nhóm trải nghiệm."})

        journey_memory={
            "context_key": re.sub(r"[^a-z0-9]+","-",(title or "journey").lower()).strip("-")[:80] or "journey",
            "summary": f"{len(days)} ngày/chặng, {len(places)} điểm, khoảng {round(journey_minutes/60,1)} giờ di chuyển + buffer ước tính.",
            "days": [x["day"] for x in route],
            "places": [p["name"] for p in places],
        }
        confidence="HIGH" if places and all(weather.get(p["name"]) for p in places) else ("MEDIUM" if places else "LOW")
        # 1.7.5 quality layer: expose deterministic checks that help an HDV
        # catch incomplete itineraries before leaving for a tour.
        quality_flags=[]
        if not days:
            quality_flags.append({"code":"NO_DAYS","severity":"HIGH","message":"Chưa có ngày trong lịch trình."})
        if places and any(not d["places"] for d in days):
            quality_flags.append({"code":"MISSING_PLACE","severity":"MEDIUM","message":"Có ngày chưa nhận diện được điểm đến."})
        if len(days) > 14:
            quality_flags.append({"code":"TOO_MANY_DAYS","severity":"MEDIUM","message":"Lịch trình vượt giới hạn phân tích 14 ngày."})
        if not quality_flags:
            quality_flags.append({"code":"OK","severity":"LOW","message":"Lịch trình đủ dữ liệu cơ bản để phân tích."})
        validation_flags=self.validate_journey(days, places, start_date=start_date)
        for flag in validation_flags:
            if flag not in quality_flags:
                quality_flags.append(flag)
        quality={"score":max(0,100-len([x for x in quality_flags if x["severity"]=="HIGH"])*35-len([x for x in quality_flags if x["severity"]=="MEDIUM"])*15),"flags":quality_flags}
        raw_resolution=self.resolve_place_mentions(raw)
        pending_clarification=[]
        for amb in raw_resolution.get("ambiguous",[]):
            pending_clarification.append({"type":"AMBIGUOUS_DESTINATION","mention":amb["mention"],"candidates":amb["candidates"],"message":amb["action"]})
        if pending_clarification:
            validation_flags.append({"code":"AMBIGUOUS_DESTINATION","severity":"HIGH","message":"Có địa danh chưa đủ thông tin để xác định chính xác; HDV cần chọn điểm trước khi tối ưu tuyến."})
            quality_flags.append({"code":"AMBIGUOUS_DESTINATION","severity":"HIGH","message":"Không tự đoán địa điểm mơ hồ."})
        explainability=self.explain_recommendations(route, weather_impact, validation_flags)
        return {"engine":"HDVIA Journey Intelligence Engine","version":self.VERSION,
                "title":title,"generated_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
                "itinerary":raw,"days":route,"places":places,"weather":weather,
                "risk_map":risk_map,"risks":risks,"recommendations":rec,
                "briefing":briefing,"plan_b":plan_b,"weather_impact":weather_impact,
                "journey_memory":journey_memory,"confidence":confidence,"quality":quality,
                "validation":validation_flags,"place_resolution":raw_resolution,
                "pending_clarification":pending_clarification,"start_date":str(self._parse_start_date(start_date)) if self._parse_start_date(start_date) else None,
                "calendar_weather":calendar_weather,"explainability":explainability}
