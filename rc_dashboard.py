import streamlit as st
import pandas as pd
import requests
import json
import plotly.express as px

st.html("""
    <style>
        .stMainBlockContainer {
            max-width:65rem;
        }
    </style>
    """
)

##### GENERAL FUNCTIONS
@st.cache_data
def create_df(url):
    response = requests.get(url)
    try:
        json_data = json.loads(response.text)
        return pd.DataFrame(json_data['values'], columns=json_data['fields'])
    except Exception as e:
        print("Error: ",e)


                ##### INTRO INDO ##########

## GET CHAMPIONSHIP ENTRIES (DRIVERS AND TEAMS)

@st.cache_data
def get_championship_entries():
    url_entries = f"https://p-p.redbull.com/rb-wrccom-lintegration-yv-prod/api/championship-detail.json?championshipId=333&seasonId={47}"
    championship_entries = requests.get(url_entries).json()
    return championship_entries

championship_entries = get_championship_entries()

entries_dict = {entry["championshipEntryId"]: [f'{entry["fieldOne"]} {entry["fieldTwo"]}',
                                               entry["fieldFour"]] for entry in championship_entries["championshipEntries"]}




#### GET OVERALL RESULTS (FOR POINTS AND POSITIONS)

# Function to get overall results dataframe
@st.cache_data
def get_champ_overall(entries_dict=entries_dict):
    champ_overall_url = "https://p-p.redbull.com/rb-wrccom-lintegration-yv-prod/api/championship-overall-results.json?championshipId=333&seasonId=47"
    champ_overall = requests.get(champ_overall_url).json()
    # Creating dataframe with overall results
    champ_overall_df = pd.DataFrame(champ_overall["entryResults"])
    # Keeping only necessary columns
    champ_overall_df = champ_overall_df[["championshipEntryId", "overallPosition", "overallPoints"]].copy()

    # Adding driver names to the dataframe (based on the entries_dict created before)
    champ_overall_df["driverName"] = champ_overall_df["championshipEntryId"].apply(lambda x : entries_dict[x][0])
    champ_overall_df = champ_overall_df.sort_values("overallPosition")
    return champ_overall_df

# Get championship overall results dataframe 
champ_overall_df = get_champ_overall()

st.title("WRC DASHBOARD")
st.subheader("2026 Season")

col1, col2, col3 = st.columns(3)
col1.metric("POS 1", champ_overall_df.iloc[0]["driverName"], champ_overall_df.iloc[0]["overallPoints"], delta_color="off", delta_arrow ="off")
col2.metric("POS 2", champ_overall_df.iloc[1]["driverName"], champ_overall_df.iloc[1]["overallPoints"], delta_color="off", delta_arrow ="off")
col3.metric("POS 3", champ_overall_df.iloc[2]["driverName"], champ_overall_df.iloc[2]["overallPoints"], delta_color="off", delta_arrow ="off")

                    ##### DATA DASHBOARD ##############

wrc_dict = {"Monte Carlo": [703, 635],
            "Sweden": [704, 636],
            "Kenya": [705, 637],
            "Croatia": [706, 638],
            "Islas Canarias": [707, 639],
            "Portugal": [709, 640],
            "Japan": [710, 641],
            "Greece": [711, 642],
            "Estonia": [712, 643]
            }

#st.write("MC: 703, 635")

options = ["Monte Carlo", "Sweden", "Kenya","Croatia", "Islas Canarias", "Portugal", "Japan", "Greece", "Estonia"]
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



    ## CARDS

    # Getting last stage info
    last_stage = all_overall["stage"].iloc[-1]


    # Creating cards for rally leader
    # Getting rally leader info
    rally_leader = all_overall[all_overall["stage"] == last_stage].sort_values("diffFirstOverall").iloc[0]
    st.subheader("Rally Leader")
    col1, col2, col3 = st.columns(3)
    col1.metric("Driver", rally_leader["driver"])
    col2.metric("Total Time", rally_leader["totalTime"])
    col3.metric("Diff to 2nd", all_overall[all_overall["stage"] == last_stage].sort_values("diffFirstOverall").iloc[1]["diffFirstOverall"])


    # Creating horizontal chart with stages winners
    st.subheader("Stage Winners")
    # Getting stage winners
    stage_winners = all_stages.groupby(by="stage").first().reset_index()[["stage", "driver"]]
    # Sorting stages in the correct order
    stage_winners["stage_number"] = stage_winners["stage"].apply(lambda x: int(x.replace("SS", ""))).astype(int)
    stage_winners = stage_winners.sort_values("stage_number")
    # Creating pivot table to show stage winners in horizontal format
    stage_winners_pivot = stage_winners.pivot_table(index=None, columns="stage_number", values="driver", aggfunc='first')
    stage_winners_pivot.columns = [f'SS{col}' for col in stage_winners_pivot.columns]
    st.dataframe(stage_winners_pivot) 



    ## GRÁFICOS

    st.subheader("Charts")

    # Add slider to choose drivers count
    n_drivers = st.slider("How many drivers on compact chart? ", 0, all_overall["driver"].nunique(), 4)


    tab5, tab3, tab4 = st.tabs(["Compact overall chart", "Overall chart", "Stage chart"])

   


    with tab3:
        fig = px.line(all_overall, x="stage", y="diffFirstOverall", color="driver")

        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
        
    with tab4:
        fig2 = px.line(all_stages, x="stage", y="diffFirst", color="driver")

        st.plotly_chart(fig2, theme="streamlit", use_container_width=True)
    
    with tab5:
        last_stage = all_overall[all_overall["stage"] == last_stage][["stage", "driver", "totalTime", "diffFirstOverall"]].sort_values("diffFirstOverall")
        compact_overall = all_overall[all_overall["driver"].isin(last_stage["driver"].iloc[:n_drivers])][["stage", "driver", "totalTime", "diffFirstOverall"]]
        fig3 = px.line(compact_overall, x="stage", y="diffFirstOverall", color="driver")

        st.plotly_chart(fig3, theme="streamlit", use_container_width=True)




    ### TABELAS 
    st.subheader("Tables")

    # Getting index of last stage for selectbox default value
    last_stage_index = len(all_overall["stage"].unique()) -1

    # Select box -> Selects between the available stages (from the stage dict created above on Stages section)
    rally_stage = st.selectbox(
        "Select Stage:",
        (stage_dict.keys()), index=last_stage_index
    )

    # Creates a variable with the stage id of the selected stage
    stage_id = stage_dict[rally_stage][0]


    # Shows the table of the selected stage

    tab2, tab1  = st.tabs(["Overall", "Stage time"])

    with tab1:
        st.dataframe(all_stages.drop(columns="stage")[all_stages["stage"] == rally_stage])
    with tab2:
        #st.header("Overall")
        st.dataframe(all_overall.drop(columns="stage")[all_overall["stage"] == rally_stage])
else:
    st.write("Choose a rally to start")
