import times
#from streamlit_autorefresh import st_autorefresh
import streamlit as st
from datetime import timedelta
import config as cnf
import bigquery as bq
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

    (tab_hmaps_building_param, tab_hmaps_data_param,
     tab_hmaps_time_param, tab_hmaps_agg_param) = hmap.set_params_heatmaps(col1_rooms_hmaps, col2_rooms_hmaps)

    (tab_rooms_charts_building_param, tab_rooms_charts_floor_param,
     tab_rooms_charts_room_param) = cha.set_params_room_charts(col1_rooms_charts, col2_rooms_charts)

    (tab_ahu_charts_building_param, tab_ahu_charts_ahu_param) = cha.set_params_ahu_charts(col1_AHU_charts, col2_AHU_charts)

    (tab_consumpt_building_param, tab_consumpt_time_param,
     tab_consumpt_agg_param, tab_consumpt_metric_param, tab_consumpt_data_param) = cons.set_params_consumpt(col1_consumpt, col2_consumpt)

    (tab_exper_exp_param, tab_exper_metric_param, 
     tab_exper_agg_param) = exp.set_params_exp(col1_exper, col2_exper)

    return (col2_rooms_hmaps, tab_hmaps_building_param, tab_hmaps_data_param, tab_hmaps_time_param, tab_hmaps_agg_param,
            col2_rooms_charts, tab_rooms_charts_building_param, tab_rooms_charts_floor_param, tab_rooms_charts_room_param,
            col2_AHU_charts, tab_ahu_charts_building_param, tab_ahu_charts_ahu_param,
            col2_consumpt, tab_consumpt_building_param, tab_consumpt_time_param, tab_consumpt_agg_param, tab_consumpt_metric_param, tab_consumpt_data_param,
            col2_exper, tab_exper_exp_param, tab_exper_metric_param, tab_exper_agg_param)


def main():
    date_yesterday = (times.utc_now() - timedelta(days=1))
    date_last_week = (times.utc_now() - timedelta(days=7))

    bq_client = bq.get_bq_client_from_toml_key(cnf.bq_project)

    (col2_rooms_hmaps, tab_hmaps_building_param, tab_hmaps_data_param, tab_hmaps_time_param, tab_hmaps_agg_param,
     col2_rooms_charts, tab_rooms_charts_building_param, tab_rooms_charts_floor_param, tab_rooms_charts_room_param,
     col2_AHU_charts, tab_ahu_charts_building_param, tab_ahu_charts_ahu_param,
     col2_consumpt, tab_consumpt_building_param, tab_consumpt_time_param, tab_consumpt_agg_param, tab_consumpt_metric_param, tab_consumpt_data_param,
     col2_exper, tab_exper_exp_param, tab_exper_metric_param, tab_exper_agg_param) = set_homepage()  # Get choice of building

    # consumption
    times.log(f'loading consumption data between {tab_consumpt_time_param[0].strftime("%Y-%m-%d")} AND {tab_consumpt_time_param[1].strftime("%Y-%m-%d")}')
    agg_param_dict = cnf.consumpt_agg_param_dict[tab_consumpt_agg_param]
    site_dict = cnf.sites_dict[tab_consumpt_building_param]

    if agg_param_dict['aggregation_bq'] == "DATE":
        agg_func = f'''EXTRACT({agg_param_dict['aggregation_bq']} FROM timestamp AT TIME ZONE '{site_dict["time_zone"]}')'''
    elif agg_param_dict['aggregation_bq'] == "WEEK":
        agg_func = f'''DATE(DATE_TRUNC(timestamp, WEEK(MONDAY)))'''
    elif agg_param_dict['aggregation_bq'] == "MONTH":
        agg_func = f'''FORMAT_TIMESTAMP('%Y-%m', timestamp)'''
    elif agg_param_dict['aggregation_bq'] == "HOUR":
        agg_func = f'''FORMAT_TIMESTAMP('%H', timestamp)'''

    query = f'''
        SELECT
            {agg_func} AS `{agg_param_dict['aggregation_field_name']}`,
            data_param,
             CASE
                WHEN data_param like "%temperature%" THEN AVG(value)
                ELSE SUM(value)
            END AS aggregate_value
        FROM {cnf.table_consumption}
        WHERE
            Date(timestamp, "{site_dict['time_zone']}") BETWEEN  "{tab_consumpt_time_param[0].strftime("%Y-%m-%d")}"
                AND "{tab_consumpt_time_param[1].strftime("%Y-%m-%d")}"
            AND building = "{tab_consumpt_building_param}"
            AND data_param IN {'('+ ','.join([f'"{t}"' for t in tab_consumpt_data_param])+')'}
        GROUP BY
            {agg_func},
            data_param
    '''
    cons_df = bq.send_bq_query(bq_client, query)
    cons_df = cons_df.pivot(index=agg_param_dict['aggregation_field_name'], columns='data_param', values='aggregate_value')
    cons_df['Building avg. consumption 2022'] = cons_df['Building energy consumption'].mean() # 7/6 * agg_param_dict['building_consump_intensity_target'] * site_dict['area_m2']  ####################
    cons_df['Building target consumption 2023'] = agg_param_dict['building_consump_intensity_target'] * site_dict['area_m2']
    cons_df_metric = cons.convert_metric(cons_df, tab_consumpt_metric_param, site_dict)
    if 'consump_raw_data' in st.session_state and st.session_state.consump_raw_data:
        col2_consumpt.dataframe(cons_df_metric, use_container_width=True)
    else:
        chart = cons.chart_df(cons_df_metric, tab_consumpt_agg_param, tab_consumpt_metric_param)
        col2_consumpt.altair_chart(chart.interactive(), use_container_width=True)


    # Heatmaps
    times.log(f'loading file heatmaps between {(times.utc_now() - timedelta(days=7)).strftime("%Y-%m-%d")} AND {date_yesterday.strftime("%Y-%m-%d")}')
    site_dict = cnf.sites_dict[tab_hmaps_building_param]
    param_dict = cnf.data_param_dict[tab_hmaps_data_param]
    agg_param_dict = cnf.hmps_agg_param_dict[tab_hmaps_agg_param]
    agg_func = 'MAX(parameter_value) - MIN(parameter_value)' if param_dict.get('cumulative') else 'AVG(parameter_value)'

    query = f'''
        SELECT
            EXTRACT({agg_param_dict['aggregation_bq']} FROM timestamp AT TIME ZONE "{site_dict['time_zone']}") AS `{agg_param_dict['aggregation_field_name']}`,
            floor,
            room,
            {agg_func} AS parameter_value
        FROM {cnf.table_heatmaps}
        WHERE
            Date(timestamp, "{site_dict['time_zone']}") BETWEEN "{tab_hmaps_time_param[0].strftime("%Y-%m-%d")}"
                AND "{tab_hmaps_time_param[1].strftime("%Y-%m-%d")}"
            AND building = "{tab_hmaps_building_param}"
            AND data_param = "{param_dict['bq_field']}"
        GROUP BY
            EXTRACT({agg_param_dict['aggregation_bq']} FROM timestamp AT TIME ZONE "{site_dict['time_zone']}"),
            floor,
            room
    '''
    hmp_df = bq.send_bq_query(bq_client, query)
    for floor in site_dict['floors_order']:
        hmp_df_floor = hmap.pivot_df(hmp_df, floor, agg_param_dict['aggregation_field_name'])
        hmap.plot_heatmap(df=hmp_df_floor,
                          fmt=param_dict['fmt'],
                          title=floor,
                          xlabel=agg_param_dict['aggregation_field_name'],
                          ylabel="Rooms",
                          scale=cnf.hmaps_figure_memory_scale,
                          col=col2_rooms_hmaps)

    # Room charts
    # charts_dict structure: {building_param -> floor_param or collection title -> room --> df of all params}
    # TODO: move the below loops and concatenation into transfer process
    site_dict = cnf.sites_dict[tab_rooms_charts_building_param]
    where_cond = f''' WHERE
        Date(timestamp, "{site_dict['time_zone']}") BETWEEN "{date_last_week.strftime("%Y-%m-%d")}" AND "{date_yesterday.strftime("%Y-%m-%d")}"
        AND building = "{tab_rooms_charts_building_param}"
        AND room = "{tab_rooms_charts_room_param}"
    '''
    rooms_chart_df = bq.read_bq(bq_client, cnf.table_charts_rooms, where_cond)
    cha.run_flow_charts(rooms_chart_df,
                        st.session_state.chart_rooms_raw_data,
                        site_dict['rooms_chart_cols'], col2_rooms_charts)

    # AHU charts
    # charts_dict structure: {building_param -> ventilation unit (e.g. CL01) --> df of all params}
    # TODO: move the below loops and concatenation into transfer process
    site_dict = cnf.sites_dict[tab_ahu_charts_building_param]
    where_cond = f''' WHERE
        Date(timestamp, "{site_dict['time_zone']}") BETWEEN "{date_last_week.strftime("%Y-%m-%d")}" AND "{date_yesterday.strftime("%Y-%m-%d")}"
        AND building = "{tab_ahu_charts_building_param}"
        AND ahu = "{tab_ahu_charts_ahu_param}"
    '''
    ahu_chart_df = bq.read_bq(bq_client, cnf.table_charts_ahus, where_cond)
    cha.run_flow_charts(ahu_chart_df,
                        st.session_state.chart_ahu_raw_data,
                        site_dict['AHU_chart_cols'], col2_AHU_charts)

    # experiments
    # exp_dict structure: {building_param -> floor_param or collection title -> room --> df of all params}
    # TODO: since we move to BQ enable start_date longer than X days
    start_date = (cnf.exp_dict[tab_exper_exp_param]['start_exp_date_utc']
                  - timedelta(days=cnf.exp_dict[tab_exper_exp_param]['calibration_days']))
    end_date = min(times.utc_now(), cnf.exp_dict[tab_exper_exp_param]['end_exp_date_utc'])
    query = f"""
        select *
        from
        (
        SELECT DATETIME_TRUNC(DATETIME(timestamp, "{cnf.exp_dict[tab_exper_exp_param]['time_zone']}"), HOUR) as timestamp,
              floor,
              avg(average_room_temperature) as average_room_temperature,
              avg(cooling_temperature_setpoint) as cooling_temperature_setpoint,
              avg(heating_temperature_setpoint) as heating_temperature_setpoint,
              avg(IF(percentage_of_ac_usage=1, 1 ,0)) as percentage_of_ac_usage,
              avg(
                IF(percentage_of_ac_usage=1,
                    IF(timestamp>"2023-03-01",
                        IF(cooling_temperature_setpoint<average_room_temperature,
                            1,
                            0
                        ),
                        1
                    ),
                    0
                )
            ) as percentage_of_refrigerant_usage,
              --avg(outside_temperature) as outside_temperature,
              COUNT(DISTINCT room) as rooms_count
        FROM {cnf.table_exp_rooms}
        WHERE timestamp BETWEEN "{start_date.strftime("%Y-%m-%d %H:%M:%S")}" AND "{end_date.strftime("%Y-%m-%d %H:%M:%S")}"
        AND experiment_name = "{tab_exper_exp_param}"
        group by
            DATETIME_TRUNC(DATETIME(timestamp, "{cnf.exp_dict[tab_exper_exp_param]['time_zone']}"), HOUR),
            floor
        )
        ORDER BY timestamp ASC
    """
    exp_df = bq.send_bq_query(bq_client, query)
    summary_dict = exp.get_exp_summary_dict(exp_df, tab_exper_exp_param)

    test_dict = summary_dict[cnf.test_group]
    control_dict = summary_dict[cnf.control_group]
    if (len(control_dict['summary avg post']) == 0) or (len(test_dict['summary avg post']) == 0):
        col2_exper.header("Not enough data to show results yet.")
    else:
        # if 'ventilation' in tab_exper_exp_param or 'cooling' in tab_exper_exp_param or 'shutdown' in tab_exper_exp_param:
        #     # A horrible hack to deal with cases of very different distributions
        #     scaling_factors = test_dict['summary avg pre'].mean() / control_dict['summary avg pre'].mean()
        #     control_dict['summary avg'] = control_dict['summary avg'] * scaling_factors
        #     control_dict['summary avg pre'] = control_dict['summary avg pre'] * scaling_factors
        #     control_dict['summary avg post'] = control_dict['summary avg post'] * scaling_factors

        # get selected metric summarised in a compact df
        metric_df = exp.get_selected_metric_df(test_dict, control_dict, tab_exper_exp_param,
                                               tab_exper_metric_param, tab_exper_agg_param)
        if 'exp_raw_data' in st.session_state and st.session_state.exp_raw_data:
            col2_exper.dataframe(metric_df, use_container_width=True)
        else:
            chart = exp.chart_df(metric_df, tab_exper_exp_param, tab_exper_metric_param)
            col2_exper.altair_chart(chart.interactive(), use_container_width=True)
            exp.show_summary_tables(test_dict, control_dict, col2_exper, tab_exper_exp_param)


main()
