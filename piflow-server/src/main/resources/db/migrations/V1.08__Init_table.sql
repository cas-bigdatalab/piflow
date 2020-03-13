drop table if exists project;
alter table if exists flow drop column projectId;
alter table if exists flowGroup alter column projectId rename to parentId;
alter table if exists flowGroup alter column flowCount rename to childCount;
