# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "curl-cffi",
#     "seleniumbase",
# ]
# ///

import os
import sys
import json
import time
import urllib.parse
import argparse
from seleniumbase import SB
from curl_cffi import requests as curl_requests

# Cache storage tracking engines
SESSION_CACHE_FILE = os.path.abspath("./tesla_session_cache.json")
VEHICLE_CACHE_FILE = os.path.abspath("./tesla_vehicle_inventory_cache.json")
TG_OFFSET_FILE = os.path.abspath("./tg_offset.txt")

# ==============================================================================
# NOTIFICATION IMPLEMENTATION CONFIGURATION
# ==============================================================================
ENABLE_EMAIL = False
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"
RECEIVER_EMAIL = "alerts@gmail.com"

# ==============================================================================
# ROUTING & TELEGRAM BOT UTILITY CONTROLLERS
# ==============================================================================
def dispatch_telegram_message(token, chat_id, text, reply_markup=None):
    """Transmits specific formatting updates out to a remote Telegram window."""
    if not token or not chat_id:
        return
    try:
        tg_url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            payload["reply_markup"] = reply_markup

        curl_requests.post(tg_url, json=payload, impersonate="chrome")
        print(" -> Telegram update completed successfully.")
    except Exception as e:
        print(f" -> Failed to transmit Telegram message frame: {e}")

def process_telegram_updates(token):
    """Polls Telegram updates to respond to /status and handles Acknowledge button clicks."""
    if not token:
        return

    offset = 0
    if os.path.exists(TG_OFFSET_FILE):
        try:
            with open(TG_OFFSET_FILE, "r") as f:
                offset = int(f.read().strip())
        except Exception:
            offset = 0

    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}&timeout=2"
        res = curl_requests.get(url, impersonate="chrome").json()

        for update in res.get("result", []):
            offset = update["update_id"] + 1
            with open(TG_OFFSET_FILE, "w") as f:
                f.write(str(offset))

            # ------------------------------------------------------------------
            # 1. HANDLE BUTTON CLICK (CALLBACK QUERY)
            # ------------------------------------------------------------------
            if "callback_query" in update:
                cb = update["callback_query"]
                data = cb.get("data", "")
                cb_id = cb.get("id")
                msg = cb.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                msg_id = msg.get("message_id")

                if data.startswith("ack_"):
                    raw_vin = data.split("ack_")[1]

                    # Read Cache
                    cache = load_json_file(VEHICLE_CACHE_FILE) or {}

                    # Mark raw_vin as acknowledged across active search zones
                    acknowledged = False
                    for search_key in cache:
                        if raw_vin in cache[search_key]:
                            cache[search_key][raw_vin]["acknowledged"] = True
                            acknowledged = True

                    if acknowledged:
                        save_json_file(VEHICLE_CACHE_FILE, cache)

                        # Answer Callback Alert Popup
                        curl_requests.post(f"https://api.telegram.org/bot{token}/answerCallbackQuery", json={
                            "callback_query_id": cb_id,
                            "text": f"Vehicle {raw_vin} Muted!",
                            "show_alert": False
                        })

                        # Edit Telegram Message to remove button and display status
                        updated_text = msg.get("text", "") + "\n\n✅ <i>Acknowledged & Alerts Muted</i>"
                        curl_requests.post(f"https://api.telegram.org/bot{token}/editMessageText", json={
                            "chat_id": chat_id,
                            "message_id": msg_id,
                            "text": updated_text,
                            "parse_mode": "HTML",
                            "reply_markup": {"inline_keyboard": []}
                        })
                        print(f" -> Telegram Acknowledged VIN: {raw_vin}")

            # ------------------------------------------------------------------
            # 2. HANDLE /status COMMAND
            # ------------------------------------------------------------------
            message = update.get("message", {})
            text = message.get("text", "").strip()
            chat_id = message.get("chat", {}).get("id")

            if text.startswith("/status"):
                cache = load_json_file(VEHICLE_CACHE_FILE) or {}
                status_msg = "<b>📊 Current Tesla Inventory Tracker Status</b>\n\n"
                total_tracked = 0

                for zone, vehicles in cache.items():
                    status_msg += f"<b>Zone: {zone}</b> ({len(vehicles)} vehicles)\n"
                    for raw_vin, info in vehicles.items():
                        trim = info.get("trim", "Model Y")
                        price = info.get("price", "N/A")
                        vin_url = info.get("vin", raw_vin)
                        ack = "✅ [Muted]" if info.get("acknowledged") else "🚨 [Unacknowledged]"
                        status_msg += f"  • {ack} <a href='{vin_url}'>{trim}</a> ({price})\n"
                        total_tracked += 1
                    status_msg += "\n"

                if total_tracked == 0:
                    status_msg += "<i>No active inventory currently stored in cache.</i>"

                print(" -> Responding to /status request in Telegram...")
                dispatch_telegram_message(token, chat_id, status_msg)

    except Exception as e:
        print(f" -> Warning: Failed processing Telegram updates: {e}")

def trigger_alert_notifications(title, description, web_url, token, chat_id, reply_markup=None):
    """Dispatches notifications across terminal and active communication loops."""
    full_description = f"{description}\n🔗 View Inventory: {web_url}"
    print("\n" + "!"*60 + f"\n{title}\n{full_description}" + "!"*60)

    sys.stdout.write('\a')
    sys.stdout.flush()

    telegram_text = f"<b>{title}</b>\n\n{description}\n👉 <a href='{web_url}'>Click Here to View Inventory</a>"
    dispatch_telegram_message(token, chat_id, telegram_text, reply_markup=reply_markup)

    if ENABLE_EMAIL:
        import smtplib
        from email.mime.text import MIMEText
        try:
            msg = MIMEText(f"{title}\n\n{full_description}")
            msg['Subject'] = title
            msg['From'] = SENDER_EMAIL
            msg['To'] = RECEIVER_EMAIL
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
            print(" -> Email notification sent successfully.")
        except Exception as e:
            print(f" -> Failed to deliver alerting mail dispatch block: {e}")

# ==============================================================================
# PERSISTENT STORAGE CACHE HANDLERS
# ==============================================================================
def load_json_file(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception:
            print(f" -> Warning: Cache tracking target {os.path.basename(file_path)} corrupted. Dropping index.")
    return None

def save_json_file(file_path, data):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f" -> Failed writing database file reference: {e}")

# ==============================================================================
# MAIN TRACKING PIPELINE
# ==============================================================================
def get_live_akamai_session(model_code, zip_code):
    print("Opening background channel (Headless=True) to clear Akamai verification layers...")
    session_data = {"cookies": {}, "user_agent": ""}
    profile_path = os.path.abspath("./tesla_profile")

    if not os.path.exists(profile_path):
        os.makedirs(profile_path)

    with SB(uc=True, headless=True, user_data_dir=profile_path) as sb:
        encoded_zip = urllib.parse.quote_plus(zip_code)
        url = f"https://www.tesla.com/en_CA/inventory/new/{model_code}?arrangeby=relevance&zip={encoded_zip}&range=200"
        sb.uc_open_with_reconnect(url, reconnect_time=6)
        time.sleep(3)

        for cookie in sb.get_cookies():
            session_data["cookies"][cookie['name']] = cookie['value']
        session_data["user_agent"] = sb.get_user_agent()

    print(" -> New authentication profile generated cleanly.")
    save_json_file(SESSION_CACHE_FILE, session_data)
    return session_data

def request_inventory_safely(args, session):
    model_mapping = {"ct": "Cybertruck", "my": "Model Y", "m3": "Model 3"}
    model_name = model_mapping.get(args.model, args.model.upper())

    print(f"Fetching live database rows for {model_name.upper()} in {args.region} ({args.zip})...")

    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'referer': f'https://www.tesla.com/en_CA/inventory/new/{args.model}?arrangeby=relevance&zip={urllib.parse.quote_plus(args.zip)}&range={args.range}',
        'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': session["user_agent"]
    }

    query_params = {
        "query": {
            "model": args.model,
            "condition": "new",
            "options": {},
            "arrangeby": "Relevance",
            "order": "desc",
            "market": args.market,
            "language": "en",
            "super_region": "north america",
            "PaymentType": args.payment_type,
            "lng": args.lng,
            "lat": args.lat,
            "zip": args.zip,
            "region": args.region,
            "range": int(args.range)
        },
        "offset": 0,
        "count": 24,
        "outsideOffset": 0,
        "outsideSearch": False,
        "isFalconDeliverySelectionEnabled": True,
        "version": "v2"
    }

    if args.payment_range:
        query_params["query"]["paymentRange"] = args.payment_range

    encoded_query = urllib.parse.quote(json.dumps(query_params))
    api_url = f"https://www.tesla.com/inventory/api/v4/inventory-results?query={encoded_query}"

    response = curl_requests.get(
        api_url,
        headers=headers,
        cookies=session["cookies"],
        impersonate="chrome"
    )

    if response.status_code != 200:
        print(f" -> Access Denied (Status {response.status_code}). Session token expired or rejected.")
        return False

    payload = response.text
    if not payload:
        print(f" -> Success! Empty response from server. Found 0 available {model_name}s.")
        return True

    try:
        data = json.loads(payload)
        if isinstance(data, str):
            data = json.loads(data)
    except Exception:
        print(" -> Error decoding response payload structure.")
        return False

    if not isinstance(data, dict):
        data = {}

    results = data.get("results", [])
    if isinstance(results, str):
        try: results = json.loads(results)
        except Exception: results = []

    master_list = []
    if isinstance(results, dict):
        for cluster_key in ["exact", "approximate", "approximateOutside"]:
            cluster = results.get(cluster_key, [])
            if isinstance(cluster, list): master_list.extend(cluster)
    elif isinstance(results, list):
        master_list = results

    visible_vehicles = []
    for item in master_list:
        if not isinstance(item, dict) or not item.get("Price") or item.get("IsMatchedToOrder") is True:
            continue
        visible_vehicles.append(item)

    historical_inventory = load_json_file(VEHICLE_CACHE_FILE) or {}

    search_key = f"{args.region}_{args.zip}_{args.model}"
    if search_key not in historical_inventory:
        historical_inventory[search_key] = {}

    previously_saved_vins = set(historical_inventory[search_key].keys())
    currently_found_vins = set()

    unacknowledged_alerts_to_send = []

    print(f" -> Public database contains {len(visible_vehicles)} active matches inside this evaluation zone.")

    for item in visible_vehicles:
        raw_vin = item.get("VIN", "N/A")
        if raw_vin == "N/A":
            continue

        currently_found_vins.add(raw_vin)

        web_order_url = f"https://www.tesla.com/en_CA/{args.model}/order/{raw_vin}"
        price = item.get("Price", "N/A")

        subtypes = item.get("TitleSubtype", [])
        if not isinstance(subtypes, list):
            subtypes = [subtypes] if subtypes else []

        if item.get("IsDemo") is True and "DEMO" not in subtypes:
            subtypes.append("DEMO")

        subtype_prefix = " ".join([f"[{st.upper()}]" for st in subtypes]) if subtypes else ""
        base_trim = item.get("TrimName", model_name)
        trim = f"{subtype_prefix} {base_trim}".strip()

        options = []
        for option in item.get("OptionCodeSpecs", {}).get("C_OPTS", {}).get("options", []):
            options.append(option.get("description"))

        status = item.get("TransportationState", "Available")

        try: formatted_price = f"${int(price):,}"
        except (ValueError, TypeError): formatted_price = f"${price}"

        # Get acknowledgment state if already seen
        already_ack = historical_inventory[search_key].get(raw_vin, {}).get("acknowledged", False)

        vehicle_payload = {
            "vin": web_order_url,
            "raw_vin": raw_vin,
            "price": formatted_price,
            "trim": trim,
            "options": options,
            "status": status,
            "acknowledged": already_ack
        }

        # Save to cache so /status knows about it immediately
        historical_inventory[search_key][raw_vin] = vehicle_payload

        # REPEATING ALERTS LOGIC:
        # If the user has NOT acknowledged this car yet, send an alert!
        if not already_ack:
            print(f"    🚨 [UNACKNOWLEDGED / ALERTING] - [{trim}] - Price: {formatted_price} | VIN: {raw_vin}")
            unacknowledged_alerts_to_send.append(vehicle_payload)
        else:
            print(f"    • [Acknowledged / Silent]    - [{trim}] - VIN: {raw_vin} is muted.")

    # Calculate dropped / sold inventory items safely
    sold_vins = previously_saved_vins - currently_found_vins
    sold_vehicles_detected = []

    for sold_vin in sold_vins:
        sold_info = historical_inventory[search_key][sold_vin]
        sold_trim = sold_info.get("trim", model_name)
        print(f"    ❌ [REMOVED/SOLD] - [{sold_trim}] - VIN: {sold_vin}")
        sold_vehicles_detected.append(sold_info)
        del historical_inventory[search_key][sold_vin]

    # Save state back to cache
    save_json_file(VEHICLE_CACHE_FILE, historical_inventory)

    # Dynamic Direct Web Browser URL construction
    encoded_zip = urllib.parse.quote_plus(args.zip)
    market_path = args.market.lower() if args.market.lower() != "us" else "en_US"
    if market_path == "ca": market_path = "en_CA"

    direct_web_url = f"https://www.tesla.com/{market_path}/inventory/new/{args.model}?arrangeby=relevance&zip={encoded_zip}&range={args.range}"

    # Dispatch alerts with Inline Acknowledge Buttons for all unacknowledged cars
    if unacknowledged_alerts_to_send:
        title = f"🚨 TESLA INVENTORY ALERT ({len(unacknowledged_alerts_to_send)} Active Vehicle(s) Require Action)!"

        for v in unacknowledged_alerts_to_send:
            body = f"✨ ACTIVE: [{v['trim']}] - {v['options']}\nPrice: {v['price']} | Status: {v['status']} | VIN: {v['vin']}"

            # Generate Acknowledge Button
            reply_markup = json.dumps({
                "inline_keyboard": [[
                    {
                        "text": "✅ Acknowledge & Mute Alerts",
                        "callback_data": f"ack_{v['raw_vin']}"
                    }
                ]]
            })

            trigger_alert_notifications(title, body, direct_web_url, args.tg_token, args.tg_chat, reply_markup=reply_markup)

    # Trigger alerts for SOLD entries
    if sold_vehicles_detected:
        title = f"💨 TESLA INVENTORY SOLD: {len(sold_vehicles_detected)} {model_name}(s) Left Market in {args.region} ({args.zip})!"
        body = ""
        for v in sold_vehicles_detected:
            trim = v.get("trim", model_name)
            options = v.get("options", [])
            price = v.get("price", "N/A")
            vin_link = v.get("vin", v.get("raw_vin", "N/A"))
            body += f"❌ SOLD: [{trim}] - {options} | Price: {price} | VIN: {vin_link}\n"
        trigger_alert_notifications(title, body, direct_web_url, args.tg_token, args.tg_chat)

    return True

# ==============================================================================
# ENTRY INITIALIZATION CONTRACT
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Tesla Custom Laptop Inventory Tracker Engine")
    parser.add_argument("-m", "--model", choices=["ct", "my", "m3"], required=True)
    parser.add_argument("-z", "--zip", default="VV3B0G6")
    parser.add_argument("-r", "--range", default="200")
    parser.add_argument("-reg", "--region", default="BC")
    parser.add_argument("-mkt", "--market", default="CA")
    parser.add_argument("-pt", "--payment_type", default="cash")
    parser.add_argument("-pr", "--payment_range", default="1,200000")
    parser.add_argument("-lat", "--lat", type=float, default=49.255052)
    parser.add_argument("-lng", "--lng", type=float, default=-122.748232)

    # Telegram Overrides Command Line Arguments
    parser.add_argument("--tg_token", default="")
    parser.add_argument("--tg_chat", default="")

    args = parser.parse_args()

    # Process pending Telegram /status commands and Acknowledge button clicks
    process_telegram_updates(args.tg_token)

    # Attempt cached verification session token extraction
    session = load_json_file(SESSION_CACHE_FILE)

    if not session:
        print(" -> No dynamic profile tracking cache found.")
        session = get_live_akamai_session(args.model, args.zip)

    print("=" * 70)

    # Process inventory request check safely with hot loop recovery matrix
    success = request_inventory_safely(args, session)

    if not success:
        print("\n -> Cache validation failed or dropped by proxy. Refreshing credentials via SeleniumBase...")
        session = get_live_akamai_session(args.model, args.zip)
        print("-" * 70)
        request_inventory_safely(args, session)

    print("=" * 70)

if __name__ == "__main__":
    main()
