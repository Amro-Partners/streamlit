import plot
import config as cnf
import times
from datetime import timedelta, timezone
import streamlit as st


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


def run_plots_heatmaps(df_dict, building_param, data_param, time_param, agg_param, col):
    building_dict, param_dict, agg_param_dict = get_config_dicts(building_param, data_param, agg_param)
    t_min = times.convert_datetime_to_string(times.local_to_utc(time_param[0], building_dict['time_zone'], timezone.utc))
    t_max = times.convert_datetime_to_string(times.local_to_utc(time_param[1] + timedelta(days=1), building_dict['time_zone'], timezone.utc))

    for i, (title, df) in enumerate(df_dict.items()):
        plot.plot_heatmap(
            df=df[(df.index >= t_min) & (df.index <= t_max)],
            agg_param=agg_param,
            fmt=param_dict['fmt'],
            title=title,
            # xlabel=agg_param,
            # ylabel=f'{collect_title}\nrooms' + '\n',
            to_zone=building_dict['time_zone'],
            scale=cnf.hmaps_figure_memory_scale,
            col=col)
