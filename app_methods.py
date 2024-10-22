import datetime as dt
import time

import numpy as np
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, ColumnsAutoSizeMode, GridOptionsBuilder


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
            jobs_todo = self.jobs_df.loc[
                self.jobs_df["Progress"] != 100,
                ["Job ID", "Company", "Description", "Size", "Status", "Deadline"],
            ].copy()
            AgGrid(jobs_todo, height=200, fit_columns_on_grid_load=True)
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

    def update_job(self):
        self.format_data()
        # Job status and progress update
        st.subheader("Update Job Status")
        selected_job = st.selectbox("Select Job to Update", self.jobs_df["Job ID"])
        self.new_status = st.selectbox(
            "Update Status", ["Pending", "In Progress", "Completed"]
        )
        if st.button("Update Status"):
            self.jobs_df.loc[self.jobs_df["Job ID"] == selected_job, "Status"] = (
                self.new_status
            )
            self.jobs_df.loc[
                self.jobs_df["Job ID"] == selected_job, "JobCompletedTime"
            ] = {self.today}
            self.jobs_df.loc[self.jobs_df["Job ID"] == selected_job, "Progress"] = (
                0
                if self.new_status == "Pending"
                else 50 if self.new_status == "In Progress" else 100
            )
            self.jobs_df.to_csv("foilwork_jobs.csv", index=False)
            st.success(f"Job {selected_job} updated!")
            time.sleep(1)
            st.rerun()

    def overdue_jobs(self):
        # Check overdue jobs
        st.subheader("Overdue Jobs")
        today = dt.date.today()
        overdue_jobs = self.jobs_df[
            (self.jobs_df["Deadline"] < self.today)
            & (self.jobs_df["Status"] != "Completed")
        ]

        if not overdue_jobs.empty:
            st.warning(f"There are {len(overdue_jobs)} overdue jobs:")
            st.dataframe(overdue_jobs)
        else:
            st.success("No overdue jobs.")
