# Run this file from the app directory

import toml
import os
import config as cnf

cert_file = cnf.bq_cert_file  # certification file for firebase authentication
output_file = os.path.join('.streamlit', "secrets.toml")

with open(os.path.join(os.path.realpath('./'), cert_file)) as json_file:
    json_text = json_file.read()

config = {"bigquery_key": json_text}
toml_config = toml.dumps(config)

# Write the new key in append mode
with open((os.path.join(os.path.realpath('./'), output_file)), "a") as target:
    target.write("\n")  # Add a new line before appending the new data
    target.write(toml_config)
