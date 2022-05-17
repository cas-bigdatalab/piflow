create table if not exists taskplan_group (id varchar(255), groupName varchar(255), groupDataCenter varchar(255));
create table if not exists taskplan_flow (id varchar(255), groupId varchar(255), flowName varchar(255), flowDataCenter varchar(255));
create table if not exists taskplan_condition (id varchar(255), groupId varchar(255), upstreamFlowName varchar(255), flowOutport varchar(255), flowInport varchar(255), downstreamFlowName varchar(255));
create table if not exists taskplan_stop (id varchar(255), flowId varchar(255), stopName varchar(255), stopDataCenter varchar(255));
create table if not exists taskplan_path (id varchar(255), flowId varchar(255), fromStop varchar(255), outport varchar(255), inport varchar(255), toStop varchar(255));
