from datetime import datetime
import numpy as np
import times

app_version = 3.0
release_date = '22/02/2023'

cert_file = "amro-partners-firebase-adminsdk-syddx-7de4edb3c4.json"  # certification file for firebase authentication
bq_cert_file = "amro-partners-f2967e9bb3a0.json"
storage_bucket = 'amro-partners.appspot.com'
bq_project = "amro-partners"

# BQ tables
table_consumption = 'consumption.consumption'
table_heatmaps = 'heatmaps.heatmaps'
table_charts_rooms = 'charts.rooms'
table_charts_ahus = 'charts.ahus'
table_exp_rooms = 'experiments.rooms'


tabs = ["CONSUMPTION", "ROOMS HEATMAPS", "ROOMS CHARTS", "AHU CHARTS", "EXPERIMENTS", "OCCUPANCY", "WATER"]
tabs_space = [2.5, 0.5, 6, 1]

sites_dict = {
    "Amro Seville": {
        'time_zone': 'Europe/Madrid',
        'rooms_file': "rooms_codes_seville.csv",
        'vent_file': 'vent_codes_seville.csv',
        'floors_order': ["Planta S", "Planta B", "Planta 1", "Planta 2", "Planta 3", "Planta 4",
                         "Planta 5", "Planta 6", "Planta 7", "Planta 8", "Planta 9"],
        'rooms_chart_cols': [('Avg. room temperature (°C)', 'Heating temperature set point (°C)', 'Outside temperature (°C)'),
                             (), 'Percentage of A/C usage (%)'],
        'AHU_chart_cols': [('Outside temperature (°C)', 'Ventilation temperature set point (°C)'),
                           ('Ventilation rate supply',),
                           'Supply Running'],
        'floors_col': 'Title',
        'location_based_co2': 0.259,
        'area_m2': 10782,
        'beds': 339
    },
    "Amro Valencia": {
        'time_zone': 'Europe/Madrid',
        'rooms_file': "rooms_codes_valencia.csv",
        'vent_file': 'vent_codes_valencia.csv',
        'floors_order': ["Planta B", "Planta 1", "Planta 2", "Planta 3",  "Planta 4", "Planta 5",  "Planta 6"],
        'rooms_chart_cols': [('Avg. room temperature (°C)', 'Heating temperature set point (°C)', 'Outside temperature (°C)'),
                             (), 'Percentage of A/C usage (%)'],
        'AHU_chart_cols': [('Outside temperature (°C)',),
                           ('Ventilation rate supply',), ''],
        'floors_col': 'Title',
        'location_based_co2': 0.259,
        'area_m2': 4007.58,
        'beds': 162
    },
    "Amro Malaga": {
        'time_zone': 'Europe/Madrid',
        'rooms_file': "rooms_codes_malaga.csv",
        'vent_file': 'vent_codes_seville.csv',
        'floors_order': ["Planta S", "Planta B", "Planta 1", "Planta 2", "Planta 3",  "Planta 4"],
        'rooms_chart_cols': [
            ('Avg. room temperature (°C)', 'Heating temperature set point (°C)', 'Outside temperature (°C)'),
            (), 'Percentage of A/C usage (%)'],
        # 'AHU_chart_cols': [('Outside temperature (°C)',),
        #                    ('Ventilation rate supply',), ''],
        'floors_col': 'Title',
        'location_based_co2': 0.259,
        'area_m2': 7000,
        'beds': 231
    },
}


######### Heatmaps  ###########

hmaps_figure_memory_scale = 0.25  # scaling the original seaborn in order to reduce memory usage

'''
data_param_dict maps keys strings to be selected by user (as keys) to a list of parameters:
field_keyword:substrings of the required field within the firebase collection
fmt: heatmap text format
vmin: heatmap scale minimum
vmax: heatmap scale maximum
'''
data_param_dict = {
    "Avg. room temperature (°C)": {
        'show_per_room': True,
        'bq_field': 'average_room_temperature',
        'fmt': '.1f',
        'colour': 'black'
    },
    "Cooling temperature set point (°C)": {
        'show_per_room': True,
        'bq_field': 'cooling_temperature_setpoint',
        'fmt': '.1f',
        'colour': 'lightskyblue'
    },
    "Heating temperature set point (°C)": {
        'show_per_room': True,
        'bq_field': 'heating_temperature_setpoint',
        'fmt': '.1f',
        'colour': 'red'
    },
    'Percentage of A/C usage (%)': {
        'show_per_room': True,
        'bq_field': 'percentage_of_ac_usage',
        'fmt': '0.0%'
    },
    'Percentage of Refrig. usage (%)': {
        'show_per_room': True,
        'bq_field': 'percentage_of_refrigerant_usage',
        'fmt': '0.0%'
    },
    'Outside temperature (°C)': {
        'show_per_room': True,
        'bq_field': 'outside_temperature',
        'fmt': '.1f',
        'colour': 'burlywood'
    },
    '_Outside temperature 3h prediction (°C)': {
        'show_per_room': False,
        'bq_field': 'outside_temperature_3h prediction',
        'colour': 'burlywood'
    },
    'Ventilation temperature set point (°C)': {
        'show_per_room': False,
        'bq_field': 'ventilation_temperature_setpoint',
        'colour': 'lightskyblue'
    },
    'Supply Running': {
        'show_per_room': False,
        'bq_field': 'supply_running'
    },
    'Ventilation rate supply': {
        'show_per_room': False,
        'bq_field': 'ventilation_rate_supply',
        'colour': 'peru'
    },
    'Ventilation rate return': {
        'show_per_room': False,
        'bq_field': 'ventilation_rate_supply',
        'colour': 'burlywood'
    },
    'Room consumption (kWh)': {
        'show_per_room': True,
        'bq_field': 'room_consumption',
        'fmt': '.1f',
        'cumulative': True
    }
}


hmps_agg_param_dict = {
    "Date": {
        'aggregation_field_name': 'Date',
        'aggregation_bq': 'DATE',
        'aggregation_strftime': '%Y-%m-%d\n%A'
    },
    "Hour of Day": {
        'aggregation_field_name': "Hour of Day",
        'aggregation_bq': 'HOUR',
        'aggregation_strftime': '%H'
    }
}


######### Consumption  ###########

# TODO: we need to localise the start_date and end_date
consumpt_agg_param_dict = {
    "Date": {
        'aggregation_bq': 'DATE',
        'building_consump_intensity_target': 6 * 12 / 365,  # 6kwh/m2 is our monthly target for
        'aggregation_field_name': 'Date',
        'aggregation_strftime': '%Y-%m-%d',
        'agg_func': 'sum'
    },
    "Week": {
        'aggregation_bq': 'WEEK',
        'building_consump_intensity_target': 6 * 12 / 52,  # 6kwh/m2 is our monthly target for
        'aggregation_field_name': 'Week',
        'aggregation_strftime': '%Y week %W',
        'agg_func': 'sum'
    },
    "Month": {
        'aggregation_bq': 'MONTH',
        'building_consump_intensity_target': 6,  # 6kwh/m2 is our monthly target for
        'aggregation_field_name': 'Month',
        'aggregation_strftime': '%Y-%m\n%B',
        'agg_func': 'sum'
    }
}


######### Experiments  ###########
######################################
exp_dict = {
    # "Amro Malaga adaptive ventilation speed": {
    #     'time_zone': 'Europe/Madrid',
    #     'groups_order': ['Control',
    #                      'Test'],
    #     'group_col': 'Group',
    #     'start_exp_date_utc': datetime(2023, 5, 24, 16, 0),
    #     'end_exp_date_utc': datetime.now(),
    #     'calibration_days': 0,
    #     'market_based_electricity_cost': 0.370,
    #     'location_based_co2': 0.259,
    #     'sequential_A_B': True
    # },
    "Amro Seville adaptive ventilation speed": {
        'time_zone': 'Europe/Madrid',
        'groups_order': ['Control',
                         'Test'],
        'group_col': 'Group',
        'start_exp_date_utc': datetime(2023, 5, 24, 16, 0),
        'end_exp_date_utc': datetime.now(),
        'calibration_days': 0,
        'market_based_electricity_cost': 0.370,
        'location_based_co2': 0.259,
        'sequential_A_B': True
    },
    "Amro Valencia adaptive ventilation speed": {
        'time_zone': 'Europe/Madrid',
        'groups_order': ['Control',
                         'Test'],
        'group_col': 'Group',
        'start_exp_date_utc': datetime(2023, 5, 24, 16, 0),
        'end_exp_date_utc': datetime.now(),
        'calibration_days': 0,
        'market_based_electricity_cost': 0.370,
        'location_based_co2': 0.259,
        'sequential_A_B': True
    },



    # "Amro Seville fan speed pilot CL01": {
    #     'time_zone': 'Europe/Madrid',
    #     'groups_order': ['Control',
    #                      'Test'],
    #     'group_col': 'Group',
    #     'start_exp_date_utc': datetime(2022, 12, 1, 0, 0),
    #     'end_exp_date_utc': datetime(2023, 1, 10, 0, 0),
    #     'calibration_days': 0,
    #     'market_based_electricity_cost': 0.370,
    #     'location_based_co2': 0.259
    # },
    # "Amro Seville ventilation temp pilot CL02": {
    #     'time_zone': 'Europe/Madrid',
    #     'groups_order': ['Control',
    #                      'Test'],
    #     'group_col': 'Group',
    #     'start_exp_date_utc': datetime(2022, 11, 29, 0, 0),
    #     'end_exp_date_utc': datetime(2023, 1, 10, 0, 0),
    #     'calibration_days': 4,
    #     'market_based_electricity_cost': 0.370,
    #     'location_based_co2': 0.259
    # },
    # "Amro Seville tenants AC shutdown": {
    #     'time_zone': 'Europe/Madrid',
    #     'groups_order': ['Control',
    #                      'Test'],
    #     'group_col': 'Group',
    #     'start_exp_date_utc': datetime(2023, 3, 21, 10, 0),  # (times.utc_now() - timedelta(days=1)),  #
    #     'end_exp_date_utc': datetime(2023, 4, 25, 0, 0),
    #     'calibration_days': 7,
    #     'market_based_electricity_cost': 0.1425,
    #     'location_based_co2': 0.259
    # },
    # "Amro Seville adaptive ventilation speed CL01": {
    #     'time_zone': 'Europe/Madrid',
    #     'groups_order': ['Control',
    #                      'Test'],
    #     'group_col': 'Group',
    #     'start_exp_date_utc': datetime(2023, 4, 11, 16, 0),  # (times.utc_now() - timedelta(days=7)),  #
    #     'end_exp_date_utc': datetime(2023, 4, 25, 0, 0),
    #     'calibration_days': 7,
    #     'market_based_electricity_cost': 0.370,
    #     'location_based_co2': 0.259
    # },
    # "Amro Seville ventilation temp CL02": {
    #     'time_zone': 'Europe/Madrid',
    #     'groups_order': ['Control',
    #                      'Test'],
    #     'group_col': 'Group',
    #     'start_exp_date_utc': datetime(2023, 4, 11, 16, 0),  # (times.utc_now() - timedelta(days=7)),  #
    #     'end_exp_date_utc': datetime(2023, 4, 25, 0, 0),
    #     'calibration_days': 7,
    #     'market_based_electricity_cost': 0.370,
    #     'location_based_co2': 0.259
    # },
    # "Amro Seville tenants cooling temp set points": {
    #     'time_zone': 'Europe/Madrid',
    #     'groups_order': ['Control',
    #                      'Test'],
    #     'group_col': 'Group',
    #     'start_exp_date_utc': datetime(2023, 4, 6, 16, 0),
    #     'end_exp_date_utc': datetime(2023, 4, 25, 0, 0),
    #     'calibration_days': 7,
    #     'market_based_electricity_cost': 0.370,
    #     'location_based_co2': 0.259
    # },
    # "Amro Seville tenants temp cooling set points - based on predicted temperatures": {
    #     'time_zone': 'Europe/Madrid',
    #     'groups_order': ['Control',
    #                      'Test'],
    #     'group_col': 'Group',
    #     'start_exp_date_utc': datetime(2023, 4, 11, 16, 0),
    #     'end_exp_date_utc': datetime(2023, 4, 25, 0, 0),
    #     'calibration_days': 7,
    #     'market_based_electricity_cost': 0.370,
    #     'location_based_co2': 0.259
    # },
}

time_agg_dict = {
    # 'Daily': '1D',        ######################################
    'Hourly': '1H',
    # TODO: bring back the 15 minutes once we re-enable 15 minutes data reads for consumption
    #'15 minutes': '15T'
}

# Experiment settings
avg_group_df_name = 'summary avg'  # avg across the group per timestamp
avg_pre_df_name = 'summary avg pre'  # avg across the group
avg_post_df_name = 'summary avg post'  # avg across the group

num_rooms_name = 'Number of rooms'  # number of rooms across the group

room_temp_name = "Avg. room temperature (°C)"  # avg. room temperature
cool_temp_setpoint_name = 'Cooling temperature set point (°C)'
heat_temp_setpoint_name = 'Heating temperature set point (°C)'
ac_usage_name = 'Percentage of A/C usage (%)'
ref_usage_name = 'Percentage of Refrig. usage (%)'
elect_consump_name = 'Average room electricity consumption (kWh)'  # number of rooms across the group
elect_cost_name = 'Average room electricity cost (€) (ex. VAT)'  # number of rooms across the group
elect_carbon_name = 'Average room carbon footprint (kg CO2)'  # number of rooms across the group

int_format = lambda x: f"{round(x)}" if x == x else x
perc_format = lambda x: f"{x:.1%}" if type(x) in (float, np.float32, np.float64) else f"[{x[0]:.1%}, {x[1]:.1%}]"
dec_format = lambda x: f"{x:.2f}" if type(x) in (float, np.float32, np.float64) else f"[{x[0]:.2f}, {x[1]:.2f}]"


formatters = {
    num_rooms_name: int_format,
    room_temp_name: dec_format,
    cool_temp_setpoint_name: dec_format,
    heat_temp_setpoint_name: dec_format,
    ac_usage_name: perc_format,
    elect_consump_name: dec_format,
    elect_cost_name: dec_format,
    elect_carbon_name: dec_format
}

metrics = [room_temp_name,
           cool_temp_setpoint_name,
           heat_temp_setpoint_name,
           ac_usage_name,
           elect_consump_name,
           elect_cost_name,
           elect_carbon_name]

test_group = "Test"
control_group = "Control"



