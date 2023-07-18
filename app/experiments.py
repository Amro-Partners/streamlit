import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy.stats import t
from datetime import timedelta
import times
import config as cnf
import experiments_utils as utl
import streamlit as st
import altair as alt
import pytz
import scipy.stats

# Set display options to show all columns
pd.set_option('display.max_columns', None)


def set_params_exp(col1, col2):
    sorted_experiments = dict(sorted({k: v for k, v in cnf.exp_dict.items()}.items(),
                                     key=lambda item: item[1]['start_exp_date_utc'],
                                     reverse=True)).keys()
    exp_param = col1.radio('Select Flight', sorted_experiments, key='exp_building',
                           format_func=lambda x: x + " [completed]" if cnf.exp_dict[x]['end_exp_date_utc']
                                                                       < (times.utc_now() - timedelta(hours=1)) else x)
    metric_param = col1.radio('Select chart metric',  cnf.metrics, key='exp_chart_metric')
    agg_param = col1.radio('Select chart frequency',  cnf.time_agg_dict.keys(), key='exp_chart_freq')
    raw_data = col2.checkbox("Show raw data", value=False, key="exp_raw_data")
    return exp_param, metric_param, agg_param


def avg_all_rooms(df_dict_room):
    df_rooms_list = []
    for room_param in df_dict_room.keys():
        df_rooms_list += [df_dict_room[room_param]]
    df_concat = pd.concat(df_rooms_list)
    return df_concat.groupby(df_concat.index).mean()


def get_exp_metrics(df_sum, flight_duration, exp_dict):
    # TODO: improve this formula once we store consumption with transform repo
    # 3.42 - avg daily total VRV consumption per room (external units included)
    df_sum[cnf.elect_consump_name] = ((3.42) * flight_duration.days
                                      * df_sum[cnf.ref_usage_name])
    df_sum[cnf.elect_cost_name] = exp_dict['market_based_electricity_cost'] * df_sum[cnf.elect_consump_name]
    df_sum[cnf.elect_carbon_name] = exp_dict['location_based_co2'] * df_sum[cnf.elect_consump_name]
    return df_sum


def select_columns(df):
    df = df.set_index('timestamp')
    rename_cols = {param_dict['bq_field']: param for param, param_dict
                   in cnf.data_param_dict.items() if param_dict['show_per_room']}
    drop_cols = [col for col in df.columns if col not in rename_cols.keys()]
    return df.drop(columns=drop_cols).rename(columns=rename_cols)


@st.cache_data(show_spinner=False, ttl=3600)
def get_exp_summary_dict(_exp_df, exp_param):
    exp_dict = cnf.exp_dict[exp_param]
    summary_dict = {}

    # TODO: flight_duration is currently used also for calculations in add_exp_metrics, but otherwise it is not needed
    flight_duration = exp_dict['end_exp_date_utc'] - exp_dict['start_exp_date_utc']

    for group_param in exp_dict['groups_order']:
        df_group = _exp_df[_exp_df.floor == group_param]
        df_sum = select_columns(df_group)
        #     _exp_df[_exp_df.floor == group_param].drop(columns=['floor'])
        # df_sum = (df_sum.set_index('timestamp').rename(
        #     columns={param_dict['bq_field']: param for param, param_dict
        #              in cnf.data_param_dict.items() if param_dict['show_per_room']}))

        df_sum = get_exp_metrics(df_sum, flight_duration, exp_dict)
        print(exp_param, group_param)
        print(df_sum.mean())
        # converting exp_dict['start_exp_date_utc'] to local time zone and then making it 'timezone unaware'
        # in order to compare with the also localised but 'timezone unaware' df_sum.index
        t = exp_dict['start_exp_date_utc'].astimezone(pytz.UTC).astimezone(pytz.timezone(exp_dict['time_zone'])).replace(tzinfo=None)
        df_sum_pre = df_sum.loc[df_sum.index < t]
        df_sum_post = df_sum.loc[df_sum.index >= t]

        summary_dict[group_param] = {}
        summary_dict[group_param][cnf.num_rooms_name] = df_group.rooms_count.max()

        summary_dict[group_param][cnf.avg_group_df_name] = df_sum
        summary_dict[group_param][cnf.avg_pre_df_name] = df_sum_pre
        summary_dict[group_param][cnf.avg_post_df_name] = df_sum_post
    return summary_dict


def _avg_group_series(group_dict):
    return group_dict.mean()


def _se_group_series(group_dict1, group_dict2):
    return (group_dict1 - group_dict2).sem()


@st.cache_data(show_spinner=False, ttl=3600)
def get_exp_summary_df(test_dict, control_dict, sequential_A_B):
    # avg_pre_df_name is only use for caching
    avg_test, avg_cont, diff = _groups_stat(test_dict, control_dict)
    df_sum = pd.concat([avg_test, avg_cont], axis=1)
    df_sum.columns = [cnf.test_group, cnf.control_group]
    df_sum['Difference'] = diff
    if sequential_A_B:
        std_diff = np.sqrt((test_dict.std()**2/len(test_dict)) + (control_dict.std()**2/len(control_dict)))
        ci_low, ci_high = scipy.stats.norm.interval(0.95, loc=diff, scale=std_diff)
        df_sum['95%  C.I.'] = pd.Series([(i, j) for i, j in zip(ci_low, ci_high)], index=df_sum.index)
    else:
        df_sum['95%  C.I.'] = calculate_CI_pairwise(test_dict, control_dict)
    return df_sum


def _groups_stat(test_dict, cont_dict):
    avg_test = _avg_group_series(test_dict)
    avg_cont = _avg_group_series(cont_dict)
    diff = avg_test - avg_cont
    return avg_test, avg_cont, diff


def calculate_CI_pairwise(df1, df2, lags=1000, alpha=0.05):
    # Newey–West-based estimator for C.I.
    CI_dict = {}
    for col in df1.columns:
        ts1, ts2 = df1[col], df2[col]
        # Compute the difference time series
        diff_ts = ts1 - ts2
        if np.var(diff_ts) < 1e-9:
            CI_dict[col] = (diff_ts[0], diff_ts[0])
            continue

        # Compute the sample mean and variance of the difference time series
        mean_diff = np.mean(diff_ts)

        # Estimate the Newey-West standard error of the mean difference
        n = len(diff_ts)
        lags = min(lags, n-1)
        nw_acf = sm.tsa.acf(diff_ts, nlags=lags, qstat=False, fft=False, alpha=None, missing="drop")
        acovf_nw = nw_acf[0:lags]
        nw_var = np.sum(acovf_nw * acovf_nw) * 2 / (n - 1)
        nw_se = np.sqrt(nw_var / n)

        # Compute the confidence interval for the mean difference

        df = n - lags
        t_crit = t.ppf(1 - alpha / 2, df)

        # Compute the confidence interval for the mean difference
        ci_low = mean_diff - t_crit * nw_se
        ci_high = mean_diff + t_crit * nw_se

        CI_dict[col] = (ci_low, ci_high)  # f'({ci_low:.4f}, {ci_high:.4f})'

    return pd.Series(CI_dict)


@st.cache_data(show_spinner=False, ttl=3600)
def get_exp_times(exp_param):
    exp_dict = cnf.exp_dict[exp_param]
    start_calibration_date_utc = (exp_dict['start_exp_date_utc'] - timedelta(days=exp_dict['calibration_days']))
    start_exp_date_utc = min(exp_dict['start_exp_date_utc'], times.utc_now())
    end_exp_date_utc = min(exp_dict['end_exp_date_utc'], times.utc_now())
    return start_calibration_date_utc, start_exp_date_utc, end_exp_date_utc


def show_summary_tables(_test_dict, _control_dict, _col, exp_param):
    exp_dict = cnf.exp_dict[exp_param]
    start_calibration_date_utc, start_exp_date_utc, end_exp_date_utc = get_exp_times(exp_param)
    flight_duration_pre = start_exp_date_utc - start_calibration_date_utc
    flight_duration_post = end_exp_date_utc - start_exp_date_utc

    # Get a comparison stats df between test and control sets
    first_row = pd.DataFrame({cnf.test_group: _test_dict[cnf.num_rooms_name],
                              cnf.control_group: _control_dict[cnf.num_rooms_name]},
                             index=[cnf.num_rooms_name])  # First row with number of rooms

    # if flight_duration_pre.days > 0:
    # # The rest of the metrics pre-starting the experiment
    #     summary_df_pre = get_exp_summary_df(_test_dict[cnf.avg_pre_df_name],
    #                                         _control_dict[cnf.avg_pre_df_name])
    #     summary_df_pre = pd.concat([first_row, summary_df_pre])
    #     _col.subheader('Pre-experiment calibration period')
    #     _col.text(f'Pre-experiment calibration duration: {start_calibration_date_utc} - {start_exp_date_utc} '
    #               f'({flight_duration_pre.days} days) ')
    #     _col.table(utl.format_row_wise(summary_df_pre, cnf.formatters))

    # The rest of the metrics post-starting the experiment
    summary_df_post = get_exp_summary_df(_test_dict[cnf.avg_post_df_name],
                                         _control_dict[cnf.avg_post_df_name],
                                         exp_dict['sequential_A_B'])
    summary_df_post = pd.concat([first_row, summary_df_post])

    exp_kwh_monthly = round(-summary_df_post.loc['Average room electricity consumption (kWh)']['Difference']
                       * 30 / flight_duration_post.days
                       * 329, 2)

    _col.subheader('A/B testing period')
    _col.text(f'Expected monthly savings: {exp_kwh_monthly} kWh')
    _col.text(f'Flight duration: {start_exp_date_utc} - {end_exp_date_utc} '
              f'({flight_duration_post.days} days '
              f'{flight_duration_post.seconds // 3600} hours '
              f'{flight_duration_post.seconds%3600//60} minutes)')
    _col.table(utl.format_row_wise(summary_df_post.loc[cnf.formatters.keys()], cnf.formatters))

    title, intro, body = utl.info(flight_duration_post,
                                    exp_param,
                                    exp_dict['market_based_electricity_cost'],
                                    exp_dict['location_based_co2'])
    _col.expander(title, expanded=False).write(f'{intro[1]}\n{body}')


@st.cache_data(show_spinner=False, ttl=3600)
def get_selected_metric_df(_test_dict, _control_dict, exp_param, metric_param, agg_param):
    # exp_param required only for caching
    df = _test_dict[cnf.avg_group_df_name][[metric_param]].join(
        _control_dict[cnf.avg_group_df_name][[metric_param]],
        lsuffix='_'+cnf.test_group,
        rsuffix='_'+cnf.control_group,
        how='outer')
    df = df.groupby(pd.Grouper(freq=cnf.time_agg_dict[agg_param], origin='epoch')).mean()
    df.index.name = "Time"
    return df


def chart_df(metric_df, exp_param, metric_param):
    range_ = ['#0F4C3A', '#29AB87'] # ['red', 'black']
    metric_df.columns = [c.split('_')[-1] for c in metric_df.columns]
    domain = [c.split('_')[-1] for c in metric_df.columns]

    chart = (alt.Chart(metric_df.reset_index().melt('Time'), title=f'{exp_param}: Comparison of Test and Control groups')
    .mark_line(size=3).encode(
        x=alt.X('Time', axis=alt.Axis(title='Date', format="%Y-%m-%d", tickColor='white', grid=False, domain=False)),
        y=alt.Y('value', axis=alt.Axis(title=metric_param, tickColor='white', domain=False), scale=alt.Scale(zero=False)),
        color=alt.Color('variable',
                        legend=alt.Legend(labelFontSize=14, direction='horizontal', titleAnchor='middle',
                                          orient='bottom', title=''),
                        scale=alt.Scale(domain=domain, range=range_)
                        )))

    # exp_dict = cnf.exp_dict[exp_param]
    # t = exp_dict['start_exp_date_utc'].astimezone(pytz.UTC)  # .astimezone(timezone(exp_dict['time_zone']))
    # xrule = (alt.Chart(pd.DataFrame({'Date': [t]}))
    #          .mark_rule(strokeDash=[12, 6], strokeWidth=2).encode(x='Date:T', color=alt.value('#7f7f7f')))
    return chart #+ xrule