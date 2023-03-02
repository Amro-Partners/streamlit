from datetime import timedelta, timezone
import pandas as pd
import altair as alt
import streamlit as st
from firebase_admin import firestore
import config as cnf
import rooms
import times


def set_params_consumpt(col1, col2):
    building_param = col1.radio('Select building', ['Amro Seville'], key='consump_building')
    min_time = (times.utc_now() - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    max_time = (times.utc_now() - timedelta(days=105)).replace(hour=0, minute=15, second=0, microsecond=0)
    time_param = col1.slider('Select date range',
                             min_value=min_time,
                             max_value=max_time,
                             value=(min_time, max_time),
                             key='consump_time')
    metric_param = col1.radio('Select metric', ['Elect. consumption (kWh)', 'Floor area elect. consumption (kWh/m2)',
                                                'GHG emission (kgCO2e)', 'GHG emission intensity (kgCO2e/m2)'], key='consump_metric')
    data_param_list = (['Total floors 1-8', 'Total clusters', 'Total floors S', 'Total floor B', 'Total VRV internal rooms fans',
     'Total Climatization', 'Total VRV external units', 'Total AHU', 'Total thermal stores', 'HVAC energy consumption']
                       + sorted([key for key in rooms.read_consumption_codes('consumption_codes_seville.csv').values()]))

    agg_param = col1.radio('Group by', cnf.agg_param_dict['Consumption'].keys(), key='consump_agg')
    raw_data = col2.checkbox("Show raw data", value=False, key="consump_raw_data")
    data_param = col1.multiselect('Select data', data_param_list, default='Building energy consumption', key='consump_data')
    return building_param, time_param, agg_param, metric_param, data_param, raw_data


@st.cache_data(show_spinner=False)
def consumption_summary(_db, building_param, time_param, agg_param):
    building_dict = cnf.sites_dict[building_param]

    # Choose start date and an end date for the analysis
    t_min = times.convert_datetmie_to_string(times.local_to_utc(time_param[0], building_dict['time_zone'], timezone.utc))
    t_max = times.convert_datetmie_to_string(times.local_to_utc(time_param[1] + timedelta(days=1), building_dict['time_zone'], timezone.utc))

    doc_consumpt = (_db.collection(u'BMS_Seville_Consumos_Electricidad2')
           .where('datetime', '>=', t_min).where('datetime', '<', t_max).
           order_by('datetime', direction=firestore.Query.ASCENDING)).stream()

    # print the difference in Kwh to get actual electricity consumption
    df = pd.DataFrame([s.to_dict() for s in doc_consumpt]).set_index('datetime')
    df.index = pd.to_datetime(df.index).round('15min')

    # remove unnecessary fields
    drop_cols = []
    for col in df.columns:
        if ('_W_S' in col) or ('ModbusMaster' in col) or ('Potencia' in col) or ('Porcentaj'  in col):
            drop_cols += [col]

    df.drop(columns=drop_cols, inplace=True)

    title_dict = rooms.read_consumption_codes('consumption_codes_seville.csv')
    new_cols = []
    for col in df.columns:
        if title_dict.get(col):
            new_cols += [title_dict.get(col)]
        else:
            new_cols += [col]
    df.columns = new_cols

    df['Total floors 1-8'] = (df['Floor 1 total'] + df['Floor 2 total'] + df['Floor 3 total'] + df['Floor 4 total']
                              + df['Floor 5 total'] + df['Floor 6 total'] + df['Floor 7 total'] + df['Floor 8 total'])
    df['Total AHU'] = df['Floor 9 CL01']  + df['Floor 9 CL02'] + df['Floor 9 CL03']
    df['Total Climatization'] = df['Floor 9 Climatization']
    df['Total floors S'] = (df['Floor S Laundry'] + df['Floor S generator set '] + df['Floor S Lift 1']
                            + df['Floor S Lift 1'] + df['Floor S Lift 2'] + df['Floor S Lift 3'] + df['Floor S Lift 4'])
    df['Total floor B'] = (df['Floor B Lobby'] + df['Floor B Cefeteria'] + df['Floor B Cookers'] + df['Floor B Kitchen'])
    df['Total thermal stores'] = df['Floor 9 QTON themral store'] + df['Floor 9 Aerotermia themral store']
    df['Total clusters'] = (df['Floor 1 Cluster 1'] + df['Floor 1 Cluster 2'] + df['Floor 2 Cluster 1'] + df['Floor 2 Cluster 2']
                            + df['Floor 3 Cluster 1'] + df['Floor 3 Cluster 2'] + df['Floor 4 Cluster 1'] + df['Floor 4 Cluster 2']
                            + df['Floor 5 Cluster 1'] + df['Floor 5 Cluster 2'] + df['Floor 6 Cluster 1'] + df['Floor 6 Cluster 2']
                            + df['Floor 7 Cluster 1'] + df['Floor 7 Cluster 2'] + df['Floor 8 Cluster 1'] + df['Floor 8 Cluster 2'])
    df['Total VRV internal rooms fans'] = df['Total floors 1-8'] - df['Total clusters']
    df['Total VRV external units'] = df['Total Climatization'] - df['Total thermal stores'] - df['Total AHU']
    df['HVAC energy consumption'] = df['Total AHU'] + df['Total VRV internal rooms fans'] + df['Total VRV external units']

    df = df.reindex(sorted(df.columns), axis=1)

    time_zone = cnf.sites_dict[building_param]['time_zone']
    df_diff = df.diff().round(decimals=2).shift(-1).iloc[:-1]
    df_diff = times.groupby_date_vars(df_diff,
                                          cnf.agg_param_dict['Consumption'][agg_param],
                                          to_zone=time_zone).sum()

    df_diff = df_diff.join(add_temp(_db, t_min, t_max, time_zone, agg_param))
    return df_diff


@st.cache_data(show_spinner=False)
def add_temp(_db, t_min, t_max, time_zone, agg_param):
    doc_outdoor_temp = (_db.collection(u'weather_Seville')
           .where('datetime', '>=', t_min).where('datetime', '<', t_max).
           order_by('datetime', direction=firestore.Query.ASCENDING)).stream()
    df_temp = pd.DataFrame([s.to_dict() for s in doc_outdoor_temp]).set_index('datetime')[['temperature']]
    df_temp.index = pd.to_datetime(df_temp.index).round('15min')
    df_temp = times.groupby_date_vars(df_temp,
                                          cnf.agg_param_dict['Consumption'][agg_param],
                                          to_zone=time_zone).mean()

    return df_temp.rename(columns={'temperature': 'outdoor temperature'})


@st.cache_data(show_spinner=False)
def convert_metric(df, metric_param):
    if 'kgCO2e' in metric_param:  # convert to kgCO2e
        for col in df.columns:
            if 'temperature' not in col:
                df[col] = df[col] * 0.259
    if '/m2' in metric_param:  # divide by floor area
        for col in df.columns:
            if 'temperature' not in col:
                df[col] = df[col] / 10782
    return df


def chart_df(df, data_param, agg_param, metric_param):
    chart = (alt.Chart(df[data_param].reset_index().melt(agg_param), title=f'Comparison of floor area electricity consumption with outdoor temperature').mark_line().encode(
        x=alt.X(agg_param, title='Date', axis=alt.Axis(title='', tickColor='white', grid=False, domain=False, labelAngle=0)),
        y=alt.Y('value', axis=alt.Axis(title=metric_param, tickColor='white', domain=False), scale=alt.Scale(zero=False)),
        color=alt.Color('variable',
                        legend=alt.Legend(labelFontSize=14, direction='vertical', titleAnchor='middle',
                                          orient="right", title=''))))

    temp_line = (alt.Chart(df[['outdoor temperature']].reset_index().melt(agg_param), title=metric_param).mark_line(strokeDash=[1, 1]).encode(
        x=alt.X(agg_param, axis=alt.Axis(title='Date', tickColor='white', grid=False, domain=False, labelAngle=0)),
        y=alt.Y('value', axis=alt.Axis(title='Outdoor temperature (°C)', tickColor='white', domain=False, titleAngle=-90), scale=alt.Scale(zero=False)),
        color=alt.Color('variable',
                        legend=alt.Legend(labelFontSize=14, direction='vertical', titleAnchor='middle',
                                          orient="right", title=''))))
    return alt.layer(chart, temp_line).resolve_scale(y='independent')
