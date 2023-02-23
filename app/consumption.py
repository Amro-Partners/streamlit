from datetime import timedelta, timezone
import pandas as pd
from firebase_admin import firestore
import config as cnf
import rooms
import times


def set_params_consumpt(col1, col2):
    building_param = col1.radio('Select building', cnf.non_test_sites, key='consump_building')
    min_time = (times.utc_now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    max_time = (times.utc_now() - timedelta(days=1)).replace(hour=0, minute=15, second=0, microsecond=0)
    time_param = col1.slider('Select date range',
                             min_value=min_time,
                             max_value=max_time,
                             value=(min_time, max_time),
                             key='consump_time')
    agg_param = col1.radio('Select average by', cnf.agg_param_dict.keys(), key='consump_agg')
    raw_data = col2.checkbox("Show raw data", value=False, key="consump_raw_data")
    data_param = col1.radio('Select data', [key for key in rooms.read_consumption_codes('consumption_codes_seville.csv').keys()], key='consump_data')
    return building_param, time_param, agg_param, raw_data


def consumption_summary(db, building_param, time_param, agg_param, raw_data):
    building_dict = cnf.sites_dict[building_param]

    # Choose start date and an end date for the analysis
    t_min = times.convert_datetmie_to_string(times.local_to_utc(time_param[0], building_dict['time_zone'], timezone.utc))
    t_max = times.convert_datetmie_to_string(times.local_to_utc(time_param[1] + timedelta(days=1), building_dict['time_zone'], timezone.utc))

    doc = (db.collection(u'BMS_Seville_Consumos_Electricidad2')
           .where('datetime', '>=', t_min).where('datetime', '<', t_max).
           order_by('datetime', direction=firestore.Query.ASCENDING)).stream()

    # print the difference in Kwh to get actual electricity consumption
    df = pd.DataFrame([s.to_dict() for s in doc]).set_index('datetime')
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
        new_cols += [title_dict.get(col)]
    df.columns = new_cols
    df = df.reindex(sorted(df.columns), axis=1)

    df_diff = df.diff().round(decimals=2).shift(-1).iloc[:-1]
    df_diff = times.groupby_date_vars(df_diff,
                                      cnf.agg_param_dict[agg_param],
                                      to_zone=cnf.sites_dict[building_param]['time_zone']).sum()
    return df_diff
