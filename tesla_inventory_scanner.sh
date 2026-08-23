##Example shell script that scans all regions once per hour. 
##I generated unique list of tesla service center postal codes with co-ordinatnes.
##It searches 200km radius and I tried to avoid overlap, but there still is some.
##On mac laptop, I would run this with caffeinate to avoid computer sleeping

TG_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxxxxx"
TG_CHAT="-2346326326326326326"

COMMON_ARGS=(-m my -pt cash -pr "1,200000" --tg_token "$TG_TOKEN" --tg_chat "$TG_CHAT")

while true; do
 echo "========================================================================"
 echo " 🚀 INVENTORY SCAN INITIALIZED: $(date "+%Y-%m-%d %H:%M:%S")"
 echo "========================================================================"

 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "T2H0X3" -reg "AB" --lat 51.0447 --lng -114.0719
 echo "------------------------------------------------------------------------"

 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "T5S0A2" -reg "AB" --lat 53.5461 --lng -113.4938
 echo "------------------------------------------------------------------------"

 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "V1V2Y4" -reg "BC" --lat 49.8874 --lng -119.4960
 echo "------------------------------------------------------------------------"

 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "V5L1H7" -reg "BC" --lat 49.2827 --lng -123.1207
 echo "------------------------------------------------------------------------"

 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "R3T5V7" -reg "MB" --lat 49.8951 --lng -97.1384
 echo "------------------------------------------------------------------------"

 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "B3B1V5" -reg "NS" --lat 44.6681 --lng -63.5674
 echo "------------------------------------------------------------------------"

 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "M3A1C6" -reg "ON" --lat 43.6532 --lng -79.3832
 echo "------------------------------------------------------------------------"

 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "H4P1L9" -reg "QC" --lat 45.5017 --lng -73.5673
 echo "------------------------------------------------------------------------"

 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "G1N2E5" -reg "QC" --lat 46.8139 --lng -71.2080
 echo "------------------------------------------------------------------------"

 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "S7T0C9" -reg "SK" --lat 52.1332 --lng -106.6700

 echo "========================================================================"
 echo " ✅ Full regional scanning sequence complete."
 echo " 💤 Sleeping for 1 hour until the next refresh pass..."
 echo "========================================================================"

 sleep 3600
done
