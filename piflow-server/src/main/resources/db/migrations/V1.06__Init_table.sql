create table if not exists PROJECT (id varchar(255), name varchar(255), state varchar(255), startTime varchar(255), endTime varchar(255));
create table if not exists FLOWGROUP (id varchar(255), projectId varchar(255), name varchar(255), state varchar(255), startTime varchar(255), endTime varchar(255));

alter table FLOW add column GROUPID int;
alter table FLOW add column PROJECTID int;
alter table FLOWGROUP add column FLOWCOUNT int;