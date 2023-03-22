import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import times
import config as cnf
from datetime import timedelta
import streamlit as st
import altair as alt

plt.rcParams.update({'figure.max_open_warning': 0})
pd.options.mode.chained_assignment = None  # default='warn'





@st.cache_data(show_spinner=False)
def create_start_end_times(df, col_name):
    column = df[col_name].fillna(value=False)
    start_on_times = []
    end_on_times = []
    if column.iloc[0] in (True, False) and column.iloc[0]:
        start_on_times += [list(df.index)[0]]
    if column.iloc[-1] in (True, False) and column.iloc[-1]:
        end_on_times += [list(df.index)[-1]]

    start_on_times = start_on_times + list(df[(column - column.shift(1)) > 0].index)
    end_on_times = list(df[(column - column.shift(-1)) > 0].index) + end_on_times
    start_on_times = [t - timedelta(minutes=7.5) for t in start_on_times]
    end_on_times = [t + timedelta(minutes=7.5) for t in end_on_times]
    return pd.DataFrame({'start_on_times': start_on_times, 'end_on_times': end_on_times})


def charts(df, _max_datetime, chart_cols):
    # TODO: Ugly code. Must improve this code, no need for a separate chart for predictions
    df_on_off_times = create_start_end_times(df, chart_cols[2])
    # pred_row = pd.DataFrame([[None]*len(df.columns)], columns=df.columns, index=[_max_datetime+timedelta(hours=3)])
    # pred_row['Outside temperature (°C)'] = df.iloc[-1]['_Outside temperature 3h prediction (°C)']
    # df = pd.concat([df, pred_row])
    xvars = [col for col in df.columns if col in chart_cols[0]]

    range_ = [cnf.chart_colours_dict[xvar] for xvar in xvars]
    df.index.name = "Time"
    df = df[xvars]

    df = df.reset_index().melt('Time')
    chart = (alt.Chart(df.loc[df['Time'] <= _max_datetime]).mark_line().encode(
        x=alt.X('Time', axis=alt.Axis(title='Date', formatType="time", tickColor='white', grid=False, domain=False)),
        y=alt.Y('value', axis=alt.Axis(title='Temperature (°C)', tickColor='white', domain=False), scale=alt.Scale(zero=False)),
        color=alt.Color('variable',
                        legend=alt.Legend(labelFontSize=14, direction='horizontal', titleAnchor='middle',
                                          orient='bottom', title=''),
                        scale=alt.Scale(domain=xvars, range=range_)
                        )
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

    rect = alt.Chart(df_on_off_times).mark_rect().mark_rect(opacity=0.2).encode(
        x='start_on_times:T',
        x2='end_on_times:T')

    ch_lay = alt.layer(chart, rect).configure_view(strokeWidth=0)

    return ch_lay