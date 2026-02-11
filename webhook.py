import requests
import json
import datetime


webhook_url = "YOUR_URL_HERE"

def send_webhook(run_time: str, num_runs: int, task_name: str, img):

    if True:

        payload = {
            
        "username": "Loxer's Automation",
        "avatar_url": "https://i.pinimg.com/736x/97/10/48/97104879f559410dcdb09999d1910f2e.jpg",
        "embeds": [
            {
            "title": "Loxer's Automation",
            "description": "",
            "color": 3447003,
            "fields": [
                {
                "name": "🕒 Run Time",
                "value": run_time,
                "inline": True
                },

                {
                "name": "🔁 Total Runs",
                "value": num_runs,
                "inline": True
                },
                {
                "name": "⚙️ Current Task",
                "value": task_name
                }
            ],
            "image": {
                "url": "attachment://screenshot.png",
            },
            "thumbnail": {
                "url": "https://media1.tenor.com/m/m0KNx_D9YKoAAAAC/dio-the-world.gif",
            },
            "footer": {
                "text": f"Loxer's Automation | Run time: {run_time}",
                "icon_url": "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDRlMno0eXBhM2Uyb2hoYzJlYnJ6dW05NWQwdTE0dHd6MW9saXJ3eCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/6UL3rqweR5Y2Jcrnqb/giphy.gif"
            },
            "timestamp": datetime.datetime.utcnow().isoformat()
            }
        ]
        }
        files = {
            "file": ("screenshot.png", img, "image/png")  # name must match attachment:// name
    
        }

        

        response = requests.post(webhook_url, data={"payload_json": json.dumps(payload)}, files=files)
        #print(response.status_code, response.text)
    else:
        print("Error, no wins or losses detected")

