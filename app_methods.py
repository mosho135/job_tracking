import datetime as dt
import time

import numpy as np
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from streamlit_option_menu import option_menu

# TODO: Add the name of the DTP when adding a job
# TODO: Add a delete job button.
# TODO: Add an admin page for display 1.
# TODO: Add in section for the total numner. Need to check at what point this is displayed.
# TODO: Find a better way to edit the data and update.
# TODO: Add in a download button for the data.
# TODO: Create auto saves for the data so that it doesn't get lost


class Production:
    def __init__(self):
        self.df = pd.read_csv("foilwork_jobs.csv", encoding="latin-1", low_memory=False)
        self.jobs_df = pd.DataFrame()
        self.today = pd.to_datetime(dt.datetime.today().strftime("%Y/%m/%d %H:%M:%S"))
        self.new_status = ""

    def format_data(self):
        self.df["MachineTime"] = pd.to_datetime(
            self.df["MachineTime"], format="%H:%M:%S"
        ).dt.time
        self.df["EstimatedDeliveryDate"] = pd.to_datetime(
            self.df["EstimatedDeliveryDate"]
        )
        self.df["ArtworkCompleteTime"] = pd.to_datetime(self.df["ArtworkCompleteTime"])
        self.df["CODPaymentTime"] = pd.to_datetime(self.df["CODPaymentTime"])
        self.df["CNCStartTime"] = pd.to_datetime(self.df["CNCStartTime"])
        self.df["CNCCompleteTime"] = pd.to_datetime(self.df["CNCCompleteTime"])
        self.df["FinishingCompleteTime"] = pd.to_datetime(
            self.df["FinishingCompleteTime"]
        )
        self.df["JobCompletedTime"] = pd.to_datetime(self.df["JobCompletedTime"])
        self.jobs_df = self.df.copy()

    def display_data(self, displaytype, fullname):
        from streamlit_extras.metric_cards import style_metric_cards

        self.format_data()
        if st.button("Refresh Table"):
            st.rerun()

        all_artwork_jobs = self.jobs_df.loc[
            (self.jobs_df["Status"] == "Artwork")
        ].copy()

        # Added jobs from Artwork
        pending_jobs = self.jobs_df.loc[
            (self.jobs_df["Status"] == "Artwork")
            & (self.jobs_df["DTPOperator"] == fullname)
        ].copy()

        # Jobs waiting COD Payment
        waiting_cod_payment = self.jobs_df.loc[
            (self.jobs_df["DTPOperator"] == fullname)
            & (self.jobs_df["CODStatus"] == "Not Paid")
        ].copy()

        # Ready for machine
        ready_for_machine = self.jobs_df.loc[
            self.jobs_df["Status"] == "Machining (Not Processed)"
        ].copy()

        # Display for Machine in process jobs
        cutting_in_progress = self.jobs_df.loc[
            self.jobs_df["Status"] == "Machining (In Process)"
        ].copy()

        # Display for finishing
        finishing_jobs = self.jobs_df.loc[
            self.jobs_df["Status"] == "At Finishing"
        ].copy()

        # Delivery Jobs
        delivery_jobs = self.jobs_df.loc[
            self.jobs_df["Status"] == "Ready for Delivery"
        ].copy()

        # Delivery Jobs
        delivered_jobs = self.jobs_df.loc[self.jobs_df["Status"] == "Delivered"].copy()

        # Check the display types and display to the user
        if displaytype == 1:
            with st.sidebar:
                selected = option_menu(
                    menu_title="MAIN MENU",
                    options=["Production Dashboard", "My Jobs"],
                    icons=["book", "book"],
                    menu_icon="cast",
                    default_index=0,
                    orientation="vertical",
                )

            if selected == "Production Dashboard":
                st.subheader("DASHBOARD")
                ad_col1, ad_col2, ad_col3 = st.columns(3)
                ad_col1.metric(
                    label="Jobs At Artwork",
                    value=all_artwork_jobs["Status"].count(),
                    delta="",
                )
                ad_col2.metric(
                    label="Jobs Ready to Cut",
                    value=ready_for_machine["Status"].count(),
                    delta="",
                )
                ad_col3.metric(
                    label="Jobs Currently Cutting",
                    value=cutting_in_progress["Status"].count(),
                    delta="",
                )

                as_col1, as_col2, as_col3 = st.columns(3)
                as_col1.metric(
                    label="Jobs At Finishing",
                    value=finishing_jobs["Status"].count(),
                    delta="",
                )
                as_col2.metric(
                    label="Ready for Delivery",
                    value=delivery_jobs["Status"].count(),
                    delta="",
                )
                as_col3.metric(
                    label="Delivered",
                    value=delivered_jobs["Status"].count(),
                    delta="",
                )

                style_metric_cards(
                    background_color="#ffffff",
                    border_left_color="#18334C",
                    box_shadow=True,
                )

                db_radio = st.radio(
                    label="Jobs Navigation",
                    options=[
                        "Artwork Jobs",
                        "Ready for Machine",
                        "Currently Cutting",
                        "At Finishing",
                        "Ready For Delivery",
                        "Delivered",
                    ],
                    horizontal=True,
                )

                if db_radio == "Artwork Jobs":
                    AgGrid(all_artwork_jobs, height=400, key="all_artwork_grid")
                elif db_radio == "Ready for Machine":
                    AgGrid(ready_for_machine, height=400, key="all_artwork_grid")
                elif db_radio == "Currently Cutting":
                    AgGrid(cutting_in_progress, height=400, key="all_artwork_grid")
                elif db_radio == "At Finishing":
                    AgGrid(finishing_jobs, height=400, key="all_artwork_grid")
                elif db_radio == "Ready For Delivery":
                    AgGrid(delivery_jobs, height=400, key="all_artwork_grid")
                elif db_radio == "Delivered":
                    AgGrid(delivered_jobs, height=400, key="all_artwork_grid")

            elif selected == "My Jobs":
                navigation = st.radio(
                    "Job Navigation", ["All Jobs", "Add Job"], horizontal=True
                )
                if navigation == "All Jobs":
                    at_col1, at_col2 = st.columns(2)
                    at_col1.metric(
                        label="All Current Artwork Jobs",
                        value=pending_jobs["Status"].count(),
                        delta="",
                    )
                    at_col2.metric(
                        label="Jobs Waiting COD Payement",
                        value=waiting_cod_payment["Status"].count(),
                        delta="",
                    )
                    style_metric_cards(
                        background_color="#ffffff",
                        border_left_color="#18334C",
                        box_shadow=True,
                    )

                    at_radio = st.radio(
                        label="Current Job Navigation",
                        options=["Artwork Jobs", "Waiting COD Payment"],
                        horizontal=True,
                    )

                    if at_radio == "Artwork Jobs":
                        # Display Current Artwork Jobs
                        st.subheader("All Current Jobs")
                        self.update_job(
                            pending_jobs, "Machining (Not Processed)", "artwork_grid"
                        )
                    elif at_radio == "Waiting COD Payment":
                        st.subheader("Waiting COD Payment")
                        self.update_job(waiting_cod_payment, "Paid", "cod_grid")

                elif navigation == "Add Job":
                    self.add_job(fullname=fullname)

        elif displaytype == 2:
            # Display Jobs per DTP Operator
            at_col1, at_col2 = st.columns(2)
            at_col1.metric(
                label="All Current Artwork Jobs",
                value=pending_jobs["Status"].count(),
                delta="",
            )
            at_col2.metric(
                label="Jobs Waiting COD Payement",
                value=waiting_cod_payment["Status"].count(),
                delta="",
            )
            style_metric_cards(
                background_color="#ffffff",
                border_left_color="#18334C",
                box_shadow=True,
            )

            at_radio = st.radio(
                label="Current Job Navigation",
                options=["Artwork Jobs", "Waiting COD Payment"],
                horizontal=True,
            )

            if at_radio == "Artwork Jobs":
                # Display Current Artwork Jobs
                st.subheader("All Current Jobs")
                self.update_job(
                    pending_jobs, "Machining (Not Processed)", "artwork_grid"
                )
            elif at_radio == "Waiting COD Payment":
                st.subheader("Waiting COD Payment")
                self.update_job(waiting_cod_payment, "Paid", "cod_grid")
        elif displaytype == 3:
            # Display for the machine ready jobs
            el_col1, el_col2, el_col3 = st.columns(3)
            el_col1.metric(
                label="Jobs To Cut", value=ready_for_machine["Status"].count(), delta=""
            )
            el_col2.metric(
                label="Jobs Currently Cutting",
                value=cutting_in_progress["Status"].count(),
                delta="",
            )
            el_col3.metric(
                label="Jobs At Finishing",
                value=finishing_jobs["Status"].count(),
                delta="",
            )
            style_metric_cards(
                background_color="#ffffff",
                border_left_color="#18334C",
                box_shadow=True,
            )

            el_radio = st.radio(
                label="Screen Navigation",
                options=["Ready For Machine", "Currently Cutting", "Finishing"],
                horizontal=True,
            )

            if el_radio == "Ready For Machine":
                # Display Machine Jobs
                st.subheader("Ready For Machine")
                self.update_job(
                    ready_for_machine, "Machining (In Process)", "maching_grid"
                )
            elif el_radio == "Currently Cutting":
                # Display Cutting
                st.subheader("Cutting In Process")
                self.update_job(cutting_in_progress, "At Finishing", "cutting_grid")
            elif el_radio == "Finishing":
                # Display Finishing
                st.subheader("Finishing")
                self.update_job(finishing_jobs, "Ready for Delivery", "finishing_grid")
        elif displaytype == 5:
            # Display jobs for delivery
            dl_col1, dl_col2 = st.columns(2)
            dl_col1.metric(
                label="Jobs To Deliver", value=delivery_jobs["Status"].count(), delta=""
            )
            style_metric_cards(
                background_color="#ffffff",
                border_left_color="#18334C",
                box_shadow=True,
            )
            st.subheader("Jobs to Deliver")
            self.update_job(delivery_jobs, "Delivered", "delivery_grid")

    def update_job(self, display_df, status_update, aggrid_key):
        # Create grid options
        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_selection(
            "multiple", use_checkbox=True
        )  # Enable single row selection
        grid_options = gb.build()

        # Display the grid
        grid_response = AgGrid(
            display_df,
            gridOptions=grid_options,
            enable_enterprise=False,
            height=400,
            key=aggrid_key,
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
                    for j_id in task_id:
                        if new_status == "Machining (Not Processed)":
                            self.jobs_df["Status"] = np.where(
                                self.jobs_df["Job ID"] == j_id,
                                new_status,
                                self.jobs_df["Status"],
                            )
                            self.jobs_df.loc[
                                self.jobs_df["Job ID"] == j_id, "ArtworkCompleteTime"
                            ] = {self.today}
                        elif new_status == "Machining (In Process)":
                            self.jobs_df["Status"] = np.where(
                                self.jobs_df["Job ID"] == j_id,
                                new_status,
                                self.jobs_df["Status"],
                            )
                            self.jobs_df.loc[
                                self.jobs_df["Job ID"] == j_id, "CNCStartTime"
                            ] = {self.today}
                        elif new_status == "At Finishing":
                            self.jobs_df["Status"] = np.where(
                                self.jobs_df["Job ID"] == j_id,
                                new_status,
                                self.jobs_df["Status"],
                            )
                            self.jobs_df.loc[
                                self.jobs_df["Job ID"] == j_id, "CNCCompleteTime"
                            ] = {self.today}
                        elif new_status == "Ready for Delivery":
                            cod_current_status = self.jobs_df.loc[
                                self.jobs_df["Job ID"] == j_id, "CODStatus"
                            ].sum()
                            if cod_current_status == "Not Paid":
                                new_status = "Waiting payment (COD)"

                            self.jobs_df["Status"] = np.where(
                                self.jobs_df["Job ID"] == j_id,
                                new_status,
                                self.jobs_df["Status"],
                            )
                            self.jobs_df.loc[
                                self.jobs_df["Job ID"] == j_id, "FinishingCompleteTime"
                            ] = {self.today}
                        elif new_status == "Paid":
                            current_status = self.jobs_df.loc[
                                self.jobs_df["Job ID"] == j_id, "Status"
                            ].sum()
                            self.jobs_df["CODStatus"] = np.where(
                                self.jobs_df["Job ID"] == j_id,
                                new_status,
                                self.jobs_df["CODStatus"],
                            )
                            self.jobs_df.loc[
                                self.jobs_df["Job ID"] == j_id, "CODPaymentTime"
                            ] = {self.today}
                            if current_status == "Waiting payment (COD)":
                                new_status = "Ready for Delivery"
                                self.jobs_df["Status"] = np.where(
                                    self.jobs_df["Job ID"] == j_id,
                                    new_status,
                                    self.jobs_df["Status"],
                                )

                        elif new_status == "Delivered":
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

    def add_job(self, fullname):
        # Add a new job
        self.format_data()
        st.subheader("Add New Job")
        fr_col1, fr_col2 = st.columns(2)
        with fr_col1:
            job_id = st.text_input("Job ID - Leave empty to auto increment number")
        with fr_col2:
            client = st.text_input("Client")

        sr_col1, sr_col2 = st.columns(2)
        with sr_col1:
            client_type = st.selectbox("Client Type", ["Account", "COD"])
        with sr_col2:
            cod_status = st.selectbox(
                "COD Status", ["Not Applicable", "Not Paid", "Paid"]
            )

        tr_col1, tr_col2 = st.columns(2)
        with tr_col1:
            jobname = st.text_input("Job Name")
        with tr_col2:
            size = st.text_input("Size")

        hr_col1, hr_col2, hr_col3 = st.columns(3)
        with hr_col1:
            material = st.text_input("Material")
        with hr_col2:
            machine_time = st.time_input("Machine Time")
        with hr_col3:
            status = st.selectbox(
                "Status",
                [
                    "Artwork",
                    "Machining (Not Processed)",
                    "Machining (In Process)",
                    "At Finishing",
                    "Waiting payment (COD)",
                    "Ready for Delivery",
                    "Delivered",
                ],
            )
        l_col1, l_col2 = st.columns(2)
        with l_col1:
            d_deadline = st.date_input("Estimated Delivery Date", value=self.today)
        with l_col2:
            d_time = st.time_input("Estimated Delivery Time")
        deadline = (pd.to_datetime(str(d_deadline) + " " + str(d_time))).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        if st.button("Add Job"):
            if not job_id:
                j_list = self.jobs_df["Job ID"].unique().tolist()
                j_list.sort()
                job_id = j_list[-1] + 1

            new_job = {
                "Job ID": [job_id],
                "Client": [client],
                "ClientType": [client_type],
                "JobName": [jobname],
                "Size": [size],
                "Material": [material],
                "MachineTime": [machine_time],
                "EstimatedDeliveryDate": [deadline],
                "Status": [status],
                "CODStatus": [cod_status],
                # "Progress": [
                #     0 if status == "Pending" else 50 if status == "In Progress" else 100
                # ],
                "DTPOperator": [fullname],
                "JobAddedTime": [self.today],
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
            (self.jobs_df["EstimatedDeliveryDate"] < self.today)
            & (self.jobs_df["Status"] != "Completed")
        ]

        if not overdue_jobs.empty:
            st.warning(f"There are {len(overdue_jobs)} overdue jobs:")
            st.dataframe(overdue_jobs)
        else:
            st.success("No overdue jobs.")
