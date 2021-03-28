if (!require("pacman")) install.packages("pacman")
pacman::p_load(here, ggplot2)


compose_projects = read.csv(here("data-collection/data", "compose_project_commit_contributor_count.csv"), header =
                              TRUE, sep = ",")

root_compose_project = compose_projects[is.na(compose_projects$forked_from) & compose_projects$deleted == 0,]


root_compose_project$owner_project = paste(root_compose_project$owner_id, root_compose_project$name, sep = "/")

project_commit_cdf = data.frame(commit_count = numeric(), number_of_project = numeric())

for(no_of_commit in seq(1, max(root_compose_project$commit_count))){
  
  project_commit_cdf = rbind(project_commit_cdf, data.frame(commit_count = no_of_commit
                                                            , number_of_project = nrow(root_compose_project[root_compose_project$commit_count >= no_of_commit,])))
}

ggplot(data=project_commit_cdf, aes(x=commit_count, y = number_of_project, group=1)) +
  geom_line()+
  ylab("# of projects")+
  xlab("# of commits")+
  theme_bw()+
  scale_x_log10()

#write.csv(root_compose_project[root_compose_project$commit_count >= 100,c('owner_project')], file = here("~//data/", "filtered_by_commit_count_compose_projects.csv"), row.names=FALSE)

write.csv(root_compose_project[root_compose_project$commit_count >= 100,], file = here("rqs/data/","root_compose_projects_commit_count_100.csv"), row.names=FALSE)
