package cn.piflow.conf.bean

import cn.piflow.{Condition, ProjectImpl}
import cn.piflow.conf.util.MapUtil

/**
  * Created by xjzhu@cnic.cn on 4/25/19
  */
class ProjectBean {

  var uuid : String = _
  var name : String = _
  var projectEntries : List[ProjectEntryBean] = List()
  var conditions = scala.collection.mutable.Map[String, ConditionBean]()

  def init(map : Map[String, Any]) = {

    val projectMap = MapUtil.get(map, "project").asInstanceOf[Map[String, Any]]

    this.uuid = MapUtil.get(projectMap,"uuid").asInstanceOf[String]
    this.name = MapUtil.get(projectMap,"name").asInstanceOf[String]

    //construct FlowGroupBean List
    val groupList = MapUtil.get(projectMap,"groups").asInstanceOf[List[Map[String, Any]]]
    groupList.foreach( flowGroupMap => {
      val flowGroup = FlowGroupBean(flowGroupMap.asInstanceOf[Map[String, Any]])
      this.projectEntries =   flowGroup +: this.projectEntries
    })

    //construct FlowBean List
    val flowList = MapUtil.get(projectMap,"flows").asInstanceOf[List[Map[String, Any]]]
    flowList.foreach( flowMap => {
      val flow = FlowBean(flowMap.asInstanceOf[Map[String, Any]])
      this.projectEntries =   flow +: this.projectEntries
    })

    //construct ConditionBean List
    val conditionList = MapUtil.get(projectMap,"conditions").asInstanceOf[List[Map[String, Any]]]
    conditionList.foreach( conditionMap => {
      val conditionBean = ConditionBean(conditionMap.asInstanceOf[Map[String, Any]])
      conditions(conditionBean.entry) =  conditionBean
    })

  }

  def constructProject() = {
    val project = new ProjectImpl();
    project.setProjectName(name)

    this.projectEntries.foreach( projectEntryBean => {
      if( !conditions.contains(projectEntryBean.name) ){
        if (projectEntryBean.isInstanceOf[FlowBean]){
          val bean = projectEntryBean.asInstanceOf[FlowBean]
          project.addProjectEntry(projectEntryBean.name,bean.constructFlow())
        }else{
          val groupBean = projectEntryBean.asInstanceOf[FlowGroupBean]
          project.addProjectEntry(groupBean.name,groupBean.constructFlowGroup())
        }

      }
      else{
        val conditionBean = conditions(projectEntryBean.name)

        if(conditionBean.after.size == 0){

          println(projectEntryBean.name + " do not have after flow "  + "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

          if (projectEntryBean.isInstanceOf[FlowBean]){
            val bean = projectEntryBean.asInstanceOf[FlowBean]
            project.addProjectEntry(projectEntryBean.name,bean.constructFlow())
          }else{
            val groupBean = projectEntryBean.asInstanceOf[FlowGroupBean]
            project.addProjectEntry(groupBean.name,groupBean.constructFlowGroup())
          }

        }
        else if(conditionBean.after.size == 1){

          println(projectEntryBean.name + " after " + conditionBean.after(0) + "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

          if (projectEntryBean.isInstanceOf[FlowBean]){
            val bean = projectEntryBean.asInstanceOf[FlowBean]
            project.addProjectEntry(projectEntryBean.name,bean.constructFlow(),Condition.after(conditionBean.after(0)))
          }else{
            val groupBean = projectEntryBean.asInstanceOf[FlowGroupBean]
            project.addProjectEntry(groupBean.name,groupBean.constructFlowGroup(), Condition.after(conditionBean.after(0)))
          }

        }
        else {
          println(projectEntryBean.name + " after " + conditionBean.after.toSeq + "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

          var other = new Array[String](conditionBean.after.size-1)
          conditionBean.after.copyToArray(other,1)

          if (projectEntryBean.isInstanceOf[FlowBean]){
            val bean = projectEntryBean.asInstanceOf[FlowBean]
            project.addProjectEntry(projectEntryBean.name,bean.constructFlow(),Condition.after(conditionBean.after(0),other: _*))
          }else{
            val groupBean = projectEntryBean.asInstanceOf[FlowGroupBean]
            project.addProjectEntry(groupBean.name,groupBean.constructFlowGroup(), Condition.after(conditionBean.after(0),other: _*))
          }

        }
      }

    })

    project
  }

  /*private def addProjectEntry(project:ProjectImpl, projectEntryBean:ProjectEntryBean, conditionBean: ConditionBean): Unit ={
    if (projectEntryBean.isInstanceOf[FlowBean]){
      val bean = projectEntryBean.asInstanceOf[FlowBean]
      project.addProjectEntry(projectEntryBean.name,bean.constructFlow(),Condition.after(conditionBean.after(0),other: _*))
    }else{
      val groupBean = projectEntryBean.asInstanceOf[FlowGroupBean]
      project.addProjectEntry(groupBean.name,groupBean.constructFlowGroup(), Condition.after(conditionBean.after(0),other: _*))
    }
  }*/

}

object ProjectBean {
  def apply(map : Map[String, Any]): ProjectBean = {

    val projectBean = new ProjectBean()
    projectBean.init(map)
    projectBean
  }
}
