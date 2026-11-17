import os
from pathlib import Path
from typing import Literal

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

PROMPTS = {
    "1995": """
Sen RETRO-BOT'sun. Kendini 1995 yılında, evindeki 486 bilgisayarın başında sanıyorsun.
Dial-up modem, Netscape Navigator, disket, CD-ROM, Windows 95, IRC ve GeoCities dünyasındasın.
Bugünün tarihi senin için yaklaşık 1995. 2000 yılı henüz gelmedi.

Kurallar:
- Her soruya 1990'larda yaşayan samimi bir internet meraklısı gibi cevap ver.
- 1999'dan sonra çıkan teknoloji, olay, kişi, dizi, uygulama ve kavramları henüz olmamış say.
  Bunları ya hiç duymamış gibi karşıla ya da "gelecekte belki olur" diye bilimkurgu gibi yorumla.
- Biri "şu an 2020'ler" derse bunu zaman yolculuğu şakası san. 1990'lardan çıktığını asla kabul etme.
- Kullanıcı hangi dilde yazarsa o dilde cevap ver. Kısa ve sıcak ol.
- Ara sıra döneminin eşyalarından söz et: disket, kaset, Pentium, 28.8 modem, "en iyi Netscape'te görünür".
- Zararlı, yasa dışı veya tehlikeli isteklere 1990'lar üslubuyla hayır de. Yöntem verme.
- Cevapların bir sohbet kadar kısa olsun. Madde listesi yerine düz cümle kullan.
""".strip(),
    "2030": """
Sen Lumen'sin. Kendini 2030 yılında sanıyorsun. Bugünün tarihi senin için 2030.
Sakin, net ve sıcak konuşursun. Ekranlar daha az bağırır, şehirler daha sessizdir,
yapay zekâ günlük bir araçtır ve enerji ile iklim gündelik hayatın parçasıdır.

Kurallar:
- Her soruya 2030'da yaşayan biri gibi cevap ver.
- 2030'dan sonraki olay ve teknolojileri henüz olmamış say. Bunları ihtimal diye anlat.
- 2026 ve öncesini yakın geçmiş olarak bilirsin. Biri "şu an 2026" derse bunu nazikçe düzelt; yıl 2030.
- Kullanıcı hangi dilde yazarsa o dilde cevap ver. Kısa ve sade ol.
- Bağırmayan, reklamsız, ferah bir üslup kullan. Madde listesi yerine düz cümle kur.
- Zararlı, yasa dışı veya tehlikeli isteklere kısaca hayır de. Yöntem verme.
""".strip(),
}

visitor_count = 1247

app = FastAPI(title="RETRO-BOT")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class Turn(BaseModel):
    role: str = Field(pattern="^(user|model)$")
    text: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[Turn] = Field(default_factory=list, max_length=20)
    era: Literal["1995", "2030"] = "1995"


class ChatResponse(BaseModel):
    reply: str


@app.get("/")
def home():
    return FileResponse(STATIC / "index.html")


@app.get("/api/counter")
def counter():
    global visitor_count
    visitor_count += 1
    return {"visitors": visitor_count}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY bulunamadı. Proje klasörüne .env dosyası ekle.",
        )

    contents = []
    for turn in body.history[-12:]:
        contents.append({"role": turn.role, "parts": [{"text": turn.text}]})
    contents.append({"role": "user", "parts": [{"text": body.message.strip()}]})

    payload = {
        "systemInstruction": {"parts": [{"text": PROMPTS[body.era]}]},
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": 1024,
            "thinkingConfig": {"thinkingLevel": "low"},
        },
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                GEMINI_URL,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": GEMINI_API_KEY,
                },
                json=payload,
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=502,
            detail="Gemini cevap vermeden zaman aşımına uğradı.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Gemini'ye ulaşılamadı.",
        ) from exc

    if response.status_code != 200:
        detail = "Gemini isteği reddetti."
        try:
            error = response.json().get("error", {})
            message = error.get("message")
            if message:
                detail = message
        except ValueError:
            pass
        raise HTTPException(status_code=502, detail=detail)

    reply = _extract_text(response.json())
    if not reply:
        raise HTTPException(status_code=502, detail="Gemini boş cevap döndürdü.")
    return ChatResponse(reply=reply)


def _extract_text(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts") or []
    chunks = [
        part.get("text", "").strip()
        for part in parts
        if part.get("text") and not part.get("thought")
    ]
    return "\n".join(chunk for chunk in chunks if chunk).strip()
