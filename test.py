import numpy as np
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

# Sample data for tasks
# tasks = [
#     {"id": 1, "task": "Task 1", "status": "Incomplete"},
#     {"id": 2, "task": "Task 2", "status": "Incomplete"},
#     {"id": 3, "task": "Task 3", "status": "Incomplete"},
# ]

# Convert tasks to DataFrame
tasks_df = pd.read_csv("test.csv", encoding="latin-1", low_memory=False)

# Streamlit app
st.title("Todo List")

# Create grid options
gb = GridOptionsBuilder.from_dataframe(tasks_df)
gb.configure_selection("multiple", use_checkbox=True)  # Enable single row selection
gridOptions = gb.build()

# Display the grid
grid_response = AgGrid(tasks_df, gridOptions=gridOptions, enable_enterprise=False)

# Get selected row data
selected_rows = pd.DataFrame(grid_response.get("selected_rows", []))
# st.write(selected_rows)

# Ensure selected_rows is not empty
if not selected_rows.empty:  # Check if there's at least one selected row
    # selected_row = selected_rows[0]  # Get the first selected row
    task_id = selected_rows["id"].tolist()
    task_status = selected_rows["status"]

    # index=0 if task_status == "Incomplete" else 1

    # Create a form to edit the status
    with st.form(key="edit_status_form"):
        new_status = "Complete"
        submit_button = st.form_submit_button(label="Update Status")

        if submit_button:
            # Update the task's status (You would typically update your data structure here)
            tasks_df["status"] = np.where(
                tasks_df["id"].isin(task_id), new_status, tasks_df["status"]
            )
            tasks_df.to_csv("test.csv", index=False)
            st.success("Task has been updated")
            st.rerun()
