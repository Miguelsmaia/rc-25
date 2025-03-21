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
@st.cache_data
def get_stages(url):
    df = pd.DataFrame(json.loads(requests.get(url).text))
    return {code: [stage_id, name, status] for code, stage_id, name, status in zip(df["code"], df["stageId"], df["name"], df["status"])}

url_stages = f'https://p-p.redbull.com/rb-wrccom-lintegration-yv-prod/api/events/{event}/stages.json'


stage_dict = get_stages(url_stages)

rally_stage = st.selectbox(
    "Select Stage:",
    (stage_dict.keys()),
)

stage_id = stage_dict[rally_stage][0]

## GET DRIVERS INFO

drivers = f'https://p-p.redbull.com/rb-wrccom-lintegration-yv-prod/api/events/{event}/rallies/{rally}/entries.json'
@st.cache_data
def get_drivers(url):
    df = pd.DataFrame(json.loads(requests.get(url).text))
    df_clean = df.loc[df["groupId"] == 152, ["driver", "entryId"]]
    df_clean["driver"] = df["driver"].apply(lambda x: x["abbvName"])
    return {driver: entry_id for driver, entry_id in zip(df_clean["driver"], df_clean["entryId"])}, df_clean

driver_dict, drivers_clean = get_drivers(drivers)

## STAGE AND OVERALL TIMES
@st.cache_data
def get_times(url_stage, url_overall):
    df_stage = pd.DataFrame(json.loads(requests.get(url_stage).text))
    df_overall = pd.DataFrame(json.loads(requests.get(url_overall).text))

    # Cleaning overall table
    # Transforming ms to seconds
    df_overall[["diffFirstOverall", "diffPrevOverall"]] = df_overall[["diffFirstMs", "diffPrevMs"]] / 1000
    # Cleaning time columns by removing "PT"
    df_overall[["stageTime", "penaltyTime", "totalTime", "diffFirst", "diffPrev"]] = df_overall[["stageTime", "penaltyTime", "totalTime", "diffFirst", "diffPrev"]].replace("PT", "", regex=True)
    # Creating columns with the stage (SS*)
    df_overall["stage"] = stage
    # Joining column with the name of the driver
    df_overall = df_overall.merge(drivers_clean, on="entryId", how="left")
    # Creating a new df with only necessary columns
    df_overall_clean = df_overall[["driver", "position", "stageTime", "penaltyTime", "totalTime", "diffFirstOverall", "diffPrevOverall", "stage"]]

    # Cleaning stage table
    # Transforming ms to seconds
    df_stage[["diffFirst", "diffPrev"]] = df_stage[["diffFirstMs", "diffPrevMs"]] / 1000
    # Creating columns with the stage (SS*)
    df_stage["stage"] = stage
    # Joining column with the name of the driver
    df_stage = df_stage.merge(drivers_clean, on="entryId", how="left")
    df_stage = df_stage.merge(df_overall[["entryId", "diffFirstOverall"]], on="entryId", how="left")
    # Creating a new df with only necessary columns
    df_stage_clean = df_stage[["driver", "diffFirst", "diffPrev", "stage", "diffFirstOverall"]]

    return df_stage_clean, df_overall_clean

all_stages = pd.DataFrame()
all_overall = pd.DataFrame()
for stage, (stage_id, name, status) in stage_dict.items():
    if status != "ToRun":
        url_stage = f'https://p-p.redbull.com/rb-wrccom-lintegration-yv-prod/api/events/{event}/stages/{stage_id}/stagetimes.json?rallyId={rally}&championshipId=287&priority=P1'
        url_overall = f'https://p-p.redbull.com/rb-wrccom-lintegration-yv-prod/api/events/{event}/stages/{stage_id}/results.json?rallyId={rally}&championshipId=287&priority=P1'
        
        df_stage_clean, df_overall_clean = get_times(url_stage, url_overall)
            
    all_stages = pd.concat((all_stages, df_stage_clean))
    all_overall = pd.concat((all_overall, df_overall_clean))


tab1, tab2 = st.tabs(["Stage time", "Overall"])

with tab1:
    st.header("Stage time")
    st.dataframe(all_stages[all_stages["stage"] == rally_stage])
with tab2:
    st.header("Overall")
    st.dataframe(all_overall[all_overall["stage"] == rally_stage])


