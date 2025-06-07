import requests
import os
from datetime import datetime

API_KEY = os.getenv("API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {"x-rapidapi-host": "free-api-live-football-data.p.rapidapi.com",
           'x-apisports-key': API_KEY}
BASE_URL = 'https://free-api-live-football-data.p.rapidapi.com/football-current-live'
tracked_matches = {}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg}
    requests.post(url, data=data)

def get_live_matches():
    url = "https://free-api-live-football-data.p.rapidapi.com/football-current-live"
    headers = {
        "x-rapidapi-host": "free-api-live-football-data.p.rapidapi.com",
        "x-rapidapi-key": API_KEY
    }
    res = requests.get(url, headers=headers)
    data = res.json()

    if data.get("status") != "success":
        raise Exception("API response error")

    return data["response"]["live"]

def process_match(match):
    match_id = match["id"]
    match_name = f"{match['home']['name']} vs {match['away']['name']}"
    league_info = f"League ID: {match['leagueId']}"
    score_home = match['home']['score']
    score_away = match['away']['score']
    score = f"{score_home}-{score_away}"

    # Minute from "status.liveTime.short" e.g., "62’" => 62
    try:
        minute_str = match['status']['liveTime']['short']
        minute = int(minute_str.replace("’", "").strip())
    except:
        minute = None

    if match_id not in tracked_matches:
        tracked_matches[match_id] = {
            '36_bet_placed': False,
            '36_result_checked': False,
            '80_bet_placed': False,
            '80_result_checked': False,
            'match_name': match_name
        }

    state = tracked_matches[match_id]

    if minute == 36 and not state['36_bet_placed']:
        state['score_36'] = score
        state['36_bet_placed'] = True
        send_telegram(f"⏱️ 36' - {match_name}\n🏆 {league_info}\n🔢 Score: {score}\n🎯 First Bet Placed")

    if minute and minute > 45 and not state['36_result_checked']:
        if score == state.get('score_36'):
            send_telegram(f"✅ HT Result: {match_name}\n🏆 {league_info}\n🔢 Score: {score}\n🎉 36’ Bet WON")
            state['skip_80'] = True
        else:
            send_telegram(f"❌ HT Result: {match_name}\n🏆 {league_info}\n🔢 Score: {score}\n🔁 36’ Bet LOST — chasing at 80’")
        state['36_result_checked'] = True

    if minute == 80 and not state.get('skip_80', False) and not state['80_bet_placed']:
        state['score_80'] = score
        state['80_bet_placed'] = True
        send_telegram(f"⏱️ 80' - {match_name}\n🏆 {league_info}\n🔢 Score: {score}\n🎯 Chase Bet Placed")

    if match['status']['finished'] and state['80_bet_placed'] and not state['80_result_checked']:
        if score == state.get('score_80'):
            send_telegram(f"✅ FT Result: {match_name}\n🏆 {league_info}\n🔢 Score: {score}\n🎉 Chase Bet WON")
        else:
            send_telegram(f"❌ FT Result: {match_name}\n🏆 {league_info}\n🔢 Score: {score}\n📉 Chase Bet LOST")
        state['80_result_checked'] = True

def run_bot_once():
    try:
        print(f"[{datetime.now()}] Checking live matches...")
        live_matches = get_live_matches()

        from web import bot_status  # safe to import here, not at top
        bot_status['last_check'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bot_status['active_matches'] = [
            f"{m['home']['name']} vs {m['away']['name']} ({m['status']['liveTime']['short']})" 
            for m in live_matches
        ]

        for match in live_matches:
            process_match(match)

    except Exception as e:
        print(f"❌ Error: {e}")
