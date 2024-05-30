# Script flow starts from the line 132

import sys
import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import logging
import pandas as pd
from redmail import EmailSender
from almapipy import AlmaCnxn
import yaml
import time



# Loading config objects including API keys from YAML
path = ('./')
with open(path + '/' + 'config.yml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)


# Create connection to the RS partners API
alma = AlmaCnxn(config["partners"]["api_key"], data_format='json')


# Process JSON response from Analytics
def process_analytics_report_xml(current_loans):
    rows = current_loans.findall(".//Row")
    items = []
    
    for row in rows:
        item = {
            'library':row.find(".//Column4").text,
            'due_date':row.find(".//Column1").text,
            'title':row.find(".//Column3").text,
            'request_id':row.find(".//Column2").text
        }
            
        items.append(item)
    
    return items




# Request data from Alma Analytics
def get_data_from_analytics(path, apikey, limit):
    headers = {
        'accept': 'application/json',
    }

    params = {
        'path': path,
        'limit': limit, 
        'col_names': 'false',
        'apikey': apikey,
    }

    try: 
        response = requests.get('https://api-eu.hosted.exlibrisgroup.com/almaws/v1/analytics/reports', params=params, headers=headers, timeout=5) 
        response.raise_for_status() 
    except requests.exceptions.HTTPError as errh: 
        print("HTTP Error") 
        sys.exit(1)
    except requests.exceptions.ReadTimeout as errrt:
        print("Network timeout") 
        sys.exit(1) 
    except requests.exceptions.ConnectionError as conerr:
        print("Connection Error")
        sys.exit(1) 
    except requests.exceptions.RequestException as errex:
        print("Request execption")
        sys.exit(1) 

    if response.status_code != 200:
        sys.exit(1)
    else: 
        json_content = response.json()
    
    anies_list = json_content["anies"]
    analyticsData = ET.fromstring(anies_list[0])
    
    
    return analyticsData

# Send an email notification containing a list of soon-to-be overdue ILL items
def send_notification_email(email_address,title_list):

    email = EmailSender(host="localhost", port=0)

    
    email.send(
        subject="Erääntyviä kaukolainoja / Interlibrary loans soon to be overdue",
        sender="kaukopalvelu@kirjasto.fi",
        receivers = email_address,
        text=
    """Hei,

Tämä on ennakkoilmoitus viikon kuluessa erääntymässä olevista kaukolainoista.

Lainat saa uusittua sähköpostitse osoitteesta kaukopalvelu@kirjasto.fi.

---

Hello,

The following interlibrary loans are overdue within next seven days.
To renew, please send an email to ill@library.

{% for title in title_list %}
{{title}}
{% endfor %}

Terveisin / Sincerely

Kaukopalvelu / Interlibrary Services

        
""",
        body_params={
            'title_list': title_list,
            'email_address': email_address
        
        }
    )
    print("Sent notification email to " + email_address)

# Retrieve all RS partners from Alma
partners = alma.partners.get(all_records = True)

# Create a dict where partner name is a key and email address is the value
emails = {}
for partner in partners["partner"]:
    partner_details = partner["partner_details"]
    profile_type = {partner_details["profile_details"]["profile_type"]}
    if profile_type == {"EMAIL"}:
        emails[partner_details["name"]] = partner_details["profile_details"]["email_details"]["email"]

# Retrieve all ILL loans from Alma using an Analytics report       
current_loans = get_data_from_analytics('/shared/your-analytics-report-path-here/GetLendingDueDatesAPI', config["analytics"]["api_key"], '1000')


current_loans = process_analytics_report_xml(current_loans)

# Check if there are any loans soon to be overdue, if not, terminate the script
if len(current_loans)>=1:
    current_loans = pd.DataFrame.from_dict(current_loans)
else:
    sys.exit(0)


# Create a list of RS partners which currently have loans to notify about.
libraries_with_current_loans = current_loans["library"]
libraries_with_current_loans.drop_duplicates(keep='first', inplace=True)


# For every library create list of items and send a notification email containing a list of items 
# and their external ids and due dates
# Between emails, wait 5 seconds.
title_list = []
date_format = '%Y-%m-%d'

for library in libraries_with_current_loans:
    time.sleep(5)
    title_list = []
    items_to_notify = current_loans[current_loans.library == library]
    email_address = emails.get(library)
    items_to_notify = items_to_notify.to_dict("records")
    for item in items_to_notify:
        title = item.get("title")
        due_date = item.get("due_date")
        request_id = item.get("request_id")
        due_date = datetime.strptime(due_date, date_format).strftime('%-d.%-m.%Y')
        title_list.append((due_date + " - " + title + " (" + request_id + ")").strip())
    send_notification_email(email_address,title_list)

    







