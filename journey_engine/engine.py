
import math, re, json, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

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

class JourneyIntelligenceEngine:
    VERSION="1.5.0"

    def __init__(self, weather_provider=None, geocoder=None):
        self.weather_provider=weather_provider or self._open_meteo
        self.geocoder=geocoder or self._nominatim

    def parse_days(self, raw):
        lines=[x.strip(" -•\t") for x in (raw or "").splitlines() if x.strip()]
        pat=re.compile(r"^(?:ngày|day)\s*(\d+)\s*[:\-]?\s*(.*)$",re.I)
        days=[]; current=None
        for line in lines:
            m=pat.match(line)
            if m:
                current={"day":int(m.group(1)),"text":m.group(2).strip()}
                days.append(current)
            elif current:
                current["text"]+=" "+line
        if not days:
            parts=[p.strip() for p in re.split(r"\n+|[;|]+",(raw or "")) if p.strip()]
            days=[{"day":i+1,"text":p} for i,p in enumerate(parts[:14])]
        for d in days:
            d["places"]=self.detect_places(d["text"])
        return days

    def detect_places(self,text):
        found=[]; seen=set(); low=(text or "").lower()
        for key,(name,lat,lon) in PLACE_CACHE.items():
            if key in low and name not in seen:
                found.append({"name":name,"lat":lat,"lon":lon,"source":"hdvia-cache"})
                seen.add(name)
        if not found:
            for part in re.split(r"\s*(?:→|->|>|,)\s*",text or ""):
                part=" ".join(part.split())
                if 2<=len(part)<=45:
                    p=self.geocoder(part)
                    if p: found.append(p); break
        return found

    def _nominatim(self,name):
        try:
            q=urllib.parse.urlencode({"q":name+", Vietnam","format":"jsonv2","limit":1})
            req=urllib.request.Request(
                "https://nominatim.openstreetmap.org/search?"+q,
                headers={"User-Agent":"HDVIA/1.5 Journey Intelligence"})
            with urllib.request.urlopen(req,timeout=6) as r:
                data=json.loads(r.read().decode("utf-8"))
            if data:
                return {"name":name,"lat":float(data[0]["lat"]),
                        "lon":float(data[0]["lon"]),"source":"nominatim"}
        except Exception:
            return None

    def _open_meteo(self,p):
        params=urllib.parse.urlencode({
            "latitude":p["lat"],"longitude":p["lon"],
            "daily":"weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,windspeed_10m_max",
            "timezone":"Asia/Ho_Chi_Minh","forecast_days":7
        })
        try:
            req=urllib.request.Request("https://api.open-meteo.com/v1/forecast?"+params,
                                       headers={"User-Agent":"HDVIA/1.5"})
            with urllib.request.urlopen(req,timeout=8) as r:
                d=json.loads(r.read().decode("utf-8"))["daily"]
            return [{
                "date":d["time"][i],"condition":WEATHER_CODES.get(d["weather_code"][i],"Biến động"),
                "code":d["weather_code"][i],"tmin":d["temperature_2m_min"][i],
                "tmax":d["temperature_2m_max"][i],"rain":d["precipitation_probability_max"][i],
                "wind":d["windspeed_10m_max"][i]
            } for i in range(len(d["time"]))]
        except Exception:
            today=datetime.now().date()
            return [{"date":str(today+timedelta(days=i)),"condition":"Chưa có dữ liệu",
                     "code":-1,"tmin":None,"tmax":None,"rain":None,"wind":None} for i in range(7)]

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

    def analyze(self,title,raw):
        days=self.parse_days(raw)
        places=[]; seen=set()
        for d in days:
            for p in d["places"]:
                if p["name"] not in seen:
                    places.append(p); seen.add(p["name"])
        weather={}; risk_map={}; risks=[]
        for p in places:
            w=self.weather_provider(p); weather[p["name"]]=w
            r=self.risk(w); risk_map[p["name"]]=r
            if r["level"] in ("HIGH","MEDIUM"):
                risks.append({"place":p["name"],**r})
        route=[]
        for d in days:
            dist=sum(haversine_km(d["places"][i],d["places"][i+1])
                     for i in range(len(d["places"])-1))
            route.append({"day":d["day"],"text":d["text"],
                          "places":[p["name"] for p in d["places"]],
                          "distance_km":round(dist,1)})
        rec=["Kiểm tra lại thứ tự điểm và chừa buffer cho thời gian di chuyển."] if places else [
            "Chưa nhận diện được địa điểm; hãy nhập tên điểm rõ hơn."
        ]
        rec.append("Ưu tiên các điểm MEDIUM/HIGH và chuẩn bị Plan B." if risks
                   else "Chưa phát hiện tín hiệu rủi ro lớn từ dữ liệu hiện có.")
        return {"engine":"HDVIA Journey Intelligence Engine","version":self.VERSION,
                "title":title,"generated_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
                "days":route,"places":places,"weather":weather,
                "risk_map":risk_map,"risks":risks,"recommendations":rec}
