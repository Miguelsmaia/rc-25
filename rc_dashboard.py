import streamlit as st
import pandas as pd
import requests
import json


##### GENERAL FUNCTIONS
@st.cache_data
def create_df(url):
    response = requests.get(url)
    try:
        json_data = json.loads(response.text)
        return pd.DataFrame(json_data['values'], columns=json_data['fields'])
    except Exception as e:
        print("Error: ",e)





st.title("WRC Dashboard")

## CALENDAR


year = 2025
url_calendar = f'https://api.wrc.com/content/items?language=en&size=10&type=calendar&filterBy=year%2Bgroup&filter={year}%2BWRC&page=1'

# Get a dataframe with the calendar
@st.cache_data
def calendar(url):
    try:
        response = requests.get(url=url_calendar)
        json_data = json.loads(response.text)
        df = pd.DataFrame(json_data['content'])
        rally_list = {title: [event_id, rally_id] for title, event_id, rally_id in zip(df["title"].to_list(), df["eventId"].to_list(), df["rallyId"].to_list())}
        df = df.drop(columns=['id', 'guid', 'location', 'startDate', 'endDate', 'eventId',
       'rallyId', 'description', 'round', 'cvpSeriesLink', 'sponsor', 'images',
       'season', 'competition', 'asset', '__typename', 'type', 'country',
       'uid', 'seriesUid', 'releaseYear', 'availableOn', 'availableTill', 'championship', 'finishDate',
       'championshipLogo', 'endDateLocal'])
        df["startDateLocal"] = df["startDateLocal"].apply(lambda x: x[:10])
        print("teste")    
        return df, rally_list
    
    except Exception as e:
        print("Error: ",e)



calendar_df, rally_dict = calendar(url_calendar)


rally_name = st.selectbox(
    "Select Rally:",
    (rally_dict.keys()),
)

rally = rally_dict[rally_name][1]
event = rally_dict[rally_name][0]

## STAGES

def get_stages(url):
    df = pd.DataFrame(json.loads(requests.get(url_stages).text))
    return {code: [stage_id, name, status] for code, stage_id, name, status in zip(df["code"], df["stageId"], df["name"], df["status"])}

url_stages = f'https://p-p.redbull.com/rb-wrccom-lintegration-yv-prod/api/events/{event}/stages.json'


stage_dict = get_stages(url_stages)

rally_stage = st.selectbox(
    "Select Stage:",
    (stage_dict.keys()),
)

stage_id = stage_dict[rally_stage][0]



## SPLIT TIMES


