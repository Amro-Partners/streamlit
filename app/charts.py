import rooms
import config as cnf
import plot
import streamlit as st
import pandas as pd


def set_params_room_charts(col1, col2):
    building_param = col1.radio('Select building', cnf.sites_dict, key='chart_building')
    building_dict = cnf.sites_dict[building_param]
    floor_param = col1.radio('Select floor', building_dict['floors_order'], key='chart_floor')
    floor_to_rooms_dict = rooms.get_group_to_rooms_dict(building_dict['rooms_file'], building_dict['floors_col'])
    room_param = col1.selectbox('Select room', sorted(floor_to_rooms_dict[floor_param]), key='chart_room')
    raw_data = col2.checkbox("Show raw data", value=False, key="chart_rooms_raw_data")
    return building_param, floor_param, room_param


def set_params_ahu_charts(col1, col2):
    # TODO: reenable Malaga in building_param
    ahu_sites = {k for k, v in cnf.sites_dict.items() if v.get('AHU_chart_cols')}
    if not ahu_sites:
        return None, None, None
    building_param = col1.radio('Select building', ahu_sites, key='ahu_building')
    building_dict = cnf.sites_dict[building_param]
    ahu_dict = rooms.get_ahu_dict(building_dict['vent_file'])
    ahu_param = col1.radio('Select AHU unit', ahu_dict.keys(), key='ahu_room')
    raw_data = col2.checkbox("Show raw data", value=False, key="chart_ahu_raw_data")
    return building_param, ahu_dict[ahu_param]


def run_flow_charts(df, session_state_raw_data, chart_cols, _col):
    if 'Cooling temperature set point (°C)' in df.columns:
        # TODO: add setpoint mode to transfer and then drop the one that is not active
        df = df.drop(columns=['Cooling temperature set point (°C)'])
    max_datetime = df.timestamp.iloc[-1]
    if session_state_raw_data:
        _col.dataframe(df, use_container_width=True)
    else:
        p = plot.charts(df, max_datetime, chart_cols)
        _col.altair_chart(p.interactive(), use_container_width=True)


@st.cache_data(show_spinner=False, ttl=3600)
def get_rooms_dict_of_dfs(rooms_list_of_dicts, building_param, floor_param):
    rooms_dict_of_dfs = {}
    # for building_param in [bp for bp in rooms_list_of_dicts[0].keys() if bp in cnf.sites_dict]:
    #     rooms_dict_of_dfs[building_param] = {}
    #     for floor_param in rooms_list_of_dicts[0][building_param].keys():
    #         rooms_dict_of_dfs[building_param][floor_param] = {}
    for room_param in rooms_list_of_dicts[0][building_param][floor_param].keys():
        rooms_dict_of_dfs[room_param] = (
            pd.concat([dic[building_param][floor_param][room_param] for dic in rooms_list_of_dicts])
            .drop_duplicates())
    return rooms_dict_of_dfs
