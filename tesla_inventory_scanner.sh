##Shell script that scans all regions once per hour.

##Each selected postal-code point has a maximum coverage radius of 200 km, with the objective to cover every Tesla store/dealership currently listed by Tesla in Canada with as few points as practical.
##Tesla’s current Canadian store directory spans Alberta, BC, Manitoba, New Brunswick, Nova Scotia, Ontario, Quebec and Saskatchewan.

## Tokens to connect to Telegram for notifications. Replace with your own.
TG_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxxxxx"
TG_CHAT="xxxxxxxxxxxxxxxxxxxxxxxxxxxx"

## Common arguments for the Tesla inventory scanner script.
COMMON_ARGS=(-m my -pt cash -pr "1,200000" --tg_token "$TG_TOKEN" --tg_chat "$TG_CHAT")

while true; do
 ## Take note of the start time (to calculate how long the scan took).
 START=$(date +%s)

 echo "========================================================================"
 echo " 🚀 INVENTORY SCAN INITIALIZED: $(date "+%Y-%m-%d %H:%M:%S")"
 echo "========================================================================"

 ##CALGARY, AB - Covers Calgary-Fairmount.
 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "T2H0X3" -reg "AB" --lat 50.993254 --lng -114.063780
 echo "------------------------------------------------------------------------"

 ##EDMONTON, AB - Covers Edmonton, Edmonton Southgate Pop-Up.
 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "T5S0A2" -reg "AB" --lat 53.560396 --lng -113.624892
 echo "------------------------------------------------------------------------"

 ##VANCOUVER, BC - Covers West Vancouver Park Royal, Richmond, Surrey Scott Rd, Surrey, CF Richmond Centre Pop-Up, Port Coquitlam, Vancouver-Raymur Gallery.
 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "V6J1L9" -reg "BC" --lat 49.267845 --lng -123.141836
 echo "------------------------------------------------------------------------"

 ##KELOWNA, BC - Covers Kelowna.
 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "V1V2Y4" -reg "BC" --lat 49.880000 --lng -119.440000
 echo "------------------------------------------------------------------------"

 ##SASKATOON, SK - Covers Saskatoon.
 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "S7T0C9" -reg "SK" --lat 52.085519 --lng -106.653751
 echo "------------------------------------------------------------------------"

 ##WINNIPEG, MB - Covers Winnipeg.
 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "R3T5V7" -reg "MB" --lat 49.895000 --lng -97.140000
 echo "------------------------------------------------------------------------"

 ##TORONTO, ON - Covers CF Sherway Gardens, Lawrence Avenue, Yorkdale Shopping Centre, Chrislea Rd Vaughan, Markham, Markham Mall Pop-Up, Oshawa Center Mall Oshawa, Doral Dr Barrie, Coachworks Cres Brampton, CF Like Ridge Mall Hamilton, Wyecroft Oakville, Premium Outlets Pop-Up Halton Hills, Victoria St N Kitchener, CF Masonville Place London, Wonderland Rs S London.
 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "M9C1B8" -reg "ON" --lat 43.612678 --lng -79.557579
 echo "------------------------------------------------------------------------"

 ##MONTREAL, QC - Covers Montreal, Laval, Saint-Brun-de-Montarville, CF Fairview Pointe-Claire Pop-Up, West Island Kirkland, Sherbrooke, Carling Ottawa, Barrhaven Nepean/Ottawa.
 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "H4P1L9" -reg "QC" --lat 45.496185 --lng -73.658793
 echo "------------------------------------------------------------------------"

 ##QUEBEC CITY, QC - Covers Quebec City.
 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "G1N2G3" -reg "QC" --lat 46.813900 --lng -71.207900
 echo "------------------------------------------------------------------------"

 ##DIEPPE, NB & Dartmouth NS - Covers CF Champlain Mall, Dartmouth NS.
 uv run tesla_inventory_scanner.py $COMMON_ARGS -z "E1A4X5" -reg "NB" --lat 46.094000 --lng -64.735000
 echo "------------------------------------------------------------------------"

 echo "========================================================================"
 echo " ✅ Full regional scanning sequence complete."
 echo " 💤 Sleeping for 5 minutes until the next refresh pass."
 echo "========================================================================"

 ## Calculate how long the scan took, and sleep for the remainder (if any) of the 5 minutes.
 END=$(date +%s)
 ELAPSED=$((END - START))
 SLEEP_TIME=$((300 - ELAPSED))

 if [ "$SLEEP_TIME" -gt 0 ]; then
  sleep "$SLEEP_TIME"
 fi

done
