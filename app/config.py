from datetime import datetime, timedelta
import times
import numpy as np


app_version = 2.0
release_date = '22/02/2023'
test = True

figure_memory_scale = 0.25  # scaling the original seaborn in order to reduce memory usage
cert_file = "amro-partners-firebase-adminsdk-syddx-7de4edb3c4.json"  # certification file for firebase authentication
storage_bucket = 'amro-partners.appspot.com'

tabs = ["ROOMS HEATMAPS", "ROOMS CHARTS", "CONSUMPTION", "EXPERIMENTS"]


'''
data_param_dict maps keys strings to be selected by user (as keys) to a list of parameters:
field_keyword:substrings of the required field within the firebase collection
fmt: heatmap text format
vmin: heatmap scale minimum
vmax: heatmap scale maximum
'''
data_param_dict = {
    "Avg. room temperature (°C)": {
        'is_rooms': True,
        'field_keyword': ['Room_Temp', 'RoomTemp'],
        'match_keyword': 'substring',  # 'substring' or 'exact' match for field_keyword
        'fmt': '.1f'
    },
    "Cooling temperature set point (°C)": {
        'is_rooms': True,
        'field_keyword': ['SetTempCool'],
        'match_keyword': 'substring',  # 'substring' or 'exact' match for field_keyword
        'fmt': '.1f'
    },
    "Heating temperature set point (°C)": {
        'is_rooms': True,
        'field_keyword': ['SetTempHeat'],
        'match_keyword': 'substring',  # 'substring' or 'exact' match for field_keyword
        'fmt': '.1f'
    },
    'Percentage of A/C usage (%)': {
        'is_rooms': True,
        'field_keyword': ['OnOffState', 'State_BI'],
        'match_keyword': 'substring',  # 'substring' or 'exact' match for field_keyword
        'fmt': '0.0%'
    },
    'Outside temperature (°C)': {
        'is_rooms': False,
        'field_keyword': ['temperature'],
        'match_keyword': 'exact',  # 'substring' or 'exact' match for field_keyword
        'fmt': '.1f'
    },
    '_Outside temperature 3h prediction (°C)': {
        'is_rooms': False,
        'field_keyword': ['3h_temperature_interp'],
        'match_keyword': 'exact',  # 'substring' or 'exact' match for field_keyword
    },
}


# TODO: we need to localise the start_date and end_date
agg_param_dict = {
    "Date": {
        'start_date_utc': (times.utc_now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0),
        'end_date_utc': (times.utc_now()).replace(hour=0, minute=0, second=0, microsecond=0),
        'aggregation_field_name': 'Date',
        'aggregation_strftime': '%Y-%m-%d\n%A'
    },
    "Hour of Day": {
        'start_date_utc': (times.utc_now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0),
        'end_date_utc': (times.utc_now()).replace(hour=0, minute=0, second=0, microsecond=0),
        'aggregation_field_name': 'Hour',
        'aggregation_strftime': '%H'
    },
    # "Latest reading": {
    #     'start_date_utc': (times.utc_now() - timedelta(minutes=15)),
    #     'end_date_utc': (times.utc_now()),
    #     'aggregation_field_name': 'Local time',
    #     'aggregation_strftime': '%Y-%m-%d %H:%M:%S'
    # },
}


sites_dict = {
    "Amro Seville fan speed pilot CL01": {
        'time_zone': 'Europe/Madrid',
        'rooms_file': "rooms_codes_seville_CL01_exp.csv",
        'floors_order': ['Control',
                         'Test'],
        'floors_col': 'Group',
        'start_exp_date_utc': datetime(2022, 12, 2, 12, 0),
        'end_exp_date_utc': datetime(2023, 2, 28, 12, 0),
        'calibration_days': 7,
        'market_based_electricity_cost': 0.370,
        'location_based_co2': 0.136
    },
    "Amro Seville ventilation temp pilot CL02": {
        'time_zone': 'Europe/Madrid',
        'rooms_file': "rooms_codes_seville_CL02_exp.csv",
        'floors_order': ['Control',
                         'Test'],
        'floors_col': 'Group',
        'start_exp_date_utc': datetime(2022, 12, 2, 12, 0),
        'end_exp_date_utc': datetime(2022, 12, 28, 12, 0),
        'calibration_days': 7,
        'market_based_electricity_cost': 0.370,
        'location_based_co2': 0.136
    },
    "Amro Seville": {
        'time_zone': 'Europe/Madrid',
        'rooms_file': "rooms_codes_seville.csv",
        'floors_order': ["Planta S", "Planta B", "Planta 1", "Planta 2", "Planta 3", "Planta 4",
                         "Planta 5", "Planta 6", "Planta 7", "Planta 8", "Planta 9"],
        'floors_col': 'Title'
    },
    "Amro Malaga": {
        'time_zone': 'Europe/Madrid',
        'rooms_file': "rooms_codes_malaga.csv",
        'floors_order': ["Planta S", "Planta B", "Planta 1", "Planta 2", "Planta 3",  "Planta 4"],
        'floors_col': 'Title'
    },
}

test_build_terms = ['pilot', 'exp', 'flight']
test_sites = [s for s in sites_dict.keys() if any([sub in s for sub in test_build_terms])]
non_test_sites = [s for s in sites_dict.keys() if all([sub not in s for sub in test_build_terms])]


# Experiment settings
avg_group_df_name = 'summary avg'  # avg across the group per timestamp
avg_pre_df_name = 'summary avg pre'  # avg across the group
avg_post_df_name = 'summary avg post'  # avg across the group

num_rooms_name = 'Number of rooms'  # number of rooms across the group

room_temp_name = "Avg. room temperature (°C)"  # avg. room temperature
temp_setpoint_name = 'Cooling temperature set point (°C)'
ac_usage_name = 'Percentage of A/C usage (%)'
elect_consump_name = 'Average room electricity consumption (kWh)'  # number of rooms across the group
elect_cost_name = 'Average room electricity cost (€) (ex. VAT)'  # number of rooms across the group
elect_carbon_name = 'Average room carbon footprint (kg CO2)'  # number of rooms across the group


formatters = {
    num_rooms_name: lambda x: f"{round(x)}" if x == x else x,
    room_temp_name: lambda x: f"{x:.2f}" if type(x) in (float, np.float32, np.float64) else f"[{x[0]:.2f}, {x[1]:.2f}]",
    temp_setpoint_name: lambda x: f"{x:.2f}" if type(x) in (float, np.float32, np.float64) else f"[{x[0]:.2f}, {x[1]:.2f}]",
    ac_usage_name: lambda x: f"{x:.1%}" if type(x) in (float, np.float32, np.float64) else f"[{x[0]:.1%}, {x[1]:.1%}]",
    elect_consump_name: lambda x: f"{x:.2f}" if type(x) in (float, np.float32, np.float64) else f"[{x[0]:.2f}, {x[1]:.2f}]",
    elect_cost_name: lambda x: f"{x:.2f}" if type(x) in (float, np.float32, np.float64) else f"[{x[0]:.2f}, {x[1]:.2f}]",
    elect_carbon_name: lambda x: f"{x:.2f}" if type(x) in (float, np.float32, np.float64) else f"[{x[0]:.2f}, {x[1]:.2f}]"
}

formatters2 = {
    num_rooms_name: lambda x: f"{round(x)}" if x == x else x,
    room_temp_name: lambda x: f"{x:.1%}" if type(x) in (float, np.float32, np.float64) else f"[{x[0]:.1%}, {x[1]:.1%}]",
    temp_setpoint_name: lambda x: f"{x:.1%}" if type(x) in (float, np.float32, np.float64) else f"[{x[0]:.1%}, {x[1]:.1%}]",
    ac_usage_name: lambda x: f"{x:.1%}" if type(x) in (float, np.float32, np.float64) else f"[{x[0]:.1%}, {x[1]:.1%}]",
    elect_consump_name: lambda x: f"{x:.1%}" if type(x) in (float, np.float32, np.float64) else f"[{x[0]:.1%}, {x[1]:.1%}]",
    elect_cost_name: lambda x: f"{x:.1%}" if type(x) in (float, np.float32, np.float64) else f"[{x[0]:.1%}, {x[1]:.1%}]",
    elect_carbon_name: lambda x: f"{x:.1%}" if type(x) in (float, np.float32, np.float64) else f"[{x[0]:.1%}, {x[1]:.1%}]",
}

metrics = [room_temp_name,
           temp_setpoint_name,
           ac_usage_name,
           elect_consump_name,
           elect_cost_name,
           elect_carbon_name]

test_group = "Test"
control_group = "Control"

time_agg_dict = {
    'Daily': '1D',
    'Hourly': '1H',
    '15 minutes': '15T'
}

chart_colours_dict = {
    'Avg. room temperature (°C)': 'black',
    'Cooling temperature set point (°C)': 'lightskyblue',
    'Heating temperature set point (°C)': 'red',
    'Outside temperature (°C)': 'burlywood'
}