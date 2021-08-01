''' This Script fetches all your api's running in cloudhub and gets respective maximum cpu utilization and writes into csv 
Inputs: 
        username =  anypoint platform
		password =  anypoint platform
		EnvId = Environment id for which you are fetching the logs
		OrgId = Your anypoint platform Organization id 
'''


# Import Libraries

import requests
import json
import csv
import os
import time

##########################################################

# Get Token to use further calls

url = 'https://anypoint.mulesoft.com/accounts/login'
payload = {
  "username": User ,
  "password": Password
  }
  
headers = {'content-type': 'application/json'}
r = requests.post(url, data=json.dumps(payload), headers=headers)
raw_token = json.loads(r.text)
token  = raw_token["access_token"]
bearer = "Bearer " + token 

##########################################################

next_url = "https://anypoint.mulesoft.com/cloudhub/api/applications" 

headers_api_generic = {
   "Authorization": bearer,
   "X-ANYPNT-ENV-ID": EnvId, 
   "X-ANYPNT-ORG-ID": OrgId,
   }
   
get_api_generic = requests.get(next_url, headers=headers_api_generic )

##GetApi_generic.text

raw_content = get_api_generic.content
res = json.loads(raw_content)

##########################################################

# Get All applications running in mule

apps = []
for val in range(0, len(res)):
   appname = res[val]["domain"] 
   apps.append(appname)

# Funtion to Get CpuUsage per app and write into a file

def GetCpuUsage(app_name):
   next_url = "https://anypoint.mulesoft.com/cloudhub/api/v2/applications/" + app_name + "/dashboardStats" 
   headers_api = {
      "Authorization": bearer,
      "X-ANYPNT-ENV-ID": EnvId
      }
   GetApi = requests.get(next_url, headers=headers_api )
   decode_text = json.loads(GetApi.text)
   cpu_utilization = []
   if len(decode_text["workerStatistics"]) == 0:
       print ("If this is set to 0 then skip it")
       pass
   else:
       cpu_utilization = []
       cpu_utilization =  decode_text["workerStatistics"][0]["statistics"]["cpu"] 
       cpu_keys = list(cpu_utilization.keys())
       cpu_values = list(cpu_utilization.values())
       max_cpu_index_v = cpu_values.index(max(cpu_values))
       max_cpu_v =  cpu_values[max_cpu_index_v]
       max_cpu_k = cpu_keys[max_cpu_index_v] 
       key = int(max_cpu_k[:-3])
       stdtime = time.strftime("%b %d %Y %H:%M:%S", time.localtime(key))  
       WriteIntoFile.writerow([str(app_name), stdtime, max_cpu_v])
   return cpu_utilization 


# Open a file to write

WriteIntoFile = csv.writer(open("CpuUtilizationLogs.csv", "a+", newline=''))
WriteIntoFile.writerow([str("app_name"),str("DateAndTime"), str("CpuUsage")])


# Loop across apps and spawn the function GetCpuUsage

for a in range(0, len(apps)):
   app_name = apps[a]
   appname_Log =  GetCpuUsage(app_name) 
