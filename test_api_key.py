import urllib.request, json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

key = os.environ.get("WEATHERAPI_KEY", "")
if not key:
    print("STATUS : ❌ WEATHERAPI_KEY env var not set. Run: set WEATHERAPI_KEY=your_key")
    sys.exit(1)

url = 'http://api.weatherapi.com/v1/current.json?key=' + key + '&q=London&aqi=no'

try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=8) as r:
        d = json.loads(r.read())
        loc = d['location']
        cur = d['current']
        print('STATUS : ✅ ACTIVE — Key is working!')
        print('City   :', loc['name'] + ',', loc['country'])
        print('Temp   :', cur['temp_c'], 'C')
        print('Weather:', cur['condition']['text'])
        print('Wind   :', cur['wind_kph'], 'km/h')
except urllib.error.HTTPError as e:
    try:
        body = json.loads(e.read())
        code = body.get('error', {}).get('code', '?')
        msg  = body.get('error', {}).get('message', 'Unknown error')
        print('STATUS : ❌ NOT ACTIVE')
        print('HTTP   :', e.code)
        print('Code   :', code)
        print('Reason :', msg)
        if code == 2006:
            print('>> API key is invalid')
        elif code == 2007:
            print('>> API key quota exceeded')
        elif code == 2008:
            print('>> API key disabled')
    except:
        print('STATUS : ❌ HTTP Error', e.code)
except Exception as e:
    print('STATUS : ❌ NETWORK ERROR')
    print('Detail :', str(e))
    print('>> This machine may not have internet access to external APIs')
