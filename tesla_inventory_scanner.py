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


# ==============================================================================
# DISCORD NOTIFICATION CONTROLLER
# ==============================================================================
def dispatch_discord_message(webhook_url, title, description, web_url=None):
    """Send a Discord webhook embed. Returns True when Discord accepts it."""
    if not webhook_url:
        print(" -> Discord webhook URL is not configured.")
        return False

    embed = {
        "title": title[:256],
        "description": description[:4096],
    }

    if web_url:
        embed["url"] = web_url

    payload = {
        "username": "Tesla Inventory Scanner",
        "embeds": [embed],
    }

    try:
        response = curl_requests.post(
            webhook_url,
            json=payload,
            impersonate="chrome",
            timeout=15,
        )

        if response.status_code not in (200, 204):
            print(
                f" -> Discord notification failed "
                f"(Status {response.status_code})."
            )
            return False

        print(" -> Discord notification sent successfully.")
        return True

    except Exception as e:
        print(f" -> Failed to send Discord notification: {e}")
        return False


def trigger_alert_notification(title, description, web_url, discord_webhook):
    """Print an inventory event locally and send it to Discord."""
    full_description = f"{description}\n🌐 View Inventory: {web_url}"

    print(
        "\n"
        + "!" * 60
        + f"\n{title}\n{full_description}\n"
        + "!" * 60
    )

    sys.stdout.write("\a")
    sys.stdout.flush()

    return dispatch_discord_message(
        discord_webhook,
        title,
        description,
        web_url,
    )


# ==============================================================================
# PERSISTENT STORAGE CACHE HANDLERS
# ==============================================================================
def load_json_file(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception:
            print(
                f" -> Warning: Cache tracking target "
                f"{os.path.basename(file_path)} corrupted. Dropping index."
            )
    return None


def save_json_file(file_path, data):
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f" -> Failed writing database file reference: {e}")


# ==============================================================================
# MAIN TRACKING PIPELINE
# ==============================================================================
def get_live_akamai_session(model_code, zip_code):
    print(
        "Opening background channel (Headless=True) "
        "to clear Akamai verification layers..."
    )

    session_data = {"cookies": {}, "user_agent": ""}
    profile_path = os.path.abspath("./tesla_profile")

    if not os.path.exists(profile_path):
        os.makedirs(profile_path)

    with SB(uc=True, headless=True, user_data_dir=profile_path) as sb:
        encoded_zip = urllib.parse.quote_plus(zip_code)
        url = (
            f"https://www.tesla.com/en_CA/inventory/new/{model_code}"
            f"?arrangeby=relevance&zip={encoded_zip}&range=200"
        )

        sb.uc_open_with_reconnect(url, reconnect_time=6)
        time.sleep(3)

        for cookie in sb.get_cookies():
            session_data["cookies"][cookie["name"]] = cookie["value"]

        session_data["user_agent"] = sb.get_user_agent()

    print(" -> New authentication profile generated cleanly.")
    save_json_file(SESSION_CACHE_FILE, session_data)
    return session_data


def request_inventory_safely(args, session):
    model_mapping = {
        "ct": "Cybertruck",
        "my": "Model Y",
        "m3": "Model 3",
    }
    model_name = model_mapping.get(args.model, args.model.upper())

    print(
        f"Fetching live database rows for {model_name.upper()} "
        f"in {args.region} ({args.zip})..."
    )

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": (
            f"https://www.tesla.com/en_CA/inventory/new/{args.model}"
            f"?arrangeby=relevance"
            f"&zip={urllib.parse.quote_plus(args.zip)}"
            f"&range={args.range}"
        ),
        "sec-ch-ua": (
            '"Chromium";v="148", "Google Chrome";v="148", '
            '"Not/A)Brand";v="99"'
        ),
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": session["user_agent"],
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
            "range": int(args.range),
        },
        "offset": 0,
        "count": 24,
        "outsideOffset": 0,
        "outsideSearch": False,
        "isFalconDeliverySelectionEnabled": True,
        "version": "v2",
    }

    if args.payment_range:
        query_params["query"]["paymentRange"] = args.payment_range

    encoded_query = urllib.parse.quote(json.dumps(query_params))
    api_url = (
        "https://www.tesla.com/inventory/api/v4/inventory-results"
        f"?query={encoded_query}"
    )

    try:
        response = curl_requests.get(
            api_url,
            headers=headers,
            cookies=session["cookies"],
            impersonate="chrome",
            timeout=30,
        )
    except Exception as e:
        print(f" -> Inventory request failed before receiving a response: {e}")
        return False

    if response.status_code != 200:
        print(
            f" -> Access Denied (Status {response.status_code}). "
            "Session token expired or rejected."
        )
        return False

    payload = response.text
    if not payload:
        print(
            f" -> Success! Empty response from server. "
            f"Found 0 available {model_name}s."
        )
        return True

    try:
        data = json.loads(payload)
        if isinstance(data, str):
            data = json.loads(data)
    except Exception:
        print(" -> Error decoding response payload structure.")
        return False

    if not isinstance(data, dict):
        print(" -> Unexpected inventory payload structure.")
        return False

    results = data.get("results", [])

    if isinstance(results, str):
        try:
            results = json.loads(results)
        except Exception:
            print(" -> Error decoding inventory results.")
            return False

    master_list = []

    if isinstance(results, dict):
        for cluster_key in ["exact", "approximate", "approximateOutside"]:
            cluster = results.get(cluster_key, [])
            if isinstance(cluster, list):
                master_list.extend(cluster)
    elif isinstance(results, list):
        master_list = results

    visible_vehicles = []

    for item in master_list:
        if (
            not isinstance(item, dict)
            or not item.get("Price")
            or item.get("IsMatchedToOrder") is True
        ):
            continue

        visible_vehicles.append(item)

    historical_inventory = load_json_file(VEHICLE_CACHE_FILE) or {}

    search_key = f"{args.region}_{args.zip}_{args.model}"
    is_first_scan = search_key not in historical_inventory

    if is_first_scan:
        historical_inventory[search_key] = {}

    previously_saved_vins = set(historical_inventory[search_key].keys())
    currently_found_vins = set()

    new_vehicles_detected = []

    print(
        f" -> Public database contains {len(visible_vehicles)} "
        "active matches inside this evaluation zone."
    )

    for item in visible_vehicles:
        raw_vin = item.get("VIN", "N/A")

        if raw_vin == "N/A":
            continue

        currently_found_vins.add(raw_vin)

        web_order_url = (
            f"https://www.tesla.com/en_CA/{args.model}/order/{raw_vin}"
        )
        price = item.get("Price", "N/A")

        subtypes = item.get("TitleSubtype", [])
        if not isinstance(subtypes, list):
            subtypes = [subtypes] if subtypes else []

        if item.get("IsDemo") is True and "DEMO" not in subtypes:
            subtypes.append("DEMO")

        subtype_prefix = (
            " ".join([f"[{st.upper()}]" for st in subtypes])
            if subtypes
            else ""
        )

        base_trim = item.get("TrimName", model_name)
        trim = f"{subtype_prefix} {base_trim}".strip()

        options = []
        for option in (
            item.get("OptionCodeSpecs", {})
            .get("C_OPTS", {})
            .get("options", [])
        ):
            description = option.get("description")
            if description:
                options.append(description)

        status = item.get("TransportationState", "Available")

        try:
            formatted_price = f"${int(price):,}"
        except (ValueError, TypeError):
            formatted_price = f"${price}"

        vehicle_payload = {
            "vin": web_order_url,
            "raw_vin": raw_vin,
            "price": formatted_price,
            "trim": trim,
            "options": options,
            "status": status,
        }

        is_new = (
            not is_first_scan
            and raw_vin not in previously_saved_vins
        )

        historical_inventory[search_key][raw_vin] = vehicle_payload

        if is_new:
            print(
                f"    🚨 [NEW] - [{trim}] - "
                f"Price: {formatted_price} | VIN: {raw_vin}"
            )
            new_vehicles_detected.append(vehicle_payload)
        else:
            prefix = "[BASELINE]" if is_first_scan else "[UNCHANGED]"
            print(
                f"    • {prefix} - [{trim}] - VIN: {raw_vin}"
            )

    gone_vins = previously_saved_vins - currently_found_vins
    gone_vehicles_detected = []

    # On a first scan there is no previous state, so there can be no gone VINs.
    if not is_first_scan:
        for gone_vin in gone_vins:
            gone_info = historical_inventory[search_key].get(gone_vin, {})
            gone_trim = gone_info.get("trim", model_name)

            print(
                f"    ❌ [GONE] - [{gone_trim}] - VIN: {gone_vin}"
            )

            if gone_info:
                gone_vehicles_detected.append(gone_info)

            historical_inventory[search_key].pop(gone_vin, None)

    # Dynamic Direct Web Browser URL construction
    encoded_zip = urllib.parse.quote_plus(args.zip)
    market_path = (
        args.market.lower()
        if args.market.lower() != "us"
        else "en_US"
    )

    if market_path == "ca":
        market_path = "en_CA"

    direct_web_url = (
        f"https://www.tesla.com/{market_path}/inventory/new/{args.model}"
        f"?arrangeby=relevance&zip={encoded_zip}&range={args.range}"
    )

    # First successful scan establishes a baseline silently.
    if is_first_scan:
        print(
            f" -> Initial baseline saved for {args.region} ({args.zip}); "
            "no Discord alerts sent."
        )

    # Send one Discord event per newly detected VIN.
    for vehicle in new_vehicles_detected:
        options_text = (
            ", ".join(vehicle["options"])
            if vehicle["options"]
            else "No option details provided"
        )

        title = f"🚨 NEW TESLA INVENTORY — {vehicle['trim']}"
        body = (
            f"**Region:** {args.region} ({args.zip})\n"
            f"**Price:** {vehicle['price']}\n"
            f"**Status:** {vehicle['status']}\n"
            f"**VIN:** `{vehicle['raw_vin']}`\n"
            f"**Options:** {options_text}\n"
            f"**Order:** {vehicle['vin']}"
        )

        trigger_alert_notification(
            title,
            body,
            vehicle["vin"],
            args.discord_webhook,
        )

    # Send one Discord event per VIN that disappeared from this search zone.
    for vehicle in gone_vehicles_detected:
        options = vehicle.get("options", [])
        options_text = (
            ", ".join(options)
            if options
            else "No option details provided"
        )

        raw_vin = vehicle.get("raw_vin", "N/A")
        trim = vehicle.get("trim", model_name)
        price = vehicle.get("price", "N/A")

        title = f"💨 TESLA INVENTORY GONE — {trim}"
        body = (
            f"**Region:** {args.region} ({args.zip})\n"
            f"**Price:** {price}\n"
            f"**VIN:** `{raw_vin}`\n"
            f"**Options:** {options_text}"
        )

        trigger_alert_notification(
            title,
            body,
            direct_web_url,
            args.discord_webhook,
        )

    # Only update persistent inventory after a successful Tesla response
    # and after change detection has completed.
    save_json_file(VEHICLE_CACHE_FILE, historical_inventory)

    return True


# ==============================================================================
# ENTRY INITIALIZATION CONTRACT
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Tesla Inventory Tracker"
    )

    parser.add_argument(
        "-m",
        "--model",
        choices=["ct", "my", "m3"],
        required=True,
    )
    parser.add_argument("-z", "--zip", default="V3B0G6")
    parser.add_argument("-r", "--range", default="200")
    parser.add_argument("-reg", "--region", default="BC")
    parser.add_argument("-mkt", "--market", default="CA")
    parser.add_argument("-pt", "--payment_type", default="cash")
    parser.add_argument(
        "-pr",
        "--payment_range",
        default="1,200000",
    )
    parser.add_argument(
        "-lat",
        "--lat",
        type=float,
        default=49.255052,
    )
    parser.add_argument(
        "-lng",
        "--lng",
        type=float,
        default=-122.748232,
    )
    parser.add_argument(
        "--discord_webhook",
        default="",
        help="Discord webhook URL used for inventory change notifications.",
    )

    args = parser.parse_args()

    # Attempt cached verification session token extraction.
    session = load_json_file(SESSION_CACHE_FILE)

    if not session:
        print(" -> No dynamic profile tracking cache found.")
        session = get_live_akamai_session(args.model, args.zip)

    print("=" * 70)

    # Process inventory request safely with one SeleniumBase refresh retry.
    success = request_inventory_safely(args, session)

    if not success:
        print(
            "\n -> Cache validation failed or dropped by proxy. "
            "Refreshing credentials via SeleniumBase..."
        )

        session = get_live_akamai_session(args.model, args.zip)

        print("-" * 70)

        success = request_inventory_safely(args, session)

        if not success:
            print(
                " -> Inventory request failed again after session refresh. "
                "Inventory cache was left unchanged."
            )


if __name__ == "__main__":
    main()
