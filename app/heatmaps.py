import plot
import config as cnf
import utils
import times
from datetime import timedelta, timezone


def set_params_heatmaps(col1, col2):
    building_param = col1.radio('Select building', cnf.non_test_sites, key='hmaps_building')
    data_param = col1.radio('Select data', [key for key in cnf.data_param_dict.keys() if not key.startswith('_')], key='hmaps_data')
    min_time = (times.utc_now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    max_time = (times.utc_now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_param = col1.slider('Select date range',
                             min_value=min_time,
                             max_value=max_time,
                             value=(min_time, max_time),
                             key='hmaps_time')
    agg_param = col1.radio('Select average by', cnf.agg_param_dict['Heatmaps'].keys(), key='hmaps_agg')
    raw_data = col2.checkbox("Show raw data", value=False, key="hmaps_raw_data")
    return building_param, data_param, time_param, agg_param, raw_data


def run_plots_heatmaps(df_dict, building_param, data_param, time_param, agg_param, col):
    building_dict, param_dict, agg_param_dict = utils.get_config_dicts(building_param, data_param, agg_param, 'Heatmaps')
    t_min = times.convert_datetmie_to_string(times.local_to_utc(time_param[0], building_dict['time_zone'], timezone.utc))
    t_max = times.convert_datetmie_to_string(times.local_to_utc(time_param[1] + timedelta(days=1), building_dict['time_zone'], timezone.utc))

    for i, (title, df) in enumerate(df_dict.items()):
        plot.plot_heatmap(
            df=df[(df.index >= t_min) & (df.index <= t_max)],
            agg_param=agg_param,
            fmt=param_dict['fmt'],
            title=title,
            # xlabel=agg_param,
            # ylabel=f'{collect_title}\nrooms' + '\n',
            to_zone=building_dict['time_zone'],
            scale=cnf.figure_memory_scale,
            col=col)

