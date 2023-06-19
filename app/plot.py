import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import config as cnf
from datetime import timedelta
import streamlit as st
import altair as alt

plt.rcParams.update({'figure.max_open_warning': 0})
pd.options.mode.chained_assignment = None  # default='warn'



def _flot_to_bool(onoff_col):
    return onoff_col == 1


@st.cache_data(show_spinner=False, ttl=3600)
def float2bool(col):
    return col == 1


@st.cache_data(show_spinner=False, ttl=3600)
def create_start_end_times(onoff_col, timestamp_col):
    onoff_col = _flot_to_bool(onoff_col).fillna(value=0.0)
    start_on_times = []
    end_on_times = []
    if onoff_col.iloc[0] in (0, 1) and onoff_col.iloc[0]:
        start_on_times += [list(timestamp_col)[0]]
    if onoff_col.iloc[-1] in (0, 1) and onoff_col.iloc[-1]:
        end_on_times += [list(timestamp_col)[-1]]

    start_on_times = start_on_times + list(timestamp_col[float2bool(onoff_col) &
                                                         ~float2bool(onoff_col.shift(1).fillna(value=1))])
    end_on_times = list(timestamp_col[float2bool(onoff_col) &
                                      ~float2bool(onoff_col.shift(-1).fillna(value=True))]) + end_on_times
    start_on_times = [t - timedelta(minutes=7.5) for t in start_on_times]
    end_on_times = [t + timedelta(minutes=7.5) for t in end_on_times]
    return pd.DataFrame({'start_on_times': start_on_times, 'end_on_times': end_on_times})


def charts(df, _max_datetime, chart_cols):
    def _df_vars(chart_cols):
        xvars, range_ = [], []
        for col in chart_cols:
            col_dict = cnf.data_param_dict[col]
            bq_col = col_dict['bq_field']
            if bq_col in df.columns:
                df.rename(columns={bq_col: col}, inplace=True)
                xvars += [col]
                #range_ += [col_dict['colour']]

        df_plot = df.rename(columns={'timestamp': 'Time'})
        return df_plot[['Time'] + xvars].melt('Time')

    # TODO: Ugly code. Must improve this code, no need for a separate chart for predictions
    # pred_row = pd.DataFrame([[None]*len(df.columns)], columns=df.columns, index=[_max_datetime+timedelta(hours=3)])
    # pred_row['Outside temperature (°C)'] = df.iloc[-1]['_Outside temperature 3h prediction (°C)']
    # df = pd.concat([df, pred_row])

    color = alt.Color('variable',
                      legend=alt.Legend(labelFontSize=14,  titleAnchor='middle',
                                        orient="right", direction="vertical", title=''))

    df_line = _df_vars(chart_cols[0])
    chart_2_return = (alt.Chart(df_line.loc[df_line['Time'] <= _max_datetime]).mark_line().encode(
        x=alt.X('Time', axis=alt.Axis(title='Date', formatType="time", tickColor='white', grid=False, domain=False, format='%Y-%m-%d %H:%M')),
        y=alt.Y('value', axis=alt.Axis(title='Temperature (°C)', tickColor='white', domain=False),
                scale=alt.Scale(zero=False)),
        color=color
    ))

    # pred_chart = (alt.Chart(df.loc[df['Time'] >= _max_datetime]).mark_line(strokeDash=[1, 1]).encode(
    #     x=alt.X('Time', axis=alt.Axis(title='Date'', formatType="time", tickColor='white', grid=False, domain=False)),
    #     y=alt.Y('value', axis=alt.Axis(title='Temperature (°C)', tickColor='white', domain=False)),
    #     color=alt.Color('variable',
    #                     legend=alt.Legend(labelFontSize=14, direction='horizontal', titleAnchor='middle',
    #                                       orient='bottom', title=''),
    #                     scale=alt.Scale(domain=xvars, range=range_)
    #                     )
    # ))

    if chart_cols[2]:
        df_on_off_times = create_start_end_times(df[cnf.data_param_dict[chart_cols[2]]['bq_field']], df['timestamp'])
        rect = alt.Chart(df_on_off_times).mark_rect().mark_rect(opacity=0.2).encode(
            x='start_on_times:T',
            x2='end_on_times:T')

        chart_2_return = alt.layer(chart_2_return, rect)

    if 'Ventilation rate supply' in chart_cols[1]:
        df_rate = _df_vars(chart_cols[1])
        chart_rate = (alt.Chart(df_rate.loc[df_rate['Time'] <= _max_datetime]).mark_line().encode(
            x=alt.X('Time', axis=alt.Axis(title='Date', formatType="time", tickColor='white', grid=False, domain=False, format='%Y-%m-%d %H:%M')),
            y=alt.Y('value', axis=alt.Axis(title='Ventilation rate (m3/h)', tickColor='white', domain=False),
                    scale=alt.Scale(zero=False, padding=0.3)),
            color=color
        ))

        chart_2_return = alt.layer(chart_2_return, chart_rate).resolve_scale(y='independent')

    return chart_2_return
