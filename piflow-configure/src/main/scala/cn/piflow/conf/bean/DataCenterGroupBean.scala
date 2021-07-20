package cn.piflow.conf.bean

import cn.piflow.{Condition, DataCenterGroupImpl, Path}
import cn.piflow.conf.util.MapUtil

class DataCenterGroupBean extends GroupEntryBean{

  var uuid : String = _
  var name : String = _
  var groupEntries : List[GroupEntryBean] = List()
  var paths : List[DataCenterConditionBean] = List()
  var conditions = scala.collection.mutable.Map[String, DataCenterConditionBean]()

  def init(map : Map[String, Any]) = {

    val groupMap = MapUtil.get(map, "group").asInstanceOf[Map[String, Any]]

    this.uuid = MapUtil.get(groupMap,"uuid").asInstanceOf[String]
    this.name = MapUtil.get(groupMap,"name").asInstanceOf[String]


    //construct FlowBean List
    if(MapUtil.get(groupMap,"flows") != None){
      val flowList = MapUtil.get(groupMap,"flows").asInstanceOf[List[Map[String, Any]]]
      flowList.foreach( flowMap => {
        val flow = FlowBean(flowMap.asInstanceOf[Map[String, Any]])
        this.groupEntries =   flow +: this.groupEntries
      })
    }

    //construct groupEntry path
    val pathsList = MapUtil.get(groupMap,"conditions").asInstanceOf[List[Map[String, Any]]]
    pathsList.foreach( pathMap => {
      val path = DataCenterConditionBean(pathMap.asInstanceOf[Map[String, Any]])
      this.paths = path +: this.paths
    })

    //construct ConditionBean List
    if(MapUtil.get(groupMap,"conditions") != None){
      val conditionList = MapUtil.get(groupMap,"conditions").asInstanceOf[List[Map[String, Any]]]
      conditionList.foreach( conditionMap => {
        val conditionBean = DataCenterConditionBean(conditionMap.asInstanceOf[Map[String, Any]])
        if(!conditions.getOrElse(conditionBean.entry.flowName,"").equals("")){

          conditionBean.after = conditions(conditionBean.entry.flowName).after ::: conditionBean.after
        }
        conditions(conditionBean.entry.flowName) = conditionBean
      })
    }

  }

  def constructGroup() : DataCenterGroupImpl = {
    val group = new DataCenterGroupImpl();
    group.setGroupName(name)

    this.groupEntries.foreach(groupEntryBean => {
      if( !conditions.contains(groupEntryBean.name) ){
        if (groupEntryBean.isInstanceOf[FlowBean]){
          val bean = groupEntryBean.asInstanceOf[FlowBean]
          group.addGroupEntry(groupEntryBean.name,bean.constructFlow())
        }else{
          val groupBean = groupEntryBean.asInstanceOf[GroupBean]
          group.addGroupEntry(groupBean.name,groupBean.constructGroup())
        }
      }
      else{
        val conditionBean = conditions(groupEntryBean.name)

        if(conditionBean.after.size == 0){

          println(groupEntryBean.name + " do not have after flow "  + "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

          if (groupEntryBean.isInstanceOf[FlowBean]){
            val bean = groupEntryBean.asInstanceOf[FlowBean]
            group.addGroupEntry(groupEntryBean.name,bean.constructFlow())
          }else{
            val groupBean = groupEntryBean.asInstanceOf[GroupBean]
            group.addGroupEntry(groupBean.name,groupBean.constructGroup())
          }

        }
        else if(conditionBean.after.size == 1){

          println(groupEntryBean.name + " after " + conditionBean.after(0) + "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

          if (groupEntryBean.isInstanceOf[FlowBean]){
            val bean = groupEntryBean.asInstanceOf[FlowBean]
            group.addGroupEntry(groupEntryBean.name,bean.constructFlow(),Condition.after(conditionBean.after(0).flowName))
          }else{
            val groupBean = groupEntryBean.asInstanceOf[GroupBean]
            group.addGroupEntry(groupBean.name,groupBean.constructGroup(), Condition.after(conditionBean.after(0).flowName))
          }

        }
        else {
          println(groupEntryBean.name + " after " + conditionBean.after.toSeq + "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

          var other = List[String]()
          conditionBean.after.foreach{x =>
            other = x.flowName +: other
          }

          if (groupEntryBean.isInstanceOf[FlowBean]){
            val bean = groupEntryBean.asInstanceOf[FlowBean]
            group.addGroupEntry(groupEntryBean.name,bean.constructFlow(),Condition.after(conditionBean.after(0).flowName,other: _*))
          }else{
            val groupBean = groupEntryBean.asInstanceOf[GroupBean]
            group.addGroupEntry(groupBean.name,groupBean.constructGroup(), Condition.after(conditionBean.after(0).flowName,other: _*))
          }

        }
      }

    })

    this.paths.foreach( pathBean => {
      group.addPath(Path.from(pathBean.after(0).flowName).via(pathBean.outport, pathBean.inport).to(pathBean.entry.flowName))
    })

    group
  }
}

object DataCenterGroupBean {
  def apply(map : Map[String, Any]): DataCenterGroupBean = {

    val groupBean = new DataCenterGroupBean()
    groupBean.init(map)
    groupBean
  }
}
