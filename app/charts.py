import rooms
import config as cnf
import plot


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
