import rooms
import config as cnf
import plot
import times
import firebase as fb
import streamlit as st
import pandas as pd


def set_params_room_charts(col1, col2):
    building_param = col1.radio('Select building', cnf.non_test_sites, key='chart_building')
    building_dict = cnf.sites_dict[building_param]
    floor_param = col1.radio('Select floor', building_dict['floors_order'], key='chart_floor')
    floor_to_rooms_dict = rooms.get_floor_to_rooms_dict(building_dict['rooms_file'], building_dict['floors_col'])
    room_param = col1.selectbox('Select room', sorted(floor_to_rooms_dict[floor_param]), key='chart_room')
    raw_data = col2.checkbox("Show raw data", value=False, key="chart_rooms_raw_data")
    return building_param, floor_param, room_param, raw_data


def set_params_ahu_charts(col1, col2):
    building_param = col1.radio('Select building', cnf.non_test_sites, key='ahu_building')
    building_dict = cnf.sites_dict[building_param]
    ahu_dict = rooms.get_ahu_dict(building_dict['vent_file'])
    ahu_param = col1.radio('Select AHU unit', ahu_dict.keys(), key='ahu_room')
    raw_data = col2.checkbox("Show raw data", value=False, key="chart_ahu_raw_data")
    return building_param, ahu_dict[ahu_param], raw_data


def run_flow_charts(df, session_state_raw_data, chart_cols, _col):
    df = df.sort_index()
    if 'Cooling temperature set point (°C)' in df.columns:
        # TODO: add setpoint mode to transfer and then drop the one that is not active
        df = df.drop(columns=['Cooling temperature set point (°C)'])
    max_datetime = df.index[-1]
    if session_state_raw_data:
        _col.dataframe(df, use_container_width=True)
    else:
        _col.altair_chart(plot.charts(df, max_datetime, chart_cols).interactive(), use_container_width=True)


@st.cache_data(show_spinner=False)
def get_ahu_dict_of_dfs(ahu_list_of_dicts):
    charts_dict_of_dfs = {}
    for building_param in [bp for bp in ahu_list_of_dicts[0].keys() if bp in cnf.non_test_sites]:
        charts_dict_of_dfs[building_param] = {}
        for ahu_unit in ahu_list_of_dicts[0][building_param].keys():
            charts_dict_of_dfs[building_param][ahu_unit] = (
                    pd.concat([dic[building_param][ahu_unit] for dic in ahu_list_of_dicts])
                    .drop_duplicates())
    return charts_dict_of_dfs


@st.cache_data(show_spinner=False)
def get_rooms_dict_of_dfs(rooms_list_of_dicts):
    rooms_dict_of_dfs = {}
    for building_param in [bp for bp in rooms_list_of_dicts[0].keys() if bp in cnf.non_test_sites]:
        rooms_dict_of_dfs[building_param] = {}
        for floor_param in rooms_list_of_dicts[0][building_param].keys():
            rooms_dict_of_dfs[building_param][floor_param] = {}
            for room_param in rooms_list_of_dicts[0][building_param][floor_param].keys():
                rooms_dict_of_dfs[building_param][floor_param][room_param] = (
                    pd.concat([dic[building_param][floor_param][room_param] for dic in rooms_list_of_dicts])
                    .drop_duplicates())
    return rooms_dict_of_dfs
