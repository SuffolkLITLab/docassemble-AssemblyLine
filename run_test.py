
import requests
import json
import re

session = requests.Session()
url = "https://apps-dev.suffolklitlab.org/interview?i=docassemble.playground10ALInterviewImport:test_import_filter.yml"
print("Fetching URL:", url)
try:
    r = session.get(url, timeout=60)
    print("Status Code:", r.status_code)
    
    match = re.search(r"<pre id="test_results">\s*(.*?)\s*</pre>", r.text, re.DOTALL)
    if match:
        data = json.loads(match.group(1))
        print("SUCCESS! Parsed JSON:")
        print(json.dumps(data, indent=2))
        
        print("\nusers in all_vars?", "users" in data["all_vars"])
        print("my_test_var in all_vars?", "my_test_var" in data["all_vars"])
    else:
        print("Failed to find results. HTML excerpt:")
        print(r.text.split("<body")[1][:2000] if "<body" in r.text else r.text[:2000])
except Exception as e:
    print("Error:", type(e).__name__, str(e))
