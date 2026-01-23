import streamlit as st
import pandas as pd
import requests
import json
import plotly.express as px

##### GENERAL FUNCTIONS
@st.cache_data
def create_df(url):
    response = requests.get(url)
    try:
        json_data = json.loads(response.text)
        return pd.DataFrame(json_data['values'], columns=json_data['fields'])
    except Exception as e:
        print("Error: ",e)



wrc_dict = {"Monte Carlo": [703, 635],
            "Sweden": [704, 636],
            "Kenya": [705, 637],
            }

#st.write("MC: 703, 635")

options = ["Monte Carlo", "Sweden", "Kenya"]
selection = st.pills("Rallies", options, selection_mode="single")


if selection:

    rally = wrc_dict[selection][0]
    event = wrc_dict[selection][1]
    title = selection

# rally = st.text_input("Insert rally code") #rally_dict[rally_name][1]
# event =  st.text_input("Insert event code") #rally_dict[rally_name][0]
# title = st.text_input("Insert rally name (if needed)")

    st.title(title)

    ## STAGES
    @st.cache_data
    def get_stages(url):
        df = pd.DataFrame(json.loads(requests.get(url).text))
        return {code: [stage_id, name, status] for code, stage_id, name, status in zip(df["code"], df["stageId"], df["name"], df["status"])}

    url_stages = f'https://p-p.redbull.com/rb-wrccom-lintegration-yv-prod/api/events/{event}/stages.json'


    stage_dict = get_stages(url_stages)


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
        # Cleaning elapsed duration
        df_stage["elapsedDuration"] = df_stage["elapsedDuration"].fillna("00:00:00").apply(lambda x: x[3:11])
        # Creating columns with the stage (SS*)
        df_stage["stage"] = stage
        # Joining column with the name of the driver
        df_stage = df_stage.merge(drivers_clean, on="entryId", how="left")
        df_stage = df_stage.merge(df_overall[["entryId", "diffFirstOverall"]], on="entryId", how="left")
        # Creating a new df with only necessary columns
        df_stage_clean = df_stage[["driver", "elapsedDuration", "diffFirst", "diffPrev", "stage", "diffFirstOverall"]]

        return df_stage_clean, df_overall_clean

    if st.button("Refresh data", type="primary"):
        st.cache_data.clear()

    all_stages = pd.DataFrame()
    all_overall = pd.DataFrame()
    for stage, (stage_id, name, status) in stage_dict.items():
        if status != "ToRun":
            url_stage = f'https://p-p.redbull.com/rb-wrccom-lintegration-yv-prod/api/events/{event}/stages/{stage_id}/stagetimes.json?rallyId={rally}&championshipId=287&priority=P1'
            url_overall = f'https://p-p.redbull.com/rb-wrccom-lintegration-yv-prod/api/events/{event}/stages/{stage_id}/results.json?rallyId={rally}&championshipId=287&priority=P1'
                
            df_stage_clean, df_overall_clean = get_times(url_stage, url_overall)
            
        else:
            continue

        all_stages = pd.concat((all_stages, df_stage_clean))
        all_overall = pd.concat((all_overall, df_overall_clean))


    ### GRÁFICOS


    tab3, tab4 = st.tabs(["Overall chart", "Stage chart"])

    with tab3:
        fig = px.line(all_overall, x="stage", y="diffFirstOverall", color="driver", markers=True)

        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
        
    with tab4:
        fig2 = px.line(all_stages, x="stage", y="diffFirst", color="driver", markers=True)

        st.plotly_chart(fig2, theme="streamlit", use_container_width=True)




    ### TABELAS 

    # Select box -> Selects between the available stages (from the stage dict created above on Stages section)
    rally_stage = st.selectbox(
        "Select Stage:",
        (stage_dict.keys()),
    )

    # Creates a variable with the stage id of the selected stage
    stage_id = stage_dict[rally_stage][0]


    # Shows the table of the selected stage

    tab1, tab2 = st.tabs(["Stage time", "Overall"])

    with tab1:
        st.header("Stage time")
        st.dataframe(all_stages.drop(columns="stage")[all_stages["stage"] == rally_stage])
    with tab2:
        st.header("Overall")
        st.dataframe(all_overall.drop(columns="stage")[all_overall["stage"] == rally_stage])
else:
    st.write("Choose a rally to start")
