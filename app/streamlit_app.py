import times
import os
from streamlit_autorefresh import st_autorefresh
import streamlit as st
from datetime import timedelta
import pandas as pd
import config as cnf
import firebase as fb
import utils
import heatmaps as hmap
import charts as cha
import experiments as exp

st.set_page_config(layout="wide")


# reboot the web app every midnight (UTC timezone) for up to 365 times
count = st_autorefresh(interval=times.milliseconds_until_midnight(), limit=365, key="fizzbuzzcounter")


def set_homepage():
    print('*************** last_cache_date:', times.last_cache_date())
    if times.utc_now().strftime('%Y-%m-%d') != times.last_cache_date():
        st.cache_data.clear()
        st.cache_resource.clear()

    st.header('TEMPERATURE MONITORING DASHBOARD')
    st.caption(f'Version {cnf.app_version}, release data: {cnf.release_date}')

    utils.line_space([st], [1])
    tab1, tab2, tab3 = st.tabs(cnf.tabs)
    utils.line_space([tab1, tab2], [3, 3])
    col11, col12, col13 = tab1.columns([2, 6, 2])
    col21, col22, col23 = tab2.columns([2, 6, 2])
    col31, col32, col33 = tab3.columns([2, 6, 2])
    tab1_building_param, tab1_data_param, tab1_time_param, tab1_agg_param, tab1_raw_data = hmap.set_params_heatmaps(col11, col12)
    tab2_building_param, tab2_floor_param, tab2_room_param, tab2_raw_data = cha.set_params_charts(col21, col22)
    tab3_building_param, tab3_metric_param, tab3_agg_param, tab3_raw_data = exp.set_params_exp(col31, col32)

    return (col12, tab1_building_param, tab1_data_param, tab1_time_param, tab1_agg_param,
            col22, tab2_building_param, tab2_floor_param, tab2_room_param,
            col32, tab3_building_param, tab3_metric_param, tab3_agg_param)


def main():
    date_yesterday = (times.utc_now() - timedelta(days=1))
    firestore_client, storage_bucket = fb.get_db_from_firebase_key(cnf.storage_bucket)

    (col12, tab1_building_param, tab1_data_param, tab1_time_param, tab1_agg_param,
     col22, tab2_building_param, tab2_floor_param, tab2_room_param,
     col32, tab3_building_param, tab3_metric_param, tab3_agg_param) = set_homepage()  # Get choice of building

    # Heatmaps
    tab1_building_dict, tab1_param_dict, tab1_agg_param_dict = utils.get_config_dicts(tab1_building_param,
                                                                                      tab1_data_param, tab1_agg_param)

    # hmp_dict structure: {[building_param, data_param, agg_param] -> collect_name  -> collect_title else rooms_title -> df of the collection and parameter}
    times.log(f'loading file heatmaps/{date_yesterday.strftime("%Y/%m/%d")}')
    hmp_dict = fb.read_and_unpickle(f'heatmaps/{date_yesterday.strftime("%Y/%m/%d")}', storage_bucket)
    hmp_dict_vals = hmp_dict[tab1_building_param, tab1_data_param, tab1_agg_param].values()
    if all(not d for d in hmp_dict_vals):
        col12.subheader('Sorry. This data is not available for the site.')
    else:
        for collection_df in hmp_dict[tab1_building_param, tab1_data_param, tab1_agg_param].values():
            hmap.run_plots_heatmaps(collection_df, tab1_building_param, tab1_data_param, tab1_time_param, tab1_agg_param, col12)

    # # Charts
    # # charts_dict structure: {building_param -> floor_param or collection title -> room --> df of all params}
    # # TODO: move the below loops and concatenation into transfer process
    # charts_list_of_dicts = []
    # for days_back in reversed(range(1, 8)):
    #     date_back = (times.utc_now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
    #     times.log(f'loading file charts/rooms/{date_back}')
    #     charts_list_of_dicts.append(fb.read_and_unpickle(f'charts/rooms/{date_back}', storage_bucket))
    #
    # charts_dict_of_dfs = {}
    # for building_param in [bp for bp in charts_list_of_dicts[0].keys() if bp in cnf.non_test_sites]:
    #     charts_dict_of_dfs[building_param] = {}
    #     for floor_param in charts_list_of_dicts[0][building_param].keys():
    #         charts_dict_of_dfs[building_param][floor_param] = {}
    #         for room_param in charts_list_of_dicts[0][building_param][floor_param].keys():
    #             charts_dict_of_dfs[building_param][floor_param][room_param] = (
    #                 pd.concat([dic[building_param][floor_param][room_param] for dic in charts_list_of_dicts])
    #                 .drop_duplicates())
    #
    # cha.run_flow_charts(charts_dict_of_dfs[tab2_building_param][tab2_floor_param][tab2_room_param], col22)

    # Experiments
    # # exp_dict structure: {building_param -> floor_param or collection title -> room --> df of all params}
    # start_date = (cnf.sites_dict[tab3_building_param]['start_exp_date_utc']
    #               - timedelta(days=cnf.sites_dict[tab3_building_param]['calibration_days']))
    # end_date = min(date_yesterday, cnf.sites_dict[tab3_building_param]['end_exp_date_utc'])
    # exp_list_of_dicts = []
    # for date in times.daterange(start_date, end_date):
    #     times.log(f'loading file experiments/rooms/{date.strftime("%Y/%m/%d")}')
    #     exp_list_of_dicts.append(fb.read_and_unpickle(f'experiments/rooms/{date.strftime("%Y/%m/%d")}', storage_bucket))
    #
    #
    # exp_dict_of_dfs = {}
    # summary_dict = {}
    # for building_param in [bp for bp in exp_list_of_dicts[0].keys() if bp in cnf.test_sites]:
    #     exp_dict_of_dfs[building_param] = {}
    #     for floor_param in exp_list_of_dicts[0][building_param].keys():
    #         exp_dict_of_dfs[building_param][floor_param] = {}
    #         for room_param in exp_list_of_dicts[0][building_param][floor_param].keys():
    #             exp_dict_of_dfs[building_param][floor_param][room_param] = (
    #                 pd.concat([dic[building_param][floor_param][room_param]
    #                            for dic in exp_list_of_dicts]).drop_duplicates())
    #
    #     summary_dict[building_param] = exp.get_exp_summary_dict(building_param, exp_dict_of_dfs[building_param])
    # del exp_dict_of_dfs
    #
    # test_dict = summary_dict[tab3_building_param][cnf.test_group]
    # control_dict = summary_dict[tab3_building_param][cnf.control_group]
    #
    # # get selected metric summarised in a compact df
    # metric_df = exp.get_selected_metric_df(test_dict, control_dict, tab3_building_param, tab3_metric_param,
    #                                        tab3_agg_param)
    # if 'exp_raw_data' in st.session_state and st.session_state.exp_raw_data:
    #     col32.dataframe(metric_df, use_container_width=True)
    # else:
    #     exp.show_summary_tables(test_dict, control_dict, col32, tab3_building_param)
    #     chart = exp.chart_df(metric_df, building_param, tab3_metric_param)
    #     col32.altair_chart(chart.interactive(), use_container_width=True)


main()


