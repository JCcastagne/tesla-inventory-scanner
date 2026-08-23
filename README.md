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

# other
written with alot of help from Gemini
