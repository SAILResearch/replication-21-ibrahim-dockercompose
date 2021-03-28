if (!require("pacman")) install.packages("pacman")
pacman::p_load(here, reshape, sqldf, splitstackshape, stringr, dplyr, DescTools)

version_changes = read.csv(file = here("rqs/data","version_changes_by_commit.csv"), header =
                             TRUE, sep = ",")
version_changes$owner_project = paste(version_changes$owner_id, version_changes$project_name, sep = "/")


compose_file_features = read.csv(file = here("rqs/data","compose_features.csv"), header =
                                   TRUE, sep = ",")

#hack
compose_file_features[compose_file_features$version == 'n', c("version")] = ""

compose_file_features$version = as.character(compose_file_features$version)
compose_file_features[compose_file_features$version == "", c("version")] = "1"
compose_file_features$owner_project = paste(compose_file_features$owner_id, compose_file_features$project_name, sep = "")
compose_file_features$version_num = as.numeric(compose_file_features$version)
project_counts_per_version = sqldf("select version_num, count(distinct owner_project) as count from compose_file_features group by version_num")
project_counts_per_version = project_counts_per_version[order(project_counts_per_version$count, decreasing = TRUE),]
project_counts_per_version$percentage = round(project_counts_per_version$count/sum(project_counts_per_version$count)*100, 2)

project_counts_per_version = project_counts_per_version[project_counts_per_version$percentage > 0.1,]

project_counts_per_version$version = as.numeric(project_counts_per_version$version)
project_counts_per_version$version = sprintf("version %.1f", project_counts_per_version$version)
project_counts_per_version$version = as.character(project_counts_per_version$version)
project_counts_per_version = project_counts_per_version[order(project_counts_per_version$version, decreasing = TRUE),]
project_counts_per_version$version = factor(project_counts_per_version$version, level = project_counts_per_version$version)


ggplot(project_counts_per_version
       , aes(version, percentage, label = sprintf("%.1f%%", percentage)))+
  geom_linerange(aes(x=version, ymin = 0, ymax = percentage))+
  geom_point(aes(x = reorder(version, version), y = percentage))+
  geom_text(size=3.2, hjust=-0.25, color="black", inherit.aes = TRUE)+
  coord_flip()+
  xlab("")+
  ylab("% of projects")+
  theme_test()+
  theme(axis.text=element_text(size=10),
        axis.title=element_text(size=10),
        axis.line=element_blank(),
        axis.text.x=element_blank(),
        axis.ticks.x=element_blank(),
        legend.position = "none")+
  ylim(c(0,45))


compose_project_evolution = read.csv(file = here("rqs/data","compose_project_evolution.csv"), header =
                                       TRUE, sep = ",")
compose_project_evolution$owner_project = paste(compose_project_evolution$owner_id, compose_project_evolution$project_name, sep = "/")
compose_project_evolution$total_line_change = compose_project_evolution$lines_deleted + compose_project_evolution$lines_inserted
compose_project_evolution = unique(compose_project_evolution)

#remove unchanged commits 
compose_project_evolution = compose_project_evolution[compose_project_evolution$total_line_change > 0,]

version_changes = unique(sqldf("select version_changes.*, compose_project_evolution.commit_subject, 
      compose_project_evolution.lines_inserted, compose_project_evolution.lines_deleted
      from version_changes left outer join compose_project_evolution
      on version_changes.commit_hash = compose_project_evolution.commit_hash"))

version_changes$total_line_change = version_changes$lines_deleted + version_changes$lines_inserted
version_changes = version_changes[!is.na(version_changes$lines_deleted),] # removing merge commits


print("% of commits that change the version of Docker Compose:")
print(nrow(version_changes)/(nrow(compose_project_evolution) - length(unique(compose_project_evolution$owner_project)))*100) #minus the initial commit


print("% of projects that changes the version of Docker compose:")
print((length(unique(version_changes$owner_project))/length(unique(compose_project_evolution$owner_project))*100))


print("Summary of chnaged lines of code in a version change:")
summary(version_changes$total_line_change)


version_changes$old_val_numeric = as.numeric(as.character(version_changes$old_val))
version_changes$new_val_numeric = as.numeric(as.character(version_changes$new_val))

version_changes = na.omit(version_changes)
version_changes$old_val = as.character(version_changes$old_val)
version_changes$new_val = as.character(version_changes$new_val)

version_changes$type = ""
version_changes[version_changes$old_val_numeric < version_changes$new_val_numeric,c('type')] = "upgrade"
version_changes[version_changes$old_val_numeric > version_changes$new_val_numeric,c('type')] = "downgrade"
version_changes[version_changes$type == "" & nchar(version_changes$old_val) > nchar(version_changes$new_val), c('type')] = "Minor version removed"
version_changes[version_changes$type == "" & nchar(version_changes$new_val) > nchar(version_changes$old_val), c('type')] = "Minor version added"
version_changes$owner_project = paste(version_changes$owner_id, version_changes$project_name, sep = "/")

version_changes$change_type = ""
version_changes[abs(floor(version_changes$old_val_numeric) - floor(version_changes$new_val_numeric)) >= 1, "change_type"] = "major"
version_changes[abs(floor(version_changes$old_val_numeric) - floor(version_changes$new_val_numeric)) < 1, "change_type"] = "minor"

print("% of version major version changes")
print(nrow(version_changes[version_changes$change_type == 'major',])/nrow(version_changes)*100)
version_changes$major_version_old = floor(version_changes$old_val_numeric)
version_changes$major_version_new = floor(version_changes$new_val_numeric)


print("% of version minor version changes")
print(nrow(version_changes[version_changes$change_type == 'minor',])/nrow(version_changes)*100)

version_upgrade_downgrade_pattern = sqldf("select owner_project, group_concat(type) as pattern from version_changes group by owner_project")

print("% of version upgraded:")
print((nrow(version_changes[version_changes$old_val_numeric < version_changes$new_val_numeric,])/nrow(version_changes)*100))


print("% of version downgraded:")
print((nrow(version_changes[version_changes$old_val_numeric > version_changes$new_val_numeric,])/nrow(version_changes)*100))

version_downgrade_instances = unique(version_changes[version_changes$old_val_numeric > version_changes$new_val_numeric,c('commit_hash', 'old_val', 'new_val')])
version_downgrade_instances$change_type = ""
version_downgrade_instances$old_val = as.numeric(as.character(version_downgrade_instances$old_val))
version_downgrade_instances$new_val = as.numeric(as.character(version_downgrade_instances$new_val))

version_downgrade_instances[floor(version_downgrade_instances$old_val) - floor(version_downgrade_instances$new_val) >= 1, "change_type"] = "major"
version_downgrade_instances[floor(version_downgrade_instances$old_val) - floor(version_downgrade_instances$new_val) < 1, "change_type"] = "minor"


print("% of version unchanged:")
print((nrow(version_changes[version_changes$old_val_numeric == version_changes$new_val_numeric,])/nrow(version_changes)*100))

number_of_projects = length(unique(compose_project_evolution$owner_project))

print("% of projects that upgrade versions of Docker Compose")
print(length(unique(version_changes[version_changes$type=='upgrade',c('owner_project')]))/number_of_projects*100)

print("% of projects that downgrade versions of Docker Compose")
print(length(unique(version_changes[version_changes$type=='downgrade',c('owner_project')]))/number_of_projects*100)


######## version features analysis


compose_file_features = read.csv(file = here("rqs/data","compose_features.csv"), header =
                                   TRUE, sep = ",")

compose_file_features$owner_project = paste(compose_file_features$owner_id, compose_file_features$project_name, sep="/")
compose_file_features$feature = trimws(compose_file_features$feature)


compse_file_version1_features = read.csv(here("rqs/data/version_options","version1.csv"), header = FALSE, sep = ",")

compse_file_version1_features = as.data.frame(t(compse_file_version1_features))
colnames(compse_file_version1_features) = c('feature')
compse_file_version1_features$feature = trimws(compse_file_version1_features$feature)

compse_file_version2_features = read.csv(here("rqs/data/version_options","version2.csv"), header = FALSE, sep = ",")
compse_file_version2_features = as.data.frame(t(compse_file_version2_features))
colnames(compse_file_version2_features) = c('feature')
compse_file_version2_features$feature = trimws(compse_file_version2_features$feature)

compse_file_version3_features = read.csv(here("rqs/data/version_options","version3.csv"), header = FALSE, sep = ",")
compse_file_version3_features = as.data.frame(t(compse_file_version3_features))
colnames(compse_file_version3_features) = c('feature')
compse_file_version3_features$feature = trimws(compse_file_version3_features$feature)

unique_features_in_all_versions = unique(rbind(compse_file_version1_features, compse_file_version2_features, compse_file_version3_features))


feature_removed_in_version3 = as.data.frame(setdiff(compse_file_version2_features$feature, compse_file_version3_features$feature))
colnames(feature_removed_in_version3) = c('missing_features')


feature_added_in_version3 = as.data.frame(setdiff(compse_file_version3_features$feature, compse_file_version2_features$feature))
colnames(feature_added_in_version3) = c('missing_features')

options_that_are_not_used = as.data.frame(setdiff(unique_features_in_all_versions$feature, unique(compose_file_features$feature)))
colnames(options_that_are_not_used) = c("unused_options")

removed_unused_features = as.data.frame(intersect(options_that_are_not_used$unused_options, feature_removed_in_version3$missing_features))
colnames(removed_unused_features) = c('unused_features_removed')
print("# of removed options in version 3 that were unused:")
print(nrow(removed_unused_features))

compose_project_using_removed_features = compose_file_features[compose_file_features$feature %in% feature_removed_in_version3$missing_feature,]

removed_feature_used_by_projects_count = sqldf("select feature, count(distinct owner_project) as project_count from compose_project_using_removed_features group by feature")

print("Summary of removed features used by the number of projects:")
summary(removed_feature_used_by_projects_count$project_count)



