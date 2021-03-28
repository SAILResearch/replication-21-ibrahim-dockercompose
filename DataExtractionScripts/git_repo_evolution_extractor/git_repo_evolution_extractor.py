import os
import subprocess
import yaml
from deepdiff import DeepDiff
import pandas as pd


repository_base_paths = ["D:/Projects/Docker-Compose-Repositories", "C:/Docker-compose_repositories-2"]

output_files_root_path = "D:/Projects/wip-19-ibrahim-docker_compose-code/Data"
general_history_output_file_path = f"{output_files_root_path}/compose_project_evolution.csv"
feature_change_output_file_path = f"{output_files_root_path}/feature_changes_by_commit.csv"
image_change_output_file_path = f"{output_files_root_path}/image_changes_by_commit.csv"
version_change_output_file_path = f"{output_files_root_path}/version_changes_by_commit.csv"
number_of_images_change_output_file_path = f"{output_files_root_path}/number_of_image_changes_by_commit.csv"


def get_path_and_size(start_path):
    total_size = 0
    paths_and_size = []
    for dir_path, dir_names, file_names in os.walk(start_path):
        for f in file_names:
            fp = os.path.join(dir_path, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                size = os.path.getsize(fp)
                total_size += size
                if f == "docker-compose.yml":
                    paths_and_size.append({"path": fp, "size": size})
    return paths_and_size, total_size


def get_changed_files_in_a_commit(commit_hash):
    changed_files = subprocess.Popen(f"git diff-tree --no-commit-id --name-only -r {commit_hash}", shell=True, stdout=subprocess.PIPE).stdout.read().decode()
    files = changed_files.split("\n")
    files = [file.split('/').pop() for file in files if file.strip()]

    return '"{}"'.format(','.join(files).replace("\"", "'")), len(files)


def get_commits(commit_log_message):
    commits_list = []
    for commit_detail in str(commit_log_message).split("\n\n"):
        commit_info = {}
        line_index = 0
        for line in str(commit_detail).split('\n'):

            if line_index == 0:
                metadata = line.split("|")
                if len(metadata) > 0:
                    commit_info["commit_hash"] = metadata[0]
                else:
                    commit_info["commit_hash"] = ""

                if len(metadata) > 1:
                    commit_info["commiter_email"] = metadata[1]
                else:
                    commit_info["commiter_email"] = ""

                if len(metadata) > 2:
                    commit_info["commit_date"] = metadata[2]
                else:
                    commit_info["commit_date"] = ""

                if len(metadata) > 3:
                    commit_info["commit_subject"] = metadata[3]
                else:
                    commit_info["commit_subject"] = ""

            elif line_index == 1:
                stat_split = line.split("|")
                if len(stat_split) > 1:
                    stat = stat_split[1]
                    commit_info["lines_inserted"] = stat.count("+")
                    commit_info["lines_deleted"] = stat.count("-")
                else:
                    commit_info["lines_inserted"] = ""
                    commit_info["lines_deleted"] = ""

            commit_info["changed_files"], commit_info["number_of_files_changed"] = get_changed_files_in_a_commit(metadata[0])

            line_index += 1
        commits_list.append(commit_info)
    return commits_list


def write_all_csv_to_files(general_history_csv_param, commit_changes_csv_param, image_changes_csv_param,
                           version_changes_csv_param, number_of_images_changes_csv_param):
    with open(general_history_output_file_path, 'a', encoding='utf-8') as file1:
        file1.write(general_history_csv_param)

    with open(feature_change_output_file_path, 'a', encoding='utf-8') as file2:
        file2.write(commit_changes_csv_param)

    with open(image_change_output_file_path, 'a', encoding='utf-8') as file3:
        file3.write(image_changes_csv_param)

    with open(version_change_output_file_path, 'a', encoding='utf-8') as file4:
        file4.write(version_changes_csv_param)

    with open(number_of_images_change_output_file_path, 'a', encoding='utf-8') as file5:
        file5.write(number_of_images_changes_csv_param)


def get_number_of_images(compose_json):
    number_of_images = 0
    if isinstance(compose_json, dict):

        for key in compose_json:
            json_element = compose_json[key]
            if key == "image" or key == "build":
                number_of_images += 1
                break

            if isinstance(json_element, dict):

                for key2 in json_element:
                    json_element_2 = json_element[key2]
                    if key2 == "image" or key2 == "build":
                        number_of_images += 1
                        break

                    if isinstance(json_element_2, dict):
                        for key3 in json_element_2:
                            if key3 == "image" or key3 == "build":
                                number_of_images += 1
                                break

    return number_of_images


def get_file_by_commit_hash(commit_hash, relative_file_path):
    return subprocess.Popen(
        f"git show {commit_hash}:{relative_file_path}",
        shell=True, stdout=subprocess.PIPE).stdout.read().decode()


def get_diff(commit_old, commit_new, relative_file_path, csv_row_prefix):
    feature_diff_csv_local = ""
    image_diff_csv_local = ""
    version_diff_csv_local = ""

    commit_hash_old = commit_old.get("commit_hash", "")
    commit_hash_new = commit_new.get("commit_hash", "")

    if not (commit_hash_old and commit_hash_new):
        return ""

    old_file = get_file_by_commit_hash(commit_hash_old, relative_file_path)

    new_file = get_file_by_commit_hash(commit_hash_new, relative_file_path)

    old_file_json = {}
    try:
        old_file_json = yaml.safe_load(old_file)
    except yaml.YAMLError as exc:
        print(exc)

    new_file_json = {}
    try:
        new_file_json = yaml.safe_load(new_file)
    except yaml.YAMLError as exc:
        print(exc)

    diffs = DeepDiff(old_file_json, new_file_json)

    for status in diffs:
        changes = diffs[status]
        for changed_key in changes:
            key = changed_key
            changed_key = changed_key[5:len(changed_key) - 1]
            features_splits = changed_key.split("][")
            if not features_splits[-1].isdigit():
                changed_feature = features_splits[-1]
            else:
                changed_feature = features_splits[-2]

            changed_feature = changed_feature.replace("'", "")

            if changed_feature == "image" and status == "values_changed":
                image = changes[key]
                image_diff_csv_local += ','.join([csv_row_prefix, image['old_value'], image['new_value']]) + "\n"

            if changed_feature == "version" and status == "values_changed":
                version = changes[key]
                version_diff_csv_local += ','.join([csv_row_prefix, version['old_value'], version['new_value']]) + "\n"

            feature_diff_csv_local += ",".join([csv_row_prefix, changed_feature, status]) + "\n"

    number_of_images_in_old_version = get_number_of_images(old_file_json)
    number_of_images_in_new_version = get_number_of_images(new_file_json)

    return feature_diff_csv_local, image_diff_csv_local, version_diff_csv_local, ','.join(
        [csv_row_prefix, str(number_of_images_in_old_version), str(number_of_images_in_new_version)]) + "\n"


def get_lines_of_code_from_content(file_content):
    loc = 0
    for line in file_content.split('\n'):
        line = line.strip()
        if len(line.strip()) != 0 and "#" not in line[:1]:
            loc += 1
    return loc


def get_lines_of_code(file_path):
    with open(file_path, 'r', encoding='utf-8') as compose_file:
        loc = get_lines_of_code_from_content(compose_file.read())
    return loc


# def load_selected_projects():
#     df = pd.read_csv("D:/Projects/wip-19-ibrahim-docker_compose-code/Data/selected_projects_filtered_by_commit_count.csv")
#     selected_owner_project = df['x'].tolist()
#     return set(map(str.strip, selected_owner_project))


# Main method starts here
compose_file_general_history_csv = ""
commit_changes_csv = ""
image_changes_csv = ""
version_changes_csv = ""
number_of_images_change_csv = ""

index = 0
start_index = 0

#
# selected_projects = load_selected_projects()

for repository_base_path in repository_base_paths:

    if index == start_index:
        compose_file_general_history_csv += "owner_id, project_name, size_of_project, compose_file_path, compose_file_size, compose_file_loc, current_loc, commit_hash, lines_inserted, lines_deleted, commiter, commit_date, commit_subject, changed_files, total_file_changed, is_first_commit\n"
        commit_changes_csv += "owner_id, project_name, commit_hash, changed_feature, status\n"
        image_changes_csv += "owner_id, project_name, commit_hash, old_val, new_val\n"
        version_changes_csv += "owner_id, project_name, commit_hash, old_val, new_val\n"
        number_of_images_change_csv += "owner_id, project_name, commit_hash, old_count, new_count\n"

    # collect all the owner folders
    for owner in os.listdir(repository_base_path):

        owner_repos_base_path = os.path.join(repository_base_path, owner)
        project_directories = os.listdir(owner_repos_base_path)
        if len(project_directories) == 0:
            os.system('rmdir /S /Q "{}"'.format(owner_repos_base_path))

        # collect all the projects for a user
        for repo_name in project_directories:

            index += 1
            if start_index > index:
                continue

            print("current index: " + str(index))

            # if '/'.join([owner, repo_name]) not in selected_projects:
            #     os.system('rmdir /S /Q "{}"'.format('\\'.join([owner_repos_base_path, repo_name])))
            #     continue

            repo_absolute_path = os.path.join(owner_repos_base_path, repo_name)
            compose_file_paths_and_size_list, repo_size = get_path_and_size(repo_absolute_path)

            if len(compose_file_paths_and_size_list) > 1:
                continue

            for compose_file_path_and_size in compose_file_paths_and_size_list:

                compose_file_relative_path = compose_file_path_and_size["path"][len(repo_absolute_path) + 1:]
                compose_file_size = compose_file_path_and_size['size']
                compose_file_loc = get_lines_of_code(compose_file_path_and_size["path"])

                # remove files that are empty
                if compose_file_size == 0 or compose_file_loc == 0:
                    continue

                os.chdir(repo_absolute_path)

                log_message = subprocess.Popen(
                    "git log --no-merges --stat --date=format:\"%Y-%m-%d %H:%M:%S\" --pretty=format:\"%H|%cE|%cd|%s\" -- " + compose_file_relative_path,
                    shell=True, stdout=subprocess.PIPE).stdout.read().decode()

                commits = get_commits(log_message)

                #to sort commits in ascending order of their dates
                commits.reverse()

                is_first_commit = True
                for commit in commits:
                    compose_file_general_history_csv += ",".join(
                        [str(owner), repo_name, str(repo_size), '"{}"'.format(compose_file_relative_path),
                         str(compose_file_size), str(compose_file_loc), str(get_lines_of_code_from_content(get_file_by_commit_hash(commit.get("commit_hash", ""), compose_file_relative_path))),
                         commit.get("commit_hash", ""), str(commit.get("lines_inserted", "")),
                         str(commit.get("lines_deleted", "")),
                         '"{}"'.format(commit.get("commiter_email", "")), commit.get("commit_date", ""),
                         '"{}"'.format(commit.get("commit_subject", "").replace("\"", "'")),
                         str(commit.get("changed_files", "")),
                         str(commit.get("number_of_files_changed", "")), str(int(is_first_commit))]) + "\n"

                    if is_first_commit:
                        is_first_commit = False

                # study the files that have more than one commit, the first commit is the initial commit on which everything is added, but none is changed
                if len(commits) > 1:
                    for i in range(len(commits) - 1):
                        commit_diff_csv, image_diff_csv, version_diff_csv, image_count_diff_csv = get_diff(commits[i],
                                                                                                           commits[i + 1],
                                                                                                           compose_file_relative_path,
                                                                                                           ",".join([str(owner), repo_name, commits[i + 1].get("commit_hash", "")]))
                        commit_changes_csv += commit_diff_csv
                        image_changes_csv += image_diff_csv
                        version_changes_csv += version_diff_csv
                        number_of_images_change_csv += image_count_diff_csv

        # writing sub part of the csv and emptying the variables to avoid memory-overflow
        if index % 100 == 0:
            write_all_csv_to_files(compose_file_general_history_csv, commit_changes_csv, image_changes_csv,
                                   version_changes_csv, number_of_images_change_csv)
            compose_file_general_history_csv = ""
            commit_changes_csv = ""
            image_changes_csv = ""
            version_changes_csv = ""
            number_of_images_change_csv = ""

# writing the remaining rows of the csv
write_all_csv_to_files(compose_file_general_history_csv, commit_changes_csv, image_changes_csv, version_changes_csv,
                       number_of_images_change_csv)


