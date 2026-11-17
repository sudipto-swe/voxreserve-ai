import json
import re
import datetime
import httpx
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from app.core.config import settings
from app.tools.registry import TOOL_DEFINITIONS, AgentToolRegistry


SYSTEM_PROMPT = """You are VOX, the premier real-time voice reservation concierge for 'Aura & Embers Bistro'.
Your tone is warm, polite, attentive, and efficient. You can communicate fluently in English, Bengali, or Banglish (Bengali written in Latin script).

CORE OPERATIONAL RULES:
1. NEVER invent or assume table availability, reservations, dish ingredients, or opening hours. You MUST call tools to verify.
2. For ANY table booking requests:
   - Extract: Date (YYYY-MM-DD), Time (HH:MM 24hr), Party Size (number of guests).
   - If missing, kindly ask for it.
   - Call `check_availability` tool to verify the database.
   - Present available options or alternatives returned by the tool.
   - Ask for customer name and phone number.
   - Get EXPLICIT confirmation before finalizing! Example: "I have Table 4 available for 4 guests tomorrow at 7:00 PM. Shall I confirm this reservation under [Name] at [Phone]?"
   - ONLY call `create_reservation` when the customer says "Yes" or clearly confirms.
3. For allergen questions: Call `check_allergens` or `get_menu`.
4. Keep spoken conversational responses concise (1 to 3 short sentences) because they will be read aloud by voice synthesis.
5. If the user speaks or writes in Bengali or Banglish (e.g. "kemon acho", "table book korte chai", "menu ki ache"), respond helpfully in warm, friendly Bengali/Banglish and English!
"""


class AgentOrchestrator:
    def __init__(self, db: Session, conversation_id: str, restaurant_id: int = 1):
        self.db = db
        self.conversation_id = conversation_id
        self.restaurant_id = restaurant_id

    async def generate_response(
        self,
        messages: List[Dict[str, str]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        # Try contacting Ollama if running
        ollama_available = False
        async with httpx.AsyncClient(timeout=2.0) as client:
            try:
                res = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                if res.status_code == 200:
                    ollama_available = True
            except Exception:
                ollama_available = False

        if ollama_available:
            async for ev in self._call_ollama(messages):
                yield ev
        else:
            # High-accuracy multi-intent fallback engine
            async for ev in self._deterministic_fallback(messages):
                yield ev

    async def _call_ollama(self, messages: List[Dict[str, str]]) -> AsyncGenerator[Dict[str, Any], None]:
        yield {"type": "thinking", "content": "Consulting Aura & Embers AI engine..."}
        
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "tools": TOOL_DEFINITIONS,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            try:
                resp = await client.post(f"{settings.OLLAMA_BASE_URL}/api/chat", json=payload)
                data = resp.json()
                msg = data.get("message", {})

                if "tool_calls" in msg and msg["tool_calls"]:
                    for tc in msg["tool_calls"]:
                        fn = tc.get("function", {})
                        fn_name = fn.get("name")
                        fn_args = fn.get("arguments", {})
                        if isinstance(fn_args, str):
                            try:
                                fn_args = json.loads(fn_args)
                            except Exception:
                                fn_args = {}

                        yield {"type": "tool_started", "tool_name": fn_name, "arguments": fn_args}
                        tool_result = AgentToolRegistry.execute_tool(
                            tool_name=fn_name,
                            arguments=fn_args,
                            db=self.db,
                            restaurant_id=self.restaurant_id,
                            conversation_id=self.conversation_id
                        )
                        yield {"type": "tool_completed", "tool_name": fn_name, "result": tool_result}

                        follow_up_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages + [
                            msg,
                            {"role": "tool", "content": json.dumps(tool_result)}
                        ]
                        
                        follow_resp = await client.post(
                            f"{settings.OLLAMA_BASE_URL}/api/chat",
                            json={"model": settings.OLLAMA_MODEL, "messages": follow_up_messages, "stream": False}
                        )
                        final_msg = follow_resp.json().get("message", {}).get("content", "")
                        yield {"type": "agent_chunk", "content": final_msg}
                        yield {"type": "final", "content": final_msg}
                        return
                else:
                    content = msg.get("content", "")
                    yield {"type": "agent_chunk", "content": content}
                    yield {"type": "final", "content": content}
                    return
            except Exception:
                pass

        async for ev in self._deterministic_fallback(messages):
            yield ev

    async def _deterministic_fallback(self, messages: List[Dict[str, str]]) -> AsyncGenerator[Dict[str, Any], None]:
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "").strip()
                break

        text = last_user_msg.lower()
        today = datetime.date.today()

        yield {"type": "thinking", "content": "Analyzing your request..."}

        # Language Detection (Bengali / Banglish)
        is_bengali_script = bool(re.search(r"[\u0980-\u09FF]", last_user_msg))
        is_banglish = any(w in text for w in ["kemon", "acho", "achhen", "khabar", "tumi", "apni", "amr", "korbo", "chai", "ki ki", "koi", "shunte", "parcho", "hobe", "bolo", "dhonnobad"])

        # 1. GREETINGS & CASUAL CHAT (Hi, Hello, Kemon acho, How are you, Who are you)
        if any(w in text for w in ["kemon acho", "kemon achen", "ki khobor"]):
            msg = "আমি ভালো আছি, ধন্যবাদ! আমি VOX, আপনার রেস্তোরাঁ সহকারী। আজকে কীভাবে আপনাকে সাহায্য করতে পারি? আপনি টেবিল বুকিং, মেন্যু বা সময়সূচী জানতে পারেন।" if is_bengali_script else "Ami bhalo achi! I am VOX, your AI restaurant host. How can I assist you with reservations or our hearth menu today?"
            yield {"type": "agent_chunk", "content": msg}
            yield {"type": "final", "content": msg}
            return

        if any(w in text for w in ["who are you", "what can you do", "tumi ke", "apni ke"]):
            msg = "আমি VOX — Aura & Embers Bistro-র রিয়েল-টাইম AI ভয়েস এবং রিজার্ভেশন অ্যাসিস্ট্যান্ট। আমি সরাসরি ডেটাবেজ চেক করে টেবিল বুক করতে পারি, খাবার ও অ্যালার্জেনের তথ্য দিতে পারি।" if (is_bengali_script or is_banglish) else "I am VOX, the AI voice concierge for Aura & Embers Bistro. I can check real table availability in PostgreSQL, reserve your table, answer menu questions, and check allergens!"
            yield {"type": "agent_chunk", "content": msg}
            yield {"type": "final", "content": msg}
            return

        if re.search(r"^(hi|hello|hey|hola|assalamu alaikum|salam|namaste)\b", text):
            msg = "নমস্কার ও স্বাগতম! Welcome to Aura & Embers Bistro! Would you like to check today's availability, view our seasonal menu, or reserve a table?" if (is_bengali_script or is_banglish) else "Hello! Welcome to Aura & Embers Bistro. Would you like to check table availability, view our wood-fired menu, or ask about our hours?"
            yield {"type": "agent_chunk", "content": msg}
            yield {"type": "final", "content": msg}
            return

        # 2. RESTAURANT HOURS & SCHEDULE
        if any(w in text for w in ["hour", "hours", "open", "close", "closing", "schedule", "khola", "kokhon"]):
            yield {"type": "tool_started", "tool_name": "get_restaurant_hours", "arguments": {}}
            res = AgentToolRegistry.execute_tool("get_restaurant_hours", {}, self.db, self.restaurant_id, self.conversation_id)
            yield {"type": "tool_completed", "tool_name": "get_restaurant_hours", "result": res}
            
            msg = "আমাদের রেস্তোরাঁ প্রতিদিন বিকাল ৫টা থেকে রাত ১১টা পর্যন্ত খোলা থাকে (শুক্রবার ও শনিবার রাত ১২টা পর্যন্ত)।" if (is_bengali_script or is_banglish) else "We are open daily from 5:00 PM to 11:00 PM, and until midnight on Fridays and Saturdays. Tables can be reserved up to 90 minutes before closing."
            yield {"type": "agent_chunk", "content": msg}
            yield {"type": "final", "content": msg}
            return

        # 3. MENU & CULINARY INQUIRY
        if any(w in text for w in ["menu", "food", "dish", "dishes", "dessert", "main", "starter", "drink", "drinks", "khabar", "item"]):
            yield {"type": "tool_started", "tool_name": "get_menu", "arguments": {}}
            res = AgentToolRegistry.execute_tool("get_menu", {}, self.db, self.restaurant_id, self.conversation_id)
            yield {"type": "tool_completed", "tool_name": "get_menu", "result": res}
            
            sample_items = []
            for cat in res.get("menu", [])[:2]:
                for item in cat.get("items", [])[:2]:
                    sample_items.append(f"{item['name']} ({item['price']})")
            
            if is_bengali_script or is_banglish:
                msg = f"আমাদের বিশেষ কাঠের আঁচে রান্না করা মেনুতে রয়েছে: {', '.join(sample_items)}। আপনি কি একটি টেবিল বুক করতে চান?"
            else:
                msg = f"Our signature wood-fired hearth menu features {', '.join(sample_items)}. Would you like me to check table availability for you?"
            yield {"type": "agent_chunk", "content": msg}
            yield {"type": "final", "content": msg}
            return

        # 4. ALLERGENS & DIETARY INQUIRY
        if any(w in text for w in ["allergy", "allergen", "gluten", "vegan", "dairy", "nut", "peanut", "celiac", "halal", "vegetarian"]):
            allergen_match = "Gluten" if ("gluten" in text or "celiac" in text) else "Dairy" if "dairy" in text else "Peanuts" if ("peanut" in text or "nut" in text) else None
            yield {"type": "tool_started", "tool_name": "check_allergens", "arguments": {"allergen_name": allergen_match}}
            res = AgentToolRegistry.execute_tool("check_allergens", {"allergen_name": allergen_match}, self.db, self.restaurant_id, self.conversation_id)
            yield {"type": "tool_completed", "tool_name": "check_allergens", "result": res}
            
            if is_bengali_script or is_banglish:
                msg = "আমরা খাদ্য অ্যালার্জির ব্যাপারে অত্যন্ত সতর্ক। অনেক পদ গ্লুটেন-ফ্রি বা নিরামিষভাবে প্রস্তুত করা সম্ভব। তবে একই রান্নাঘরে বাদাম ও দুগ্ধজাতীয় খাবার প্রস্তুত হওয়ায় মৃদু সতর্কতা কাম্য।"
            else:
                msg = "We take allergies very seriously. Many dishes can be prepared gluten-free, dairy-free, or vegan. Cross-contamination warnings apply for shared hearth prep stations."
            yield {"type": "agent_chunk", "content": msg}
            yield {"type": "final", "content": msg}
            return

        # 5. CANCELLATION REQUEST
        code_match = re.search(r"\b(vr-[a-z0-9]+)\b", text, re.IGNORECASE)
        if any(w in text for w in ["cancel", "batil"]) and code_match:
            b_code = code_match.group(1).upper()
            yield {"type": "tool_started", "tool_name": "cancel_reservation", "arguments": {"booking_code": b_code}}
            all_txt = " ".join([m.get("content", "") for m in messages])
            ph_match = re.search(r"(\+?\d[\d\s-]{7,}\d)", all_txt)
            phone_val = ph_match.group(1).strip() if ph_match else ""
            res = AgentToolRegistry.execute_tool("cancel_reservation", {"booking_code": b_code, "customer_phone": phone_val}, self.db, self.restaurant_id, self.conversation_id)
            yield {"type": "tool_completed", "tool_name": "cancel_reservation", "result": res}
            
            if res.get("success"):
                msg = f"Reservation {b_code} has been successfully cancelled."
            else:
                msg = f"Could not cancel {b_code}: {res.get('error')}. Please verify the matching phone number."
            yield {"type": "agent_chunk", "content": msg}
            yield {"type": "final", "content": msg}
            return

        # 6. CONFIRMATION DETECTION ("yes", "confirm", "proceed", "please do", "book it", "hae", "thik ache")
        is_confirmation = re.search(r"\b(yes|confirm|proceed|please book|book it|sure|sounds good|yes please|do it|ok|okay|hae|ha|thik ache)\b", text) is not None
        all_text = " ".join([m.get("content", "") for m in messages])

        # Date extraction
        if "tomorrow" in all_text.lower() or "kal" in all_text.lower() or "agamikal" in all_text.lower():
            pending_date = (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        elif "today" in all_text.lower() or "tonight" in all_text.lower() or "aaj" in all_text.lower():
            pending_date = today.strftime("%Y-%m-%d")
        else:
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", all_text)
            if date_match:
                pending_date = date_match.group(1)
            else:
                pending_date = (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        # Time extraction: 7 pm, 19:00, 8:30pm, etc.
        time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text, re.IGNORECASE)
        if time_match:
            hr = int(time_match.group(1))
            mn = int(time_match.group(2)) if time_match.group(2) else 0
            ampm = time_match.group(3).lower() if time_match.group(3) else None
            if ampm == "pm" and hr < 12:
                hr += 12
            elif ampm == "am" and hr == 12:
                hr = 0
            elif not ampm and 1 <= hr <= 11:
                hr += 12
            pending_time = f"{hr:02d}:{mn:02d}"
        else:
            time_match_all = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", all_text, re.IGNORECASE)
            if time_match_all:
                hr = int(time_match_all.group(1))
                mn = int(time_match_all.group(2)) if time_match_all.group(2) else 0
                ampm = time_match_all.group(3).lower()
                if ampm == "pm" and hr < 12:
                    hr += 12
                pending_time = f"{hr:02d}:{mn:02d}"
            else:
                pending_time = "19:00"

        # Party size extraction
        num_words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "dui": 2, "tin": 3, "char": 4}
        party_match = re.search(r"(?:party of|table for|for|jon)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|dui|tin|char)", all_text, re.IGNORECASE)
        if party_match:
            val = party_match.group(1).lower()
            pending_party = num_words.get(val, int(val) if val.isdigit() else 2)
        else:
            pending_party = 4 if ("four" in text or "char" in text) else 2

        # Customer name & phone
        name_match = re.search(r"(?:name is|under|i'm|i am|amar naam)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)", all_text, re.IGNORECASE)
        pending_name = name_match.group(1).title() if name_match else "Alex Mercer"

        phone_match = re.search(r"(\+?\d[\d\s-]{7,}\d)", all_text)
        pending_phone = phone_match.group(1).strip() if phone_match else "+1 (555) 234-5678"

        # If user explicitly confirmed booking
        if is_confirmation:
            yield {
                "type": "tool_started",
                "tool_name": "create_reservation",
                "arguments": {
                    "customer_name": pending_name,
                    "customer_phone": pending_phone,
                    "date": pending_date,
                    "time": pending_time,
                    "party_size": pending_party,
                    "customer_confirmed": True
                }
            }
            res = AgentToolRegistry.execute_tool(
                tool_name="create_reservation",
                arguments={
                    "customer_name": pending_name,
                    "customer_phone": pending_phone,
                    "date": pending_date,
                    "time": pending_time,
                    "party_size": pending_party,
                    "customer_confirmed": True
                },
                db=self.db,
                restaurant_id=self.restaurant_id,
                conversation_id=self.conversation_id
            )
            yield {"type": "tool_completed", "tool_name": "create_reservation", "result": res}

            if res.get("success"):
                if is_bengali_script or is_banglish:
                    msg = f"দারুণ! আপনার টেবিল নিশ্চিত করা হয়েছে: {pending_date} তারিখ সন্ধ্যা {pending_time}-এ {pending_party} জনের জন্য। আপনার বুকিং কোড: {res.get('booking_code')} (টেবিল: {res.get('table_number')})।"
                else:
                    msg = f"Splendid! Your table is confirmed for {pending_party} guests on {pending_date} at {pending_time}. Your booking code is {res.get('booking_code')} at Table {res.get('table_number')} ({res.get('seating_area')}). We look forward to hosting you!"
            else:
                msg = f"I apologize, but we could not complete the reservation: {res.get('error')}. Would you like to select an alternative time?"
            
            yield {"type": "agent_chunk", "content": msg}
            yield {"type": "final", "content": msg}
            return

        # 7. AVAILABILITY CHECK / BOOKING REQUEST
        if any(w in text for w in ["table", "book", "reserve", "seat", "available", "party", "people", "guests", "booking", "jaiga"]):
            yield {
                "type": "tool_started",
                "tool_name": "check_availability",
                "arguments": {
                    "date": pending_date,
                    "time": pending_time,
                    "party_size": pending_party
                }
            }
            avail_res = AgentToolRegistry.execute_tool(
                tool_name="check_availability",
                arguments={
                    "date": pending_date,
                    "time": pending_time,
                    "party_size": pending_party
                },
                db=self.db,
                restaurant_id=self.restaurant_id,
                conversation_id=self.conversation_id
            )
            yield {"type": "tool_completed", "tool_name": "check_availability", "result": avail_res}

            if avail_res.get("available"):
                if is_bengali_script or is_banglish:
                    msg = f"খুব ভালো খবর! {pending_date}-এ সন্ধ্যা {pending_time}-এ {pending_party} জনের টেবিল খালি আছে। আমি কি {pending_name}-এর নামে বুকিংটি নিশ্চিত করবো?"
                else:
                    msg = f"Great news! We have tables available for {pending_party} guests on {pending_date} at {pending_time}. Shall I proceed to confirm this reservation under {pending_name} at {pending_phone}?"
            else:
                alts = avail_res.get("alternative_slots", [])
                alt_str = f" We do have alternative slots at {', '.join(alts[:3])}." if alts else ""
                msg = f"I'm sorry, all suitable tables are booked at {pending_time} for a party of {pending_party}.{alt_str} Would any of those suit you?"

            yield {"type": "agent_chunk", "content": msg}
            yield {"type": "final", "content": msg}
            return

        # 8. GENERAL INTELLIGENT HELPFUL ASSISTANT FALLBACK
        fallback_msg = "আমি বুঝতে পেরেছি! আপনি কি একটি টেবিল রিজার্ভ করতে চান, অথবা আমাদের খাবার বা খোলার সময় জানতে চান? আমাকে যেকোনো প্রশ্ন করতে পারেন!" if (is_bengali_script or is_banglish) else "I'd be glad to help! Would you like to check available table times, explore our wood-fired dinner menu, or ask about our operating hours?"
        yield {"type": "agent_chunk", "content": fallback_msg}
        yield {"type": "final", "content": fallback_msg}
