import os
import sys

import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import hmac

import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Job Tracking", page_icon="🌎", layout="wide")

from app_methods import Production


def check_password():
    """Returns `True` if the user has entered a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets[
            "passwords"
        ] and hmac.compare_digest(
            st.session_state["password"],
            st.secrets.passwords[st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            st.session_state["logged_in"] = True  # Set logged_in state
            st.session_state["logged_in_user"] = st.session_state["username"]
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    # Check if the user is already logged in
    if st.session_state.get("logged_in", False):
        return True

    # If not logged in, display the login form
    login_form()

    if "password_correct" in st.session_state:
        if not st.session_state["password_correct"]:
            st.error("😕 User not known or password incorrect")
        else:
            # Set the login state to True
            st.session_state["logged_in"] = True
            return True

    return False


# Check if the user is logged in
if check_password():
    st.image("Banner1.png", use_container_width=True)
    # Hide the login form and display the main application content
    # st.success(f"You are logged in! {st.session_state['logged_in_user']}")
    # Logout button to allow the user to log out
    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["logged_in_user"] = None
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
else:
    # Stop the execution if not logged in, preventing app content from being shown
    st.stop()


job_production = Production()

user_df = pd.read_csv("foilworx_userlist.csv")

# Get the display type from the user sheet
user_display_type = user_df.loc[
    user_df["username"] == st.session_state["logged_in_user"], "usertype"
].sum()

# Get the fullname from the user sheet
full_name = user_df.loc[
    user_df["username"] == st.session_state["logged_in_user"], "fullname"
].sum()

if user_display_type == 1:
    job_production.display_data(displaytype=user_display_type, fullname=full_name)
elif user_display_type == 2:
    job_production.display_data(displaytype=user_display_type, fullname=full_name)
else:
    job_production.display_data(displaytype=user_display_type, fullname=full_name)
