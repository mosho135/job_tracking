import datetime as dt
import time

import numpy as np
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder


class Production:
    def __init__(self):
        self.df = pd.read_csv("foilwork_jobs.csv", encoding="latin-1", low_memory=False)
        self.jobs_df = pd.DataFrame()
        self.today = pd.to_datetime(dt.datetime.today().strftime("%Y/%m/%d %H:%M:%S"))
        self.new_status = ""

    def format_data(self):
        self.df["EstimateTime"] = pd.to_datetime(
            self.df["EstimateTime"], format="%H:%M:%S"
        ).dt.time
        self.df["Deadline"] = pd.to_datetime(self.df["Deadline"])
        self.df["JobCompletedTime"] = pd.to_datetime(self.df["JobCompletedTime"])
        self.jobs_df = self.df.copy()

    def display_data(self, displaytype=1):
        self.format_data()
        if st.button("Refresh Table"):
            st.rerun()

        if displaytype == 2:
            time.sleep(5)
            st.rerun()

        def update_job(display_job, status_update):
            # Create grid options
            gb = GridOptionsBuilder.from_dataframe(display_job)
            gb.configure_selection(
                "multiple", use_checkbox=True
            )  # Enable single row selection
            grid_options = gb.build()

            # Display the grid
            grid_response = AgGrid(
                display_job, gridOptions=grid_options, enable_enterprise=False
            )

            # Get selected row data
            selected_rows = pd.DataFrame(grid_response.get("selected_rows", []))
            # st.write(selected_rows)

            # Ensure selected_rows is not empty
            if not selected_rows.empty:  # Check if there's at least one selected row
                task_id = selected_rows["Job ID"].tolist()

                # Create a form to edit the status
                with st.form(key="edit_status_form"):
                    new_status = status_update
                    submit_button = st.form_submit_button(label="Update Status")

                    if submit_button:
                        # Update the task's status (You would typically update your data structure here)
                        for j_id in task_id:
                            self.jobs_df["Status"] = np.where(
                                self.jobs_df["Job ID"] == j_id,
                                new_status,
                                self.jobs_df["Status"],
                            )
                            self.jobs_df.loc[
                                self.jobs_df["Job ID"] == j_id, "JobCompletedTime"
                            ] = {self.today}
                            self.jobs_df.to_csv("foilwork_jobs.csv", index=False)
                        st.success("Job has been updated")
                        time.sleep(1)
                        st.rerun()

        if displaytype == 1:
            pending_jobs = self.jobs_df.loc[self.jobs_df["Status"] == "Pending"].copy()
            update_job(pending_jobs, "In Progress")
        elif displaytype == 2:
            jobs_todo = self.jobs_df.loc[
                self.jobs_df["Status"] == "In Progress",
                ["Job ID", "Company", "Description", "Size", "Status", "Deadline"],
            ].copy()
            update_job(jobs_todo, "Completed")
        else:
            AgGrid(data=self.jobs_df, height=200, fit_columns_on_grid_load=True)

    def add_job(self):
        # Add a new job
        self.format_data()
        st.subheader("Add New Job")
        job_id = st.text_input("Job ID")
        company = st.text_input("Company")
        description = st.text_input("Description")
        size = st.text_input("Size")
        estimate_time = st.time_input("Estimated Time")
        status = st.selectbox("Status", ["Pending", "In Progress", "Completed"])
        col1, col2 = st.columns(2)
        with col1:
            d_deadline = st.date_input("Deadline", value=self.today)
        with col2:
            d_time = st.time_input("Deadline Time")
        deadline = (pd.to_datetime(str(d_deadline) + " " + str(d_time))).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        if st.button("Add Job"):
            new_job = {
                "Job ID": [job_id],
                "Company": [company],
                "Description": [description],
                "Size": [size],
                "EstimateTime": [estimate_time],
                "Status": [status],
                "Progress": [
                    0 if status == "Pending" else 50 if status == "In Progress" else 100
                ],
                "JobAddedTime": [self.today],
                "Deadline": [deadline],
            }
            new_job_df = pd.DataFrame(new_job)
            self.jobs_df = pd.concat([self.jobs_df, new_job_df], ignore_index=True)
            self.jobs_df.to_csv("foilwork_jobs.csv", index=False)
            st.success(f"Job {job_id} added!")
            time.sleep(1)
            st.rerun()

    def overdue_jobs(self):
        # Check overdue jobs
        st.subheader("Overdue Jobs")
        overdue_jobs = self.jobs_df[
            (self.jobs_df["Deadline"] < self.today)
            & (self.jobs_df["Status"] != "Completed")
        ]

        if not overdue_jobs.empty:
            st.warning(f"There are {len(overdue_jobs)} overdue jobs:")
            st.dataframe(overdue_jobs)
        else:
            st.success("No overdue jobs.")
