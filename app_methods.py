import datetime as dt
import time
import pytz

import gspread
import numpy as np
import pandas as pd
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
from streamlit_option_menu import option_menu
from streamlit_autorefresh import st_autorefresh


south_africa_tz = pytz.timezone('Africa/Johannesburg')

@st.cache_resource
def get_gspread_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["google"], scope
    )
    client = gspread.authorize(creds)
    return client


@st.cache_data
def fetch_sheet_data(_sheet):
    worksheet = _sheet.get_all_records()
    df = pd.DataFrame(worksheet)
    return df


client = get_gspread_client()
# TODO: Change the sheet source when going live
# sheet = client.open("Foilworx_jobs").sheet1

# Test sheet
sheet = client.open("Foilworx_test").sheet1


class Production:
    def __init__(self):
        self.jobs_df = pd.DataFrame()
        self.today = pd.to_datetime(dt.datetime.now(south_africa_tz).strftime("%Y/%m/%d %H:%M"))
        self.new_status = ""

    def format_data(self):
        df = fetch_sheet_data(sheet)
        df["JobAddedTime"] = pd.to_datetime(df["JobAddedTime"])
        df["MachineTime"] = pd.to_datetime(df["MachineTime"], format="%H:%M:%S").dt.time
        df["EstimatedDeliveryDate"] = pd.to_datetime(df["EstimatedDeliveryDate"])
        df["ArtworkCompleteTime"] = pd.to_datetime(df["ArtworkCompleteTime"])
        df["CODPaymentTime"] = pd.to_datetime(df["CODPaymentTime"])
        df["CNCStartTime"] = pd.to_datetime(df["CNCStartTime"])
        df["CNCCompleteTime"] = pd.to_datetime(df["CNCCompleteTime"])
        df["FinishingCompleteTime"] = pd.to_datetime(df["FinishingCompleteTime"])
        df["ProofApprovalTime"] = pd.to_datetime(df["ProofApprovalTime"])
        df["JobCompletedTime"] = pd.to_datetime(df["JobCompletedTime"])
        self.jobs_df = df.copy()

    def display_data(self, displaytype, fullname):
        from streamlit_extras.metric_cards import style_metric_cards

        self.format_data()

        # TODO: Use the below functions to create the all button.
        def av_options(df, options):
            available_options = (
                (df[options].sort_values(ascending=True)).unique().tolist()
            )
            available_options.insert(0, -1)

            if "max_selections" not in st.session_state:
                st.session_state["max_selections"] = len(available_options)

            return available_options

        def options_select(available_options, selected_options):
            if selected_options in st.session_state:
                if -1 in st.session_state[selected_options]:
                    st.session_state[selected_options] = available_options[1:]
                    st.session_state["max_selections"] = len(available_options)
                else:
                    st.session_state["max_selections"] = len(available_options)

        # Create filters for all jobs
        def filter_all_jobs(df):
            df_selection = pd.DataFrame()
            search_more = st.checkbox(label="Search Jobs", key="show_more")
            if st.session_state.show_more:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    user_list = self.jobs_df["DTPOperator"].unique().tolist()
                    user_list.sort()
                    user_search = st.multiselect(
                        label="User",
                        options=user_list,
                        default=user_list,
                    )
                    # TODO: Use the length of the array to fill the table.
                with col2:
                    company_list = self.jobs_df["Client"].unique().tolist()
                    company_list.sort()
                    company_search = st.multiselect(
                        label="Company",
                        options=company_list,
                        default=company_list,
                    )
                with col3:
                    job_type_list = self.jobs_df["JobName"].unique().tolist()
                    job_type_list.sort()
                    job_type_search = st.multiselect(
                        label="Job Name",
                        options=job_type_list,
                        default=job_type_list,
                    )
                with col4:
                    material_list = self.jobs_df["Material"].unique().tolist()
                    material_list.sort()
                    material_search = st.multiselect(
                        label="Material",
                        options=material_list,
                        default=material_list,
                    )
                df_selection = df.query(
                    "DTPOperator==@user_search & Client==@company_search & JobName==@job_type_search & Material==@material_search"
                )
                return df_selection
            return df

        def invoice_display():
            st.sidebar.subheader("Invoice Total")
            cost_df = self.jobs_df[["TotalCost", "JobAddedTime"]].copy()
            cost_df["JobAddedTime"] = pd.to_datetime(
                pd.to_datetime(cost_df["JobAddedTime"]).dt.strftime("%Y/%m/%d")
            )
            date_default = pd.to_datetime(self.today.strftime("%Y/%m/%d"))
            with st.sidebar:
                date1, date2 = st.sidebar.columns(2)
                with date1:
                    start_date = st.sidebar.date_input("Start Date", value=date_default)
                with date2:
                    end_date = st.sidebar.date_input("End Date", value=date_default)

                cost_selection = cost_df.query(
                    "JobAddedTime>=@start_date & JobAddedTime<=@end_date"
                )

                # st.dataframe(cost_selection)
                st.metric(
                    label="Invoice Total",
                    value=cost_selection["TotalCost"].sum(),
                    delta="",
                )

        # Refresh button for all users
        # TODO: show the button to all but the dashboard view
        if st.button("Refresh Table"):
            st.cache_data.clear()
            st.rerun()

        all_artwork_jobs = self.jobs_df.loc[
            (self.jobs_df["Status"] == "Artwork")
        ].copy()

        # Added jobs from Artwork
        pending_jobs = self.jobs_df.loc[
            (self.jobs_df["Status"].isin(['Artwork', "Artwork Only"]))
            & (self.jobs_df["DTPOperator"] == fullname)
        ].copy()

        # Waiting Proof approval data
        proof_approval = self.jobs_df.loc[
            self.jobs_df["Status"] == "Waiting Approval"
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

        # Display for QC
        qc_jobs = self.jobs_df.loc[
            self.jobs_df["Status"] == "Ready For QC"
        ].copy()

        # Delivery Jobs
        delivery_jobs = self.jobs_df.loc[
            self.jobs_df["Status"] == "Ready for Delivery"
        ].copy()

        # Delivery Jobs
        delivered_jobs = self.jobs_df.loc[self.jobs_df["Status"] == "Delivered"].copy()

        # Delivered Today
        delivered_today = delivered_jobs.loc[delivered_jobs['JobCompletedTime'] >= self.today.strftime("%Y-%m-%d")].copy()

        # Get the current machine in use
        def machineinuse(df, mac_color, output_need):
            mac_df = df.loc[
                (df["MachineInUse"] == mac_color)
                & (df["Status"] == "Machining (In Process)")
            ].copy()

            if output_need == "count":
                mac_count = mac_df["MachineInUse"].count()
                return mac_count
            elif output_need == "invoice":
                job_list = mac_df["Inv No"].tolist()
                if len(job_list) == 1:
                    mac_invoice = mac_df["Inv No"].sum()
                    return str(mac_invoice)
                elif len(job_list) > 1:
                    mac_invoice = ""
                    for inv in job_list:
                        mac_invoice = mac_invoice + " | " + str(inv)
                    return mac_invoice

        def machine_metrics():
            st.sidebar.metric(
                label="Machine - Mufasa",
                value=machineinuse(self.jobs_df, "Mufasa", "count"),
                delta=machineinuse(self.jobs_df, "Mufasa", "invoice"),
            )
            st.sidebar.metric(
                label="Machine - Logo",
                value=machineinuse(self.jobs_df, "Logo", "count"),
                delta=machineinuse(self.jobs_df, "Logo", "invoice"),
            )
            st.sidebar.metric(
                label="Machine - Fresenius",
                value=machineinuse(self.jobs_df, "Fresenius", "count"),
                delta=machineinuse(self.jobs_df, "Fresenius", "invoice"),
            )
            st.sidebar.metric(
                label="Machine - Simba",
                value=machineinuse(self.jobs_df, "Simba", "count"),
                delta=machineinuse(self.jobs_df, "Simba", "invoice"),
            )
            st.sidebar.metric(
                label="Machine - Missy",
                value=machineinuse(self.jobs_df, "Missy", "count"),
                delta=machineinuse(self.jobs_df, "Missy", "invoice"),
            )

            style_metric_cards(
                background_color="#ffffff",
                border_left_color="#18334C",
                box_shadow=True,
            )

        # Create sidebar menu
        def sidebar_option_menu(m_options, icon_count):
            m_icons = []
            for i in range(icon_count):
                m_icons.append("book")

            with st.sidebar:
                selected = option_menu(
                    menu_title="MAIN MENU",
                    options=m_options,
                    icons=m_icons,
                    menu_icon="cast",
                    orientation="vertical",
                )
            return selected

        def dashboard_metrics():
            st.subheader("DASHBOARD")
            da_col1, da_col2, da_col3 = st.columns(3)
            da_col1.metric(
                label="Jobs At Artwork",
                value=all_artwork_jobs["Status"].count(),
                delta="",
            )
            da_col2.metric(
                label="Waiting Artwork Approval",
                value=proof_approval["Status"].count(),
                delta="",
            )
            da_col3.metric(
                label="Waiting C.O.D Payment",
                value=waiting_cod_payment["Status"].count(),
                delta="",
            )

            ds_col1, ds_col2, ds_col3 = st.columns(3)
            ds_col1.metric(
                label="Jobs Ready to Cut",
                value=ready_for_machine["Status"].count(),
                delta="",
            )
            ds_col2.metric(
                label="Jobs Currently Cutting",
                value=cutting_in_progress["Status"].count(),
                delta="",
            )
            ds_col3.metric(
                label="Jobs At Finishing",
                value=finishing_jobs["Status"].count(),
                delta="",
            )
            df_col1, df_col2, df_col3 = st.columns(3)
            df_col1.metric(
                label="Ready For QC",
                value=qc_jobs["Status"].count(),
                delta="",
            )
            df_col2.metric(
                label="Ready for Delivery",
                value=delivery_jobs["Status"].count(),
                delta="",
            )
            df_col3.metric(
                label="Delivered",
                value=delivered_today["Status"].count(),
                delta="",
            )


            style_metric_cards(
                background_color="#ffffff",
                border_left_color="#18334C",
                box_shadow=True,
            )

        # Check the display types and display to the user
        # Admin User Dashboard
        if displaytype == 6:
            st_autorefresh(interval=60_000, key="auto_refresh")
            st.sidebar.markdown("<h4>Machines Currently In Use</h4>", unsafe_allow_html=True)
            machine_metrics()
            # Auto refresh the data
            dashboard_metrics()

        elif displaytype == 1:
            menu_items = ["Production Dashboard", "My Jobs"]
            selected = sidebar_option_menu(menu_items, len(menu_items))

            machine_metrics()
            invoice_display()

            if selected == "Production Dashboard":
                dashboard_metrics()

                db_radio = st.radio(
                    label="Jobs Navigation",
                    options=[
                        "Jobs At Artwork",
                        "Waiting Artwork Approval",
                        "Waiting C.O.D Payment",
                        "Ready to Cut",
                        "Currently Cutting",
                        "At Finishing",
                        "Ready For QC",
                        "Ready For Delivery",
                        "Delivered",
                    ],
                    horizontal=True,
                )

                if db_radio == "Jobs At Artwork":
                    AgGrid(all_artwork_jobs, height=400, key="all_artwork_grid")
                elif db_radio == "Waiting Artwork Approval":
                    AgGrid(proof_approval, height=400, key="all_artwork_grid")
                elif db_radio == "Waiting C.O.D Payment":
                    AgGrid(waiting_cod_payment, height=400, key="all_artwork_grid")
                elif db_radio == "Ready to Cut":
                    AgGrid(ready_for_machine, height=400, key="all_artwork_grid")
                elif db_radio == "Currently Cutting":
                    AgGrid(cutting_in_progress, height=400, key="all_artwork_grid")
                elif db_radio == "At Finishing":
                    AgGrid(finishing_jobs, height=400, key="all_artwork_grid")
                elif db_radio == "Ready For QC":
                    AgGrid(qc_jobs, height=400, key="all_artwork_grid")
                elif db_radio == "Ready For Delivery":
                    AgGrid(delivery_jobs, height=400, key="all_artwork_grid")
                elif db_radio == "Delivered":
                    AgGrid(delivered_today, height=400, key="all_artwork_grid")

            elif selected == "My Jobs":
                navigation = st.radio(
                    "Job Navigation", ["All Jobs", "Add Job"], horizontal=True
                )
                if navigation == "All Jobs":
                    at_col1, at_col2, at_col3, at_col4, at_col5 = st.columns(5)
                    at_col1.metric(
                        label="Pending",
                        value=pending_jobs["Status"].count(),
                        delta="",
                    )
                    at_col2.metric(
                        label="Ready to cut",
                        value=proof_approval["Status"].count(),
                        delta="",
                    )
                    at_col3.metric(
                        label="Awaiting C.O.D Payment",
                        value=waiting_cod_payment["Status"].count(),
                        delta="",
                    )
                    at_col4.metric(
                        label="Currently Cutting",
                        value=cutting_in_progress["Status"].count(),
                        delta="",
                    )
                    at_col5.metric(
                        label="Ready For QC",
                        value=qc_jobs["Status"].count(),
                        delta="",
                    )

                    style_metric_cards(
                        background_color="#ffffff",
                        border_left_color="#18334C",
                        box_shadow=True,
                    )

                    atl_radio = st.radio(
                        label="Current Job Navigation",
                        options=[
                            "Pending",
                            "Ready to cut",
                            "Awaiting C.O.D Payment",
                            "Currently Cutting",
                            "Ready for QC",
                        ],
                        horizontal=True,
                    )

                    if atl_radio == "Pending":
                        # Display Current Artwork Jobs
                        st.subheader("Pending Jobs")
                        self.update_job(
                            pending_jobs, "Waiting Approval", "artwork_grid"
                        )
                    elif atl_radio == "Ready to cut":
                        st.subheader("Ready to cut")
                        self.update_job(
                            proof_approval, "Machining (Not Processed)", "proof_grid"
                        )
                    elif atl_radio == "Awaiting C.O.D Payment":
                        st.subheader("Awaiting C.O.D Payment")
                        self.update_job(waiting_cod_payment, "Paid", "cod_grid")
                    elif atl_radio == "Currently Cutting":
                        st.subheader("Currently Cutting")
                        AgGrid(cutting_in_progress, height=400, key="cur_cutting_grid")
                    elif atl_radio == "Ready for QC":
                        st.subheader("Ready For QC")
                        AgGrid(qc_jobs, height=400, key="qc_cur_grid")

                elif navigation == "Add Job":
                    self.add_job(fullname=fullname)

        elif displaytype == 2:
            menu_items = ["My Jobs", "All Jobs"]
            selected = sidebar_option_menu(menu_items, len(menu_items))

            # Get the machine in use metrics
            st.sidebar.subheader("Machines Currently in Use")
            machine_metrics()
            invoice_display()

            if selected == "My Jobs":
                at_radio = st.radio(
                    label="Job Navigation",
                    options=["All Jobs", "Add Job"],
                    horizontal=True,
                )
                if at_radio == "All Jobs":
                    # Display Jobs per DTP Operator
                    at_col1, at_col2, at_col3, at_col4, at_col5 = st.columns(5)
                    at_col1.metric(
                        label="Pending",
                        value=pending_jobs["Status"].count(),
                        delta="",
                    )
                    at_col2.metric(
                        label="Ready to cut",
                        value=proof_approval["Status"].count(),
                        delta="",
                    )
                    at_col3.metric(
                        label="Awaiting C.O.D Payment",
                        value=waiting_cod_payment["Status"].count(),
                        delta="",
                    )
                    at_col4.metric(
                        label="Currently Cutting",
                        value=cutting_in_progress["Status"].count(),
                        delta="",
                    )
                    at_col5.metric(
                        label="Ready For QC",
                        value=qc_jobs["Status"].count(),
                        delta="",
                    )

                    style_metric_cards(
                        background_color="#ffffff",
                        border_left_color="#18334C",
                        box_shadow=True,
                    )

                    atl_radio = st.radio(
                        label="Current Job Navigation",
                        options=[
                            "Pending",
                            "Ready to cut",
                            "Awaiting C.O.D Payment",
                            "Currently Cutting",
                            "Ready for QC",
                        ],
                        horizontal=True,
                    )

                    if atl_radio == "Pending":
                        # Display Current Artwork Jobs
                        st.subheader("Pending Jobs")
                        self.update_job(
                            pending_jobs, "Waiting Approval", "artwork_grid"
                        )
                    elif atl_radio == "Ready to cut":
                        st.subheader("Ready to cut")
                        self.update_job(
                            proof_approval, "Machining (Not Processed)", "proof_grid"
                        )
                    elif atl_radio == "Awaiting C.O.D Payment":
                        st.subheader("Awaiting C.O.D Payment")
                        self.update_job(waiting_cod_payment, "Paid", "cod_grid")
                    elif atl_radio == "Currently Cutting":
                        st.subheader("Currently Cutting")
                        AgGrid(cutting_in_progress, height=400, key="cur_cutting_grid")
                    elif atl_radio == "Ready for QC":
                        st.subheader("Ready For QC")
                        AgGrid(qc_jobs, height=400, key="qc_cur_grid")


                elif at_radio == "Add Job":
                    self.add_job(fullname)
            elif selected == "All Jobs":
                st.subheader("All Jobs")
                job_selection = filter_all_jobs(self.jobs_df)
                gb = GridOptionsBuilder.from_dataframe(job_selection)
                gb.configure_selection("multiple", use_checkbox=True)
                gb.configure_default_column(editable=True)
                gridOptions = gb.build()

                all_grid_response = AgGrid(
                    job_selection,
                    gridOptions=gridOptions,
                    height=1000,
                    update_mode=GridUpdateMode.MODEL_CHANGED,
                    key="all_jobs_grid",
                )

                # Download button
                @st.cache_data
                def convert_to_csv(df):
                    return df.to_csv(index=False).encode("utf-8")

                csv = convert_to_csv(job_selection)

                aj_col1, aj_col2, aj_col3 = st.columns([0.5, 1.5, 1.5])

                with aj_col1:
                    download1 = st.download_button(
                        label="Download",
                        data=csv,
                        file_name=f"foilworx-download-{self.today}.csv",
                        mime="text/csv",
                    )
                with aj_col2:
                    save_button = st.button("Save Updates")

                if save_button:
                    ag_data = pd.DataFrame(all_grid_response["data"])

                    common_columns = self.jobs_df.columns.intersection(ag_data.columns)

                    for _, row in ag_data.iterrows():
                        mask = self.jobs_df["id"] == row["id"]

                        if mask.any():
                            for column in common_columns:
                                self.jobs_df.loc[mask, column] = row[column]

                    self.jobs_df = self.jobs_df.astype(str)
                    sheet.update(
                        [self.jobs_df.columns.values.tolist()]
                        + self.jobs_df.values.tolist()
                    )
                    st.success("Updated")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()

                # Create the deleting job section for all jobs
                select_rows = pd.DataFrame(all_grid_response.get("selected_rows", []))

                if not select_rows.empty:
                    selected_id = select_rows["id"].tolist()

                    with aj_col3:
                        delete_button = st.button("Delete Job")

                    if delete_button:
                        for i_id in selected_id:
                            jobs_to_delete = self.jobs_df.loc[
                                self.jobs_df["id"] == i_id
                            ].index

                            # Adjust index for Google Sheets (1-based indexing)
                            rows_to_delete = [
                                index + 2 for index in jobs_to_delete
                            ]  # +2 to skip the header row

                            # Delete rows in reverse order to avoid shifting issues
                            for row in sorted(rows_to_delete, reverse=True):
                                sheet.delete_rows(row)

                        st.success("Job has been deleted")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()

        elif displaytype == 3:
            # Display for the machine ready jobs
            el_col1, el_col2, el_col3, el_col4, el_col5 = st.columns(5)
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
            el_col4.metric(
                label="Jobs Ready for QC",
                value=qc_jobs["Status"].count(),
                delta="",
            )
            el_col5.metric(
                label="Jobs Ready for Delivery",
                value=delivery_jobs["Status"].count(),
                delta="",
            )
            style_metric_cards(
                background_color="#ffffff",
                border_left_color="#18334C",
                box_shadow=True,
            )

            el_radio = st.radio(
                label="Screen Navigation",
                options=["Ready For Machine", "Currently Cutting", "Finishing", "Ready For QC", "Ready For Delivery"],
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
                self.update_job(finishing_jobs, "Ready For QC", "finishing_grid")
            elif el_radio == "Ready For QC":
                st.subheader("Quality Checks")
                self.update_job(qc_jobs, "Ready for Delivery", "qc_grid")
            elif el_radio == "Ready For Delivery":
                st.subheader("Ready For Delivery")
                delivery_jobs['OverdueCheck'] = np.where(delivery_jobs['EstimatedDeliveryDate'] < self.today.strftime("%Y-%m-%d"), "Overdue", "NotDue")
                gb = GridOptionsBuilder.from_dataframe(delivery_jobs)

                jscode = JsCode("""
                function(params) {
                    if (params.data.JobPriority === 'Urgent'){
                        return {backgroundColor: '#FEB973'};    
                    } else if (params.data.OverdueCheck === 'Overdue'){
                        return {backgroundColor: '#FF6F6F'}
                    }
                    return {};
                }
                """)
                grid_options = gb.build()
                grid_options['getRowStyle'] = jscode

                # Display the grid
                grid_response = AgGrid(
                    delivery_jobs,
                    gridOptions=grid_options,
                    allow_unsafe_jscode=True,
                    enable_enterprise=False,
                    height=400,
                    key="delivery_jobs_grid",
                )

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
        display_df['OverdueCheck'] = np.where(display_df['EstimatedDeliveryDate'] < self.today.strftime("%Y-%m-%d"), "Overdue", "NotDue")
        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_selection(
            "multiple", use_checkbox=True
        )  # Enable single row selection

        jscode = JsCode("""
        function(params) {
            if (params.data.JobPriority === 'Urgent'){
                return {backgroundColor: '#FEB973'};    
            } else if (params.data.Status != 'Artwork' && params.data.Status != 'Artwork Only'){
                if (params.data.OverdueCheck === 'Overdue'){
                    return {backgroundColor: '#FF6F6F'}
                }
            }
            return {};
        }
        """)
        grid_options = gb.build()
        grid_options['getRowStyle'] = jscode

        # Display the grid
        grid_response = AgGrid(
            display_df,
            gridOptions=grid_options,
            allow_unsafe_jscode=True,
            enable_enterprise=False,
            height=400,
            key=aggrid_key,
        )

        # Get selected row data
        selected_rows = pd.DataFrame(grid_response.get("selected_rows", []))
        # st.write(selected_rows)

        # Ensure selected_rows is not empty
        if not selected_rows.empty:  # Check if there's at least one selected row
            task_id = selected_rows["id"].tolist()
            st.write(task_id)

            # Create a form to edit the status
            new_status = status_update
            machine_choice = ""
            total_cost = 0
            current_material = self.jobs_df.loc[
                self.jobs_df["id"] == task_id[0], "Material"
            ].sum()
            material_change = ""
            job_id = 0
            new_inv = 0
            size_change = ""
            if new_status == "Machining (Not Processed)":
                current_inv = self.jobs_df.loc[
                    (self.jobs_df["Inv No"].notnull())
                ].copy()
                num_list = current_inv["Inv No"].unique().tolist()
                num_list.sort()
                new_inv = int(num_list[-1]) + 1
                inv_no = self.jobs_df.loc[
                    self.jobs_df["id"] == task_id[0], "Inv No"
                ].sum()
                current_size = self.jobs_df.loc[
                    self.jobs_df["id"] == task_id[0], "Size"
                ].sum()

                # All Changes into one row
                cu_col1, cu_col2, cu_col3, cu_col4 = st.columns(4)
                with cu_col1:
                    job_id = st.number_input(
                        "Inv No",
                        value=inv_no,
                    )
                with cu_col2:
                    total_cost = st.number_input("Job Cost")
                with cu_col3:
                    material_change = st.text_input(
                        label="Material", value=current_material
                    )
                with cu_col4:
                    size_change = st.text_input(label="Size", value=current_size)

            if new_status == "Machining (In Process)":
                machine_choice = st.selectbox(
                    "Choose Machine", ["Mufasa", "Logo", "Fresenius", "Simba", "Missy"]
                )

            btn_col1, btn_col2 = st.columns([0.5, 3])
            with btn_col1:
                submit_button = st.button("Update Status")

            if submit_button:
                for j_id in task_id:
                    current_status = self.jobs_df.loc[
                        self.jobs_df["id"] == j_id, "Status"
                    ].sum()
                    current_jobtype = self.jobs_df.loc[
                        self.jobs_df["id"] == j_id, "JobType"
                    ].sum()
                    current_client_type = self.jobs_df.loc[self.jobs_df['id'] == j_id, "ClientType"].sum()
                    if new_status == "Waiting Approval":
                        self.jobs_df["Status"] = np.where(
                            self.jobs_df["id"] == j_id,
                            new_status,
                            self.jobs_df["Status"],
                        )
                        self.jobs_df.loc[
                            self.jobs_df["id"] == j_id, "ProofApprovalTime"
                        ] = {self.today}
                    elif new_status == "Machining (Not Processed)":
                        self.jobs_df["Inv No"] = np.where(
                            self.jobs_df["id"] == j_id,
                            np.where(job_id == 0, new_inv, job_id),
                            self.jobs_df["Inv No"],
                        )
                        self.jobs_df["TotalCost"] = np.where(
                            self.jobs_df["id"] == j_id,
                            total_cost,
                            self.jobs_df["TotalCost"],
                        )
                        self.jobs_df["Material"] = np.where(
                            self.jobs_df["id"] == j_id,
                            material_change,
                            self.jobs_df["Material"],
                        )
                        self.jobs_df["Size"] = np.where(
                            self.jobs_df["id"] == j_id,
                            size_change,
                            self.jobs_df["Size"],
                        )
                        self.jobs_df["Proof"] = np.where(
                            self.jobs_df["id"] == j_id,
                            "Approved",
                            self.jobs_df["Proof"],
                        )
                        if current_jobtype == "Artwork Only":
                            self.jobs_df["Status"] = np.where(
                                self.jobs_df["id"] == j_id,
                                "Delivered",
                                self.jobs_df["Status"],
                            )
                            self.jobs_df.loc[
                                self.jobs_df["id"] == j_id, "JobCompletedTime"
                            ] = {self.today}
                        else:
                            self.jobs_df["Status"] = np.where(
                                self.jobs_df["id"] == j_id,
                                new_status,
                                self.jobs_df["Status"],
                            )
                        self.jobs_df.loc[
                            self.jobs_df["id"] == j_id, "ArtworkCompleteTime"
                        ] = {self.today}
                    elif new_status == "Machining (In Process)":
                        self.jobs_df["MachineInUse"] = np.where(
                            self.jobs_df["id"] == j_id,
                            machine_choice,
                            self.jobs_df["MachineInUse"],
                        )
                        self.jobs_df["Status"] = np.where(
                            self.jobs_df["id"] == j_id,
                            new_status,
                            self.jobs_df["Status"],
                        )
                        self.jobs_df.loc[
                            self.jobs_df["id"] == j_id, "CNCStartTime"
                        ] = {self.today}
                    elif new_status == "At Finishing":
                        self.jobs_df["Status"] = np.where(
                            self.jobs_df["id"] == j_id,
                            new_status,
                            self.jobs_df["Status"],
                        )
                        self.jobs_df.loc[
                            self.jobs_df["id"] == j_id, "CNCCompleteTime"
                        ] = {self.today}
                    elif new_status == "Ready For QC":
                        self.jobs_df["Status"] = np.where(
                            self.jobs_df["id"] == j_id,
                            new_status,
                            self.jobs_df["Status"],
                        )
                        self.jobs_df.loc[
                            self.jobs_df["id"] == j_id, "FinishingCompleteTime"
                        ] = {self.today}
                    elif new_status == "Ready for Delivery":
                        cod_current_status = self.jobs_df.loc[
                            self.jobs_df["id"] == j_id, "CODStatus"
                        ].sum()
                        if cod_current_status == "Not Paid":
                            new_status = "Waiting payment (COD)"

                        self.jobs_df["Status"] = np.where(
                            self.jobs_df["id"] == j_id,
                            new_status,
                            self.jobs_df["Status"],
                        )
                        self.jobs_df.loc[
                            self.jobs_df["id"] == j_id, "QCCompleteTime"
                        ] = {self.today}

                    elif new_status == "Paid":
                        self.jobs_df["CODStatus"] = np.where(
                            self.jobs_df["id"] == j_id,
                            new_status,
                            self.jobs_df["CODStatus"],
                        )
                        self.jobs_df.loc[
                            self.jobs_df["id"] == j_id, "CODPaymentTime"
                        ] = {self.today}
                        if current_status == "Waiting payment (COD)":
                            new_status = "Ready for Delivery"
                            self.jobs_df["Status"] = np.where(
                                self.jobs_df["id"] == j_id,
                                new_status,
                                self.jobs_df["Status"],
                            )

                    elif new_status == "Delivered":
                        self.jobs_df["Status"] = np.where(
                            self.jobs_df["id"] == j_id,
                            new_status,
                            self.jobs_df["Status"],
                        )
                        self.jobs_df.loc[
                            self.jobs_df["id"] == j_id, "JobCompletedTime"
                        ] = {self.today}
                    self.jobs_df = self.jobs_df.astype(str)
                    sheet.update(
                        [self.jobs_df.columns.values.tolist()]
                        + self.jobs_df.values.tolist()
                    )
                st.success("Job has been updated")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()

            if new_status in (
                "Artwork",
                "Waiting Approval",
                "Machining (Not Processed)",
            ):
                with btn_col2:
                    delete_button = st.button("Delete Job")
                if delete_button:
                    for i_id in task_id:
                        jobs_to_delete = self.jobs_df.loc[
                            self.jobs_df["id"] == i_id
                        ].index

                        # Adjust index for Google Sheets (1-based indexing)
                        rows_to_delete = [
                            index + 2 for index in jobs_to_delete
                        ]  # +2 to skip the header row

                        # Delete rows in reverse order to avoid shifting issues
                        for row in sorted(rows_to_delete, reverse=True):
                            sheet.delete_rows(row)

                    st.success("Job has been deleted")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()

            if new_status in (
                "At Finishing",
                "Ready For QC",
                "Ready for Delivery",
                "Delivered",
            ):
                with btn_col2:
                    reverse_button = st.button("Reverse Status")
                if reverse_button:
                    for i_id in task_id:
                        if new_status == 'At Finishing':
                            self.jobs_df["Status"] = np.where(
                                self.jobs_df["id"] == i_id, "Machining (Not Processed)",
                                self.jobs_df["Status"],
                            )
                        elif new_status == 'Ready For QC':
                            self.jobs_df["Status"] = np.where(
                                self.jobs_df["id"] == i_id, "Machining (In Process)",
                                self.jobs_df["Status"],
                            )
                        elif new_status == 'Ready for Delivery':
                            self.jobs_df["Status"] = np.where(
                                self.jobs_df["id"] == i_id, "At Finishing",
                                self.jobs_df["Status"],
                            )
                        elif new_status == 'Delivered':
                            self.jobs_df["Status"] = np.where(
                                self.jobs_df["id"] == i_id, "Ready For QC",
                                self.jobs_df["Status"],
                            )
                        self.jobs_df = self.jobs_df.astype(str)
                        sheet.update(
                            [self.jobs_df.columns.values.tolist()]
                            + self.jobs_df.values.tolist()
                        )
                    st.success("Job has been reversed")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                

    def add_job(self, fullname):
        # Add a new job
        st.subheader("Add New Job")
        fr_col1, fr_col2 = st.columns(2)
        with fr_col1:
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
            jobtype = st.selectbox(
                "Job Type",
                [
                    "Normal",
                    "Artwork Only",
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

        cc_col1, cc_col2 = st.columns(2)
        with cc_col1:
            job_priority = st.selectbox("Priority", ["Normal", "Urgent"])
        with cc_col2:
            job_cost = st.number_input("Job Cost")

        if st.button("Add Job"):
            self.format_data()
            j_list = self.jobs_df["id"].unique().tolist()
            j_list.sort()
            wid = j_list[-1] + 1

            if client_type == "COD" and cod_status == "Not Applicable":
                cod_status = "Not Paid"

            new_job = {
                "id": [wid],
                "Client": [client],
                "ClientType": [client_type],
                "JobName": [jobname],
                "Size": [size],
                "Material": [material],
                "MachineTime": [machine_time],
                "EstimatedDeliveryDate": [deadline],
                "JobType": [jobtype],
                "Status": ["Artwork"],
                "CODStatus": [cod_status],
                "DTPOperator": [fullname],
                "JobAddedTime": [self.today],
                "JobPriority": [job_priority],
                "TotalCost": [job_cost],
            }
            new_job_df = pd.DataFrame(new_job)
            self.jobs_df = pd.concat([self.jobs_df, new_job_df], ignore_index=True)
            self.jobs_df = self.jobs_df.astype(str)
            sheet.update(
                [self.jobs_df.columns.values.tolist()] + self.jobs_df.values.tolist()
            )
            # self.jobs_df.to_csv("foilwork_jobs.csv", index=False)
            st.success(f"Job {wid} added!")
            st.cache_data.clear()
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
