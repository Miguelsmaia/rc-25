import streamlit as st
import pandas as pd
import requests
import json

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

## STAGES Winners


