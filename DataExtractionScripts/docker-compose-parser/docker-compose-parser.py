import os
import yaml
import pandas as pd

def get_compose_file_paths(start_path):
    paths = []
    for dir_path, dir_names, file_names in os.walk(start_path):
        for file_name in file_names:
            fp = os.path.join(dir_path, file_name)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                if file_name == "docker-compose.yml":
                    paths.append(fp)
    return paths


def get_image_row(json, image_csv_row_prefix):
    image_info = {}

    for key in json:
        if key == "image":
            image_info['image'] = json[key]

        if key == "build":
            image_info['build'] = 1

    image = image_info.get('image', '')
    build = image_info.get('build', '')

    if (not isinstance(image, dict)) and (image or build):
        # This is to check a case such as: [ubuntu]
        if isinstance(image, list) and len(image) > 0:
            image = image[0]
        elif isinstance(image, list) and len(image) == 0:
            image = ""

        image_name = image
        image_tag = ""
        image_name_split = image_name.split(":")
        if len(image_name_split) > 1 and "/" not in image_name_split[len(image_name_split) - 1]:
            image_name = ":".join(image_name_split[:-1])
            image_tag = image_name_split[len(image_name_split) - 1]

        return f"{image_csv_row_prefix},{image.strip()}, {image_name.strip()},{image_tag.strip()}, {build}\n"

    return ""


def is_valid_feature(feature):
    for key in feature_list:
        if feature in feature_list[key]:
            return True
    return False


def get_compose_file_images_and_features_csv(compose_file_path_param, compose_file_relative_path_param, owner_id, project_name):
    image_names_csv = ""
    compose_features_csv = ""

    csv_row_prefix = f"{owner_id}, {project_name}, \"{compose_file_relative_path_param}\""

    json = {}
    with open(compose_file_path_param, 'rb') as stream:
        try:
            json = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    if json is None:
        json = {}

    compose_version = ""

    # to extract the version of the compose file since the order of the key is not maintained
    if isinstance(json, dict):
        for key in json:
            json_element = json[key]
            if key == "version" and isinstance(json_element, dict) is False:
                compose_version = json_element
                break

    csv_row_prefix += f",\"{compose_version}\""

    # extracting features and images starts here
    # root elements
    if isinstance(json, dict):
        image_names_csv += get_image_row(json, csv_row_prefix)
        for key in json:
            json_element = json[key]
            if key != "version":
                if is_valid_feature(key):
                    compose_features_csv += f"{csv_row_prefix}, {key}, 1, \n"

            if isinstance(json_element, dict):
                image_names_csv += get_image_row(json_element, csv_row_prefix)
                # services
                for key2 in json_element:
                    json_element_2 = json_element[key2]

                    if is_valid_feature(key2):
                        compose_features_csv += f"{csv_row_prefix}, {key2}, 2, {key}\n"

                    # we get the images at this level
                    if isinstance(json_element_2, dict):
                        image_names_csv += get_image_row(json_element_2, csv_row_prefix)

                        for key3 in json_element_2:

                            json_element_3 = json_element_2[key3]

                            if is_valid_feature(key3):
                                compose_features_csv += f"{csv_row_prefix}, {key3}, 3, {key2}\n"

                            if isinstance(json_element_3, dict):
                                image_names_csv += get_image_row(json_element_3, csv_row_prefix)

                                for key4 in json_element_3:
                                    json_element_4 = json_element_3[key4]

                                    if is_valid_feature(key4):
                                        compose_features_csv += f"{csv_row_prefix}, {key4}, 4, {key3}\n"

                                    if isinstance(json_element_4, dict):
                                        image_names_csv += get_image_row(json_element_4, csv_row_prefix)

                                        for key5 in json_element_4:
                                            if is_valid_feature(key5):
                                                compose_features_csv += f"{csv_row_prefix}, {key5}, 5, {key4}\n"

    return image_names_csv, compose_features_csv


# def load_selected_projects():
#     df = pd.read_csv(
#         "D:/Projects/wip-19-ibrahim-docker_compose-code/Data/selected_projects_filtered_by_commit_count.csv")
#     selected_owner_project = df['x'].tolist()
#     return set(map(str.strip, selected_owner_project))


def load_features():
    features_base_path = "D:/Projects/wip-19-ibrahim-docker_compose-code/Data/version-features"
    versions = [1, 2, 3]
    version_features = {}

    for version in versions:
        with open(features_base_path+"/version"+str(version)+".txt") as feature_file:
            features = feature_file.read()
            version_features[version] = set(map(str.strip, features.split(",")))

    return version_features


# The main function starts here

#chnage the path accoring to the directory that contains cloned repositories
repository_base_paths = ["D:/Projects/Docker-Compose-Repositories"]
compose_images_output_file_path = "D:/Projects/wip-19-ibrahim-docker_compose-code/Data/compose_images.csv"
compose_features_output_file_path = "D:/Projects/wip-19-ibrahim-docker_compose-code/Data/compose_features.csv"

# selected_projects = load_selected_projects()
feature_list = load_features()

index = 0
start_index = 0
number_of_projects_having_more_than_one_compose_file = 0

if start_index == index:
    compose_images_csv_header = "owner_id, project_name, compose_file_path, version, image_with_tag, image, tag, custom_build\n"
    compose_features_csv_header = "owner_id, project_name, compose_file_path, version, feature, level, parent\n"

    with open(compose_images_output_file_path, 'a', encoding='utf-8') as f:
        f.write(compose_images_csv_header)

    with open(compose_features_output_file_path, 'a', encoding='utf-8') as f:
        f.write(compose_features_csv_header)

for repository_base_path in repository_base_paths:
    for owner in os.listdir(repository_base_path):
        index += 1
        if start_index > index:
            continue

        print("current index: " + str(index))

        owner_repos_base_path = os.path.join(repository_base_path, owner)

        # collect all the projects for a user
        for repo_name in os.listdir(owner_repos_base_path):

            # if '/'.join([owner, repo_name]) not in selected_projects:
            #     continue

            repo_absolute_path = os.path.join(owner_repos_base_path, repo_name)
            compose_file_paths = get_compose_file_paths(repo_absolute_path)

            if len(compose_file_paths) > 1:
                number_of_projects_having_more_than_one_compose_file += 1
                continue

            compose_images_csv_output = ""
            compose_features_csv_output = ""

            for compose_file_path in compose_file_paths:
                compose_file_relative_path = compose_file_path[len(repo_absolute_path) + 1:]
                images_csv, features_csv = get_compose_file_images_and_features_csv(compose_file_path,
                                                                                    compose_file_relative_path, owner,
                                                                                    repo_name)
                compose_images_csv_output += images_csv
                compose_features_csv_output += features_csv

            with open(compose_images_output_file_path, 'a', encoding='utf-8') as f:
                f.write(compose_images_csv_output)
                compose_images_csv_output = ""

            with open(compose_features_output_file_path, 'a', encoding='utf-8') as f:
                f.write(compose_features_csv_output)
                compose_features_csv_output = ""

print(f"number_of_projects_having_more_than_one_compose_file: {number_of_projects_having_more_than_one_compose_file}")
