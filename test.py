import gspread
import pandas as pd
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
from st_aggrid import AgGrid

# Set up Google Sheets API
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["google"], scope
)
client = gspread.authorize(credentials)

# Open the Google Sheet by name or URL
SHEET_NAME = "Foilworx_jobs"
sheet = client.open(SHEET_NAME).sheet1

data = pd.DataFrame(sheet.get_all_records())

AgGrid(data)
# # Function to load data from Google Sheet into a DataFrame
# def load_data():
#     data = sheet.get_all_records()
#     return pd.DataFrame(data)
#
# # Function to add a new job
# def add_job(job_name, status):
#     sheet.append_row([job_name, status])
#
# # Function to update a job status
# def update_job(row, status):
#     sheet.update_cell(row, 2, status)  # Assuming column 2 is the 'status' column
#
# # Function to delete a job
# def delete_job(row):
#     sheet.delete_row(row)
#
# # Streamlit UI
# st.title("Job Ticketing System with Google Sheets")
#
# # Display existing jobs
# df = load_data()
# st.write("### Existing Jobs", df)
#
# # Add a new job
# new_job = st.text_input("Enter new job name")
# if st.button("Add Job"):
#     add_job(new_job, "Pending")
#     st.success(f"Job '{new_job}' added!")
#     st.experimental_rerun()
#
# # Update job status
# job_to_update = st.number_input("Enter job row number to update", min_value=2, step=1)
# new_status = st.selectbox("Select new status", ["Pending", "In Progress", "Completed"])
# if st.button("Update Job"):
#     update_job(job_to_update, new_status)
#     st.success(f"Job row {job_to_update} updated to '{new_status}'!")
#     st.experimental_rerun()
#
# # Delete a job
# job_to_delete = st.number_input("Enter job row number to delete", min_value=2, step=1)
# if st.button("Delete Job"):
#     delete_job(job_to_delete)
#     st.success(f"Job row {job_to_delete} deleted!")
#     st.experimental_rerun()
