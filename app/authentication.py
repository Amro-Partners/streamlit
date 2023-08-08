import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
import main

# Set the page configuration to wide mode globally.
st.set_page_config(layout="wide")

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

def logout():
    return authenticator.logout('Logout', 'main', key='unique_key')

def centered_login():
    # Create empty columns for the sides to simulate centered content
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        # The actual login components and logic go here
        name, authentication_status, username = authenticator.login('Login', 'main')

        if st.session_state.get("authentication_status"):
            # Execute the main.py script
            main.main()
            # Add the logout button under the dashboard
            logout()
        elif st.session_state.get("authentication_status") is False:
            st.error('Username/password is incorrect')
        elif st.session_state.get("authentication_status") is None:
            st.warning('Please enter your username and password')

if __name__ == '__main__':
    centered_login()
