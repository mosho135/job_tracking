import pandas as pd

user_list = pd.read_csv("foilworx_userlist.csv")
username = user_list.loc[user_list["username"] == "shivaanh", "fullname"].sum()
print(username)
