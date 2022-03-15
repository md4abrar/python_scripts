import json
import requests
from base64 import b64encode

key = $NewRelicKey
headers = {"Api-Key": key, "Content-Type": "application/json"}
file_obj = open("synthetic_monitor.json")
body = json.load(file_obj)
monitor_name = body["name"]
url = "https://synthetics.newrelic.com/synthetics/api/v3/monitors"

print("Creating Monitor:  {}".format(monitor_name))
create_mon = requests.post(url, headers=headers, data=json.dumps(body))
montior_exists_msg = "Invalid name specified: '{}'; a monitor with that name already exists.".format(monitor_name)
if create_mon.status_code == 201:
    print ("Monitor is successfully created")
elif create_mon.json()['errors'][0]['error'] == montior_exists_msg:
    print("Looks like the monitor {} is already created".format(monitor_name))
elif create_mon.status_code != 201:
   print ("There is some issue creating monitor {} ".format(monitor_name))

# Get Monitor Id
monitors_url = "https://synthetics.newrelic.com/synthetics/api/v3/monitors?limit=250"
mons = requests.get(monitors_url,headers=headers)
all_monitors = mons.json()['monitors']
def get_monitor_id(monitor_name):
   for monitor in range (0, len(all_monitors)):
      if all_monitors[monitor]['name'] == monitor_name:
         monitor_id = all_monitors[monitor]['id']
         print ("This is the monitor Id: {} ".format(monitor_id))
         break
      else:
         monitor_id = ""
   return monitor_id

monitor_id = get_monitor_id(monitor_name)

script_url = url + "/" + str(monitor_id) + "/script"

script_file = open("newrelic_script.js", "r")
script_file_content = script_file.read()
encoded_text = script_file_content.encode()
encrypted_script = b64encode(encoded_text)
encrypted_script_data = encrypted_script.decode()
script_body = {"scriptText": encrypted_script_data }
script_pos = requests.put(script_url, headers=headers, data=json.dumps(script_body))

