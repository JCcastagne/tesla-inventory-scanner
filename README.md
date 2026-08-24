# Tesla Inventory Scanner

A lightweight Python tool to monitor Canadian Tesla inventory and send instant Telegram notifications when new vehicles match a given criteria.

Designed for headless Linux environments and virtual private servers (VPS) using the uv package manager. Requires loading google chrome browser to beat bot protection via python seleniumbase package.  
For telegram notifications you must setup a telegram bot and obtain the token and chat ids.

# Features

- **Bot Bypass:** Uses `seleniumbase` with Google Chrome to seamlessly handle Akamai bot protection.
- **Persistent Alerts:** Repeat notifications keep you updated on vehicle availability until acknowledged.
- **Experimental Acknowledge Button:** Includes a Telegram interactive button to mute active alerts.
- **State Management:** Tracks active listings, session cookies, and inventory state locally across runs.

#### Disclaimer

This project is an experimental reference implementation created for educational purposes. It demonstrates how to handle modern bot protection and track inventory programmatically. This tool is independent and not affiliated with, endorsed by, or connected to Tesla, Inc. or its subsidiaries. Use at your own risk.

## Requirements

- **OS:** Linux (Ubuntu/Debian recommended for headless VPS environments)
- **Package Manager:** [uv](https://github.com)
- **Browser:** Google Chrome installed on the host machine
- **Credentials:** A Telegram Bot Token and Chat ID

## Usage

The `uv` package manager will automatically resolve and install all Python requirements on the first run.

```bash
uv run tesla_inventory_scanner.py [options]
```

### Options

| Flag                   | Argument        | Description                                         |
| :--------------------- | :-------------- | :-------------------------------------------------- |
| `-h, --help`           | None            | Show help message and exit                          |
| `-m, --model`          | `{ct, my, m3}`  | Tesla model to scan (Cybertruck, Model Y, Model M3) |
| `-z, --zip`            | `ZIP`           | Postal code / ZIP code                              |
| `-r, --range`          | `RANGE`         | Search radius in miles/kilometers                   |
| `-reg, --region`       | `REGION`        | Canadian province/region (e.g., `BC`, `ON`)         |
| `-mkt, --market`       | `MARKET`        | Market code                                         |
| `-pt, --payment_type`  | `PAYMENT_TYPE`  | Payment type filtering                              |
| `-pr, --payment_range` | `PAYMENT_RANGE` | Price or monthly payment range                      |
| `--lat`                | `LAT`           | Latitude coordinates                                |
| `--lng`                | `LNG`           | Longitude coordinates                               |
| `--tg_token`           | `TG_TOKEN`      | Your Telegram Bot API Token                         |
| `--tg_chat`            | `TG_CHAT`       | Your Telegram personal/channel Chat ID              |

## Example

```bash
uv run canada_tesla.py -z "V5L1H7" -reg "BC" --lat 49.255052 --lng -122.748232 -m m3
```

```
======================================================================
Fetching live database rows for MODEL 3 in BC (V5L1H7)...
 -> Public database contains 1 active matches inside this evaluation zone.
    🚨 [UNACKNOWLEDGED / ALERTING] - [[BRANDNEW] Premium All-Wheel Drive] - Price: $52,590 | VIN: LRW3198_2758b2cbb7cc50beab7cd506fee79f44

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
🚨 TESLA INVENTORY ALERT (1 Active Vehicle(s) Require Action)!
✨ ACTIVE: [[BRANDNEW] Premium All-Wheel Drive] - ['Ultra Red', '18’’ Photon Wheels', 'Black Premium Interior', 'Traffic-Aware Cruise Control']
Price: $52,590 | Status: Available | VIN: https://www.tesla.com/en_CA/m3/order/LRW3198_2758b2cbb7cc50beab7cd506fee79f44
🔗 View Inventory: https://www.tesla.com/en_CA/inventory/new/m3?arrangeby=relevance&zip=V5L1H7&range=200
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
======================================================================
```

## Architecture

```text
               ┌────────────────────────┐
               │    Linux VPS Cron      │
               └───────────┬────────────┘
                           │ Runs every 5 minutes
                           ▼
               ┌────────────────────────┐
               │ tesla_inventory_sh/py  │
               └───────────┬────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │  Tesla Inventory API   │
               │  (via SeleniumBase)    │
               └───────────┬────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │     VIN Comparison     │
               └─────┬────────────┬─────┘
                     │            │
         New Vehicle │            │ Vehicle Removed
                     ▼            ▼
         ┌──────────────┐      ┌──────────────┐
         │ Send Telegram│      │ Clear Local  │
         │    Alert     │      │    State     │
         └──────────────┘      └──────────────┘
```

## Acknowledgements

- Original (author)[https://github.com/killafunkinmofo/] declared that the code was built with the assistance from Google Gemini. All other modifications/commits created afterwards is the code from the (owner)[https://github.com/JCcastagne/] of this fork/repo.

## Disclaimer

This project is an experimental reference implementation created for educational and research purposes. It demonstrates how to handle modern bot protection and track inventory changes programmatically. This tool is independent and is not affiliated with, endorsed by, or connected to Tesla, Inc. or its subsidiaries. Use at your own risk.
