# inventory-scanner
helps to check tesla inventory to get notified when new cars are available in your area

Designed and used with macos and uv.  
Requires loading google chrome browser to beat bot protection via python seleniumbase package.  
For telegram notifications you must setup a telegram bot and obtain the token and chat ids. 

**Disclaimer:** This project is provided as an experimental reference implementation and is not actively maintained. It demonstrates how to bypass Akamai bot detection using `seleniumbase` and track inventory changes programmatically.

# usage
uv run tesla_inventory_scanner.py  
options:  
  -h, --help            show this help message and exit  
  -m {ct,my,m3}, --model {ct,my,m3}  
  -z ZIP, --zip ZIP  
  -r RANGE, --range RANGE  
  -reg REGION, --region REGION  
  -mkt MARKET, --market MARKET  
  -pt PAYMENT_TYPE, --payment_type PAYMENT_TYPE  
  -pr PAYMENT_RANGE, --payment_range PAYMENT_RANGE  
  -lat LAT, --lat LAT  
  -lng LNG, --lng LNG  
  --tg_token TG_TOKEN  
  --tg_chat TG_CHAT  

uv should install all requirements before running. 

The notifications should repeat if this is run repeatedly to better notify the user of availability. The notification has an experimental acknowledge button that seems to mostly work.

The script creates local files to track state, cookies, and inventory. 

# example
```
uv run canada_tesla.py -z "V5L1H7" -reg "BC" --lat 49.255052 --lng -122.748232 -m m3
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

# other
written with alot of help from Gemini
