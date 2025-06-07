import requests
import os
from datetime import datetime

API_KEY = os.getenv("API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {'x-apisports-key': API_KEY}
BASE_URL = 'https://v3.football.api-sports.io'
tracked_matches = {}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg}
    requests.post(url, data=data)

def get_live_matches():
    url = f"{BASE_URL}/fixtures?live=all"
    res = requests.get(url, headers=HEADERS)
    return res.json()['response']

def process_match(match):
    fixture_id = match['fixture']['id']
    match_name = f"{match['teams']['home']['name']} vs {match['teams']['away']['name']}"
    score = match['goals']
    minute = match['fixture']['status']['elapsed']
    status = match['fixture']['status']['short']

    if fixture_id not in tracked_matches:
        tracked_matches[fixture_id] = {
            '36_bet_placed': False,
            '36_result_checked': False,
            '80_bet_placed': False,
            '80_result_checked': False,
            'match_name': match_name
        }

    state = tracked_matches[fixture_id]

    if minute == 36 and not state['36_bet_placed']:
        score_36 = f"{score['home']}-{score['away']}"
        state['score_36'] = score_36
        state['36_bet_placed'] = True
        send_telegram(f"⏱️ 36' - {match_name} | Score: {score_36} | First Bet Placed")

    if status == 'HT' and state['36_bet_placed'] and not state['36_result_checked']:
        current_score = f"{score['home']}-{score['away']}"
        if current_score == state['score_36']:
            send_telegram(f"✅ HT Result: {match_name} | Score: {current_score} | 36’ Bet WON")
            state['skip_80'] = True
        else:
            send_telegram(f"❌ HT Result: {match_name} | Score: {current_score} | 36’ Bet LOST — will chase at 80’")
        state['36_result_checked'] = True

    if minute == 80 and state['36_result_checked'] and not state.get('skip_80', False) and not state['80_bet_placed']:
        score_80 = f"{score['home']}-{score['away']}"
        state['score_80'] = score_80
        state['80_bet_placed'] = True
        send_telegram(f"⏱️ 80' - {match_name} | Score: {score_80} | Chase Bet Placed")

    if status == 'FT' and state['80_bet_placed'] and not state['80_result_checked']:
        final_score = f"{score['home']}-{score['away']}"
        if final_score == state['score_80']:
            send_telegram(f"✅ FT Result: {match_name} | Score: {final_score} | Chase Bet WON")
        else:
            send_telegram(f"❌ FT Result: {match_name} | Score: {final_score} | Chase Bet LOST")
        state['80_result_checked'] = True

def run_bot_once():
    try:
        print(f"[{datetime.now()}] Checking live matches...")
        live_matches = get_live_matches()

        from web import bot_status  # safe to import here, not at top
        bot_status['last_check'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bot_status['active_matches'] = [
            f"{m['teams']['home']['name']} vs {m['teams']['away']['name']} ({m['fixture']['status']['elapsed']}')" 
            for m in live_matches
        ]

        for match in live_matches:
            process_match(match)

    except Exception as e:
        print(f"❌ Error: {e}")
