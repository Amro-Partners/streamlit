import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
from streamlit.web import bootstrap
# import main

# Read config file with hashed passwords
try:
    with open('../auth.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    st.error("The configuration file was not found.")
    st.stop()

# Initiate authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

def login():
    # Get user information from login page
    name, authentication_status, username = authenticator.login('Login', 'main')

    if st.session_state["authentication_status"]:
        authenticator.logout('Logout', 'main', key='unique_key')
        st.write(f'Welcome *{st.session_state["name"]}*')
        st.title('Some content')
        # main()

    elif st.session_state["authentication_status"] is False:
        st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] is None:
        st.warning('Please enter your username and password')

login()