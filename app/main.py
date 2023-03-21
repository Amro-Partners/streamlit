import times
#from streamlit_autorefresh import st_autorefresh
import streamlit as st
from datetime import timedelta
import config as cnf
import firebase as fb
import heatmaps as hmap
import charts as cha
import experiments as exp
import consumption as cons
import warnings

warnings.filterwarnings('ignore')
st.set_page_config(layout="wide")


# reboot the web app every midnight (UTC timezone) for up to 365 times
#count = st_autorefresh(interval=times.milliseconds_until_midnight(), limit=365, key="fizzbuzzcounter")


def _line_space(cols_list, lines_list):
    for col, lines in zip(cols_list, lines_list):
        for i in range(lines):
            col.text("")


def set_homepage():
    print('*************** last_cache_date:', times.last_cache_date())
    if times.utc_now().strftime('%Y-%m-%d') != times.last_cache_date():
        st.cache_data.clear()
        st.cache_resource.clear()

    st.header('TEMPERATURE MONITORING DASHBOARD')
    st.caption(f'Version {cnf.app_version}, release data: {cnf.release_date}')

    _line_space([st], [1])
    tabs = st.tabs(cnf.tabs)
    tab_consumpt, tab_rooms_hmaps, tab_rooms_charts, tab_AHU_charts, tab_exper, tab_occup, tab_water = tabs
    tab_occup.header("This page is not ready yet.")
    tab_water.header("This page is not ready yet.")
    _line_space(tabs, [3] * len(tabs))
    
    col1_rooms_hmaps, _, col2_rooms_hmaps, _ = tab_rooms_hmaps.columns(cnf.tabs_space)
    col1_rooms_charts, _, col2_rooms_charts, _ = tab_rooms_charts.columns(cnf.tabs_space)
    col1_AHU_charts, _, col2_AHU_charts, _ = tab_AHU_charts.columns(cnf.tabs_space)
    col1_consumpt, _,  col2_consumpt, _ = tab_consumpt.columns(cnf.tabs_space)
    col1_exper, _, col2_exper, _ = tab_exper.columns(cnf.tabs_space)

    (tab_rooms_hmaps_building_param, tab_rooms_hmaps_data_param,
     tab_rooms_hmaps_time_param, tab_rooms_hmaps_agg_param,
     tab_rooms_hmaps_raw_data) = hmap.set_params_heatmaps(col1_rooms_hmaps, col2_rooms_hmaps)

    (tab_rooms_charts_building_param, tab_rooms_charts_floor_param,
     tab_rooms_charts_room_param, tab_rooms_charts_raw_data) = cha.set_params_room_charts(col1_rooms_charts, col2_rooms_charts)

    (tab_ahu_charts_building_param, tab_ahu_charts_ahu_param,
     tab_ahu_charts_raw_data) = cha.set_params_ahu_charts(col1_AHU_charts, col2_AHU_charts)

    (tab_consumpt_building_param, tab_consumpt_time_param,
     tab_consumpt_agg_param, tab_consumpt_metric_param,
     tab_consumpt_data_param, tab_consumpt_raw_data) = cons.set_params_consumpt(col1_consumpt, col2_consumpt)

    (tab_exper_exp_param, tab_exper_metric_param, 
     tab_exper_agg_param, tab_exper_raw_data) = exp.set_params_exp(col1_exper, col2_exper)

    return (col2_rooms_hmaps, tab_rooms_hmaps_building_param, tab_rooms_hmaps_data_param, tab_rooms_hmaps_time_param, tab_rooms_hmaps_agg_param,
            col2_rooms_charts, tab_rooms_charts_building_param, tab_rooms_charts_floor_param, tab_rooms_charts_room_param,
            col2_AHU_charts, tab_ahu_charts_building_param, tab_ahu_charts_ahu_param,
            col2_consumpt, tab_consumpt_building_param, tab_consumpt_time_param, tab_consumpt_agg_param, tab_consumpt_metric_param, tab_consumpt_data_param,
            col2_exper, tab_exper_exp_param, tab_exper_metric_param, tab_exper_agg_param)


@st.cache_resource(show_spinner=False)
def read_files_in_loop(file_prefix, start_date, end_date, _storage_bucket):
    list_of_data = []
    for date in times.daterange(start_date, end_date):
        times.log(f'loading file {file_prefix}{date.strftime("%Y/%m/%d")}')
        list_of_data.append(fb.read_and_unpickle(f'{file_prefix}{date.strftime("%Y/%m/%d")}', _storage_bucket))
    return list_of_data


def main():
    date_yesterday = (times.utc_now() - timedelta(days=1))
    firestore_client, storage_bucket = fb.get_db_from_firebase_key(cnf.storage_bucket)

    (col2_rooms_hmaps, tab_rooms_hmaps_building_param, tab_rooms_hmaps_data_param, tab_rooms_hmaps_time_param, tab_rooms_hmaps_agg_param,
     col2_rooms_charts, tab_rooms_charts_building_param, tab_rooms_charts_floor_param, tab_rooms_charts_room_param,
     col2_AHU_charts, tab_ahu_charts_building_param, tab_ahu_charts_ahu_param,
     col2_consumpt, tab_consumpt_building_param, tab_consumpt_time_param, tab_consumpt_agg_param, tab_consumpt_metric_param, tab_consumpt_data_param,
     col2_exper, tab_exper_exp_param, tab_exper_metric_param, tab_exper_agg_param) = set_homepage()  # Get choice of building

    # # consumption
    # cons_df = cons.consumption_summary(firestore_client, tab_consumpt_building_param,
    #                                    tab_consumpt_time_param, tab_consumpt_agg_param)
    # cons_df_metric = cons.convert_metric(cons_df.copy(), tab_consumpt_metric_param)
    # if 'consump_raw_data' in st.session_state and st.session_state.consump_raw_data:
    #     col2_consumpt.dataframe(cons_df_metric, use_container_width=True)
    # else:
    #     chart = cons.chart_df(cons_df_metric, tab_consumpt_data_param, tab_consumpt_agg_param, tab_consumpt_metric_param)
    #     col2_consumpt.altair_chart(chart.interactive(), use_container_width=True)


    # # Heatmaps
    # hmp_dict structure: {[building_param, data_param, agg_param] -> collect_name  -> collect_title else rooms_title -> df of the collection and parameter}
    times.log(f'loading file heatmaps/{date_yesterday.strftime("%Y/%m/%d")}')
    hmp_dict = fb.read_and_unpickle(f'heatmaps/{date_yesterday.strftime("%Y/%m/%d")}', storage_bucket)
    hmp_dict_vals = hmp_dict[tab_rooms_hmaps_building_param, tab_rooms_hmaps_data_param, tab_rooms_hmaps_agg_param].values()
    if all(not d for d in hmp_dict_vals):
        col2_rooms_hmaps.subheader('Sorry. This data is not available for the site.')
    else:
        for collection_df in hmp_dict[tab_rooms_hmaps_building_param, tab_rooms_hmaps_data_param, tab_rooms_hmaps_agg_param].values():
            hmap.run_plots_heatmaps(collection_df, tab_rooms_hmaps_building_param, tab_rooms_hmaps_data_param, tab_rooms_hmaps_time_param, tab_rooms_hmaps_agg_param, col2_rooms_hmaps)

    # # Room charts
    # # charts_dict structure: {building_param -> floor_param or collection title -> room --> df of all params}
    # # TODO: move the below loops and concatenation into transfer process
    #
    # #rooms_list_of_dicts = read_files_in_loop(date_yesterday, 'charts/rooms/', 29, storage_bucket)
    # rooms_list_of_dicts = read_files_in_loop('charts/rooms/',
    #                                                  (times.utc_now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0),
    #                                                  (times.utc_now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
    #                                                  storage_bucket)
    #
    # rooms_dict_of_dfs = cha.get_rooms_dict_of_dfs(rooms_list_of_dicts, tab_rooms_charts_building_param, tab_rooms_charts_floor_param)
    # cha.run_flow_charts(rooms_dict_of_dfs[tab_rooms_charts_room_param],
    #                     st.session_state.chart_rooms_raw_data,
    #                     cnf.sites_dict[tab_ahu_charts_building_param]['rooms_chart_cols'], col2_rooms_charts)
    #
    # # AHU charts
    # # charts_dict structure: {building_param -> ventilation unit (e.g. CL01) --> df of all params}
    # # TODO: move the below loops and concatenation into transfer process
    # ahu_list_of_dicts = read_files_in_loop('charts/ahu/',
    #                                               (times.utc_now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0),
    #                                               (times.utc_now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
    #                                               storage_bucket)
    #
    # ahu_dict_of_dfs = cha.get_ahu_dict_of_dfs(ahu_list_of_dicts, tab_ahu_charts_building_param)
    # cha.run_flow_charts(ahu_dict_of_dfs[tab_ahu_charts_ahu_param],
    #                     st.session_state.chart_ahu_raw_data,
    #                     cnf.sites_dict[tab_ahu_charts_building_param]['AHU_chart_cols'], col2_AHU_charts)
    #
    # # expers
    # # exp_dict structure: {building_param -> floor_param or collection title -> room --> df of all params}
    # # TODO: ince we move to BQ enable start_date longer than X days
    # start_date = (cnf.exp_dict[tab_exper_exp_param]['start_exp_date_utc']
    #               - timedelta(days=cnf.exp_dict[tab_exper_exp_param]['calibration_days']))
    # end_date = min(times.utc_now(), cnf.exp_dict[tab_exper_exp_param]['end_exp_date_utc'])
    # exp_list_of_dicts = read_files_in_loop('experiments/rooms/', start_date, end_date, storage_bucket)
    # summary_dict = exp.get_summary_dict(exp_list_of_dicts, tab_exper_exp_param)
    # test_dict = summary_dict[cnf.test_group]
    # control_dict = summary_dict[cnf.control_group]
    # if (len(control_dict['summary avg post']) == 0) or (len(test_dict['summary avg post']) == 0):
    #     col2_exper.header("Not enough data to show results yet.")
    # else:
    #     # get selected metric summarised in a compact df
    #     metric_df = exp.get_selected_metric_df(test_dict, control_dict, tab_exper_exp_param,
    #                                            tab_exper_metric_param, tab_exper_agg_param)
    #     if 'exp_raw_data' in st.session_state and st.session_state.exp_raw_data:
    #         col2_exper.dataframe(metric_df, use_container_width=True)
    #     else:
    #         chart = exp.chart_df(metric_df, tab_exper_exp_param, tab_exper_metric_param)
    #         col2_exper.altair_chart(chart.interactive(), use_container_width=True)
    #         exp.show_summary_tables(test_dict, control_dict, col2_exper, tab_exper_exp_param)


main()


