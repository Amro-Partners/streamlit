from datetime import timedelta
import altair as alt
import streamlit as st
import config as cnf
import rooms
import times


def set_params_consumpt(col1, col2):
    building_param = col1.radio('Select building', cnf.sites_dict.keys(), key='consump_building')
    metric_param = col1.radio('Select metric',
                              ['Elect. consumption (kWh)', 'Floor area elect. consumption (kWh/m2)',
                               'Per bed elect. consumption (kWh)', 'GHG emission (kgCO2e)',
                               'GHG emission intensity (kgCO2e/m2)', 'Per bed GHG emission (kgCO2e)'],
                              key='consump_metric')
    agg_param = col1.radio('Group by', cnf.consumpt_agg_param_dict.keys(), key='consump_agg')
    min_time = (times.utc_now() - timedelta(days=270)).replace(hour=0, minute=0, second=0, microsecond=0)
    max_time = times.utc_now()
    if agg_param == 'Month':
        min_time = min_time.replace(day=1)
        #max_time = max_time.replace(day=1)
    elif agg_param == "Week":
        min_time = min_time - timedelta(days=min_time.weekday())
        max_time = max_time - timedelta(days=max_time.weekday())

    max_time = (max_time - timedelta(days=1)).replace(hour=23, minute=59, second=59)
    time_param = col1.slider('Select date range',
                             min_value=min_time,
                             max_value=max_time,
                             value=(min_time, max_time),
                             key='consump_time')
    data_param_list = get_data_param_list(building_param, time_param)
    data_param = col1.multiselect('Select data', data_param_list, default='Building energy consumption', key='consump_data')
    data_param += ['outdoor temperature']
    raw_data = col2.checkbox("Show raw data", value=False, key="consump_raw_data")
    return building_param, time_param, agg_param, metric_param, data_param


@st.cache_data(show_spinner=False, ttl=3600)
def get_data_param_list(building_param, time_param):
    query = f'''
        SELECT
             distinct data_param
        FROM consumption.consumption
        WHERE
                Date(timestamp) BETWEEN "{time_param[0].strftime("%Y-%m-%d")}" 
                AND "{time_param[1].strftime("%Y-%m-%d")}"
            AND building = "{building_param}"
    '''
    import bigquery as bq
    bq_client = bq.get_bq_client_from_toml_key(cnf.bq_project)
    data_param_list = bq.send_bq_query(bq_client, query)['data_param'].tolist()
    data_param_list = ['Building energy consumption'] + [param for param in data_param_list if
                                                         param != 'Building energy consumption']
    return data_param_list


@st.cache_data(show_spinner=False, ttl=3600)
def convert_metric(df, metric_param, site_dict):
    if 'kgCO2e' in metric_param:
        for col in df.columns:
            if 'temperature' not in col:
                df[col] = df[col] * site_dict['location_based_co2']  # 0.259
    if '/m2' in metric_param:
        for col in df.columns:
            if 'temperature' not in col:
                df[col] = df[col] / site_dict['area_m2']  # 10782
    if 'Per bed' in metric_param:
        for col in df.columns:
            if 'temperature' not in col:
                df[col] = df[col] / site_dict['beds']  # 339
    return df


def chart_df(df, agg_param, metric_param):
    df.columns.name = None
    if df.index.dtype.name == 'dbdate':
        df.index = times.change_index_timezone(df)
    color = alt.Color('variable',
                      legend=alt.Legend(labelFontSize=14,  titleAnchor='middle',
                                        orient="right", direction="vertical", title=''))


    #chart = (alt.Chart(df.drop(['outdoor temperature', 'Building target'], axis=1).reset_index().melt(agg_param),
    chart = (alt.Chart(df.drop(['outdoor temperature', 'Building avg. consumption 2022', 'Building target consumption 2023'], axis=1).reset_index().melt(agg_param),
                       title=f'Comparison of {metric_param} with outdoor temperature').mark_line().encode(
        x=alt.X(agg_param, axis=alt.Axis(title=agg_param, tickColor='white', grid=False, domain=False, labelAngle=0)),
        y=alt.Y('value', axis=alt.Axis(title=metric_param, tickColor='white', domain=False), scale=alt.Scale(zero=False)),
        color=color))

    target_line = (alt.Chart(df['Building avg. consumption 2022'].reset_index().melt(agg_param))
                         .mark_line(strokeDash=[10, 10])
                         .encode(x=alt.X(agg_param, title=agg_param),
                                 y=alt.Y('value'),
                                 color=color))
    chart += target_line

    #################
    target_line = (alt.Chart(df['Building target consumption 2023'].reset_index().melt(agg_param))
                         .mark_line(strokeDash=[10, 10])
                         .encode(x=alt.X(agg_param, title=agg_param),
                                 y=alt.Y('value'),
                                 color=color))
    chart += target_line
    #################


    temp_line = (alt.Chart(df[['outdoor temperature']].reset_index().melt(agg_param), title=metric_param).mark_line(
        strokeDash=[1, 1]).encode(
        x=alt.X(agg_param, axis=alt.Axis(title=agg_param, tickColor='white', grid=False, domain=False, labelAngle=0)),
        y=alt.Y('value',
                axis=alt.Axis(title='Outdoor avg. temperature (°C)', tickColor='white', domain=False, titleAngle=-90),
                scale=alt.Scale(zero=False)),
        color=color))
    return alt.layer(chart, temp_line).resolve_scale(y='independent')
