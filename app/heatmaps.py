import plot
import config as cnf
import times
from datetime import timedelta, timezone
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt


def set_params_heatmaps(col1, col2):
    building_param = col1.radio('Select building', cnf.sites_dict, key='hmaps_building')
    data_param = col1.radio('Select data', [key for key in cnf.data_param_dict.keys() if not key.startswith('_')], key='hmaps_data')
    min_time = (times.utc_now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    max_time = (times.utc_now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_param = col1.slider('Select date range',
                             min_value=min_time,
                             max_value=max_time,
                             value=(min_time, max_time),
                             key='hmaps_time')
    agg_param = col1.radio('Select average by', cnf.hmps_agg_param_dict.keys(), key='hmaps_agg')
    raw_data = col2.checkbox("Show raw data", value=False, key="hmaps_raw_data")
    return building_param, data_param, time_param, agg_param, raw_data


@st.cache_data(show_spinner=False)
def get_config_dicts(building_param, data_param, agg_param):
    building_dict = cnf.sites_dict[building_param]
    param_dict = cnf.data_param_dict[data_param]
    agg_param_dict = cnf.hmps_agg_param_dict[agg_param]
    return building_dict, param_dict, agg_param_dict


@st.cache_data(show_spinner=False)
def pivot_df(df, floor):
    return df[df.floor == floor].pivot(index='timestamp', columns='room', values='parameter_value')


def plot_heatmap(df, fmt, title, xlabel, ylabel, scale, col):
    vmin, vmax = df.min().min(), df.max().max()
    fig = plt.figure(figsize=(scale*24, scale*len(df.columns)))
    sns.set(font_scale=scale*2)

    if st.session_state.hmaps_raw_data:
        col.header(title)
        col.dataframe(df.sort_index())
    else:

        df_plot = df.T.sort_index()
        sns.heatmap(df_plot,
                    annot=True, annot_kws={"fontsize": scale * 16, "weight": "bold"},
                    fmt=fmt, linewidths=.5,
                    cmap=sns.color_palette("coolwarm", as_cmap=True),
                    vmin=vmin, vmax=vmax, cbar=False)
        labels_fontsize = scale * 24
        plt.title(title, fontsize=labels_fontsize)  # title with fontsize 20
        plt.xlabel(xlabel, fontsize=labels_fontsize)  # x-axis label with fontsize 15
        plt.ylabel(ylabel, fontsize=labels_fontsize) # y-axis label with fontsize 15
        plt.yticks(rotation=0)
        col.write(fig)