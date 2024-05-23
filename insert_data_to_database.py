import time
import requests
import datetime
import pandas as pd



url = "pomelo.csv"
dataset = pd.read_csv(url)


# print(dataset)

for i in range(len(dataset)):
    data = {
    "date_price":dataset.date_price[i],
    "date_create": dataset.date_create[i],
    "name": str(dataset.name[i]),
    "minPrice": int(dataset.minPrice[i]),
    "maxPrice": int(dataset.maxPrice[i]),
    "avgPrice": int(dataset.avgPrice[i]),
    "unit": str(dataset.unit[i])
    
    }
    #Sent data to database
    url = 'http://127.0.0.1:5000/save_data'  
    response = requests.post(url, json=data)
    
    # print(data)


