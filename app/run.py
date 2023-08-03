from streamlit.web import bootstrap

# real_script = 'main.py'
# real_script = 'dashboard.py'
real_script = 'authentication.py'
bootstrap.run(real_script, f'run.py {real_script}', [], {})
