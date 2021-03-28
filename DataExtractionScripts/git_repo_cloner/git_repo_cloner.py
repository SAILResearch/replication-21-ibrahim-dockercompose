#This script clones the github repositories using 15 different github accounts by turn

import os
import time
import pandas as pd

print(os.getcwd())

#change this directory to your desired path where the repositories will be cloned
base_directory = "D:/Projects/wip-19-ibrahim-docker_compose-code/Data/Docker-Compose-Repositories"

os.chdir(base_directory)

#compose_projects_file_path = "../root_compose_projects.csv"
compose_projects_file_path = "root_compose_projects_commit_count_100.csv"
github_accounts_file_path = "github_accounts.csv"

compose_projects = pd.read_csv(compose_projects_file_path)


github_account_credentials = pd.read_csv(github_accounts_file_path)

i = 0
start_index = 0
could_not_clone = 0

for index, row in compose_projects.iterrows():
    i += 1
    if start_index > i:
        continue

    print("index: %s " % i)
    current_username = github_account_credentials.iloc[i % 15]['username']
    current_password = github_account_credentials.iloc[i % 15]['password']
    current_credentials = "//"+current_username+":"+current_password+"@"

    clone_url = row['url'].replace('//api.', current_credentials).replace('/repos/', '/')+".git"
    owner = str(row['owner_id'])

    os.chdir(base_directory)

    try:
        os.mkdir(owner)
    except:
        print("already exists!")

    os.chdir(base_directory + "/" + owner)

    start_time = time.time()
    try:
        os.system('git clone ' + clone_url)
    except:
        print("error in cloning: index %s" % i)
        could_not_clone += 1
    print("time taken %s minutes" % ((time.time() - start_time) / 60))

print(f"could not clone: {could_not_clone} out of {i} projects.")