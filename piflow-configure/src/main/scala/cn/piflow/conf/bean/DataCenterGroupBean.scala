package cn.piflow.conf.bean

import cn.piflow.{Condition, DataCenterGroupImpl, GroupImpl}
import cn.piflow.conf.util.MapUtil

class DataCenterGroupBean extends GroupEntryBean{

  var uuid : String = _
  var name : String = _
  var groupEntries : List[GroupEntryBean] = List()
  var conditions = scala.collection.mutable.Map[String, ConditionBean]()

  def init(map : Map[String, Any]) = {

    val groupMap = MapUtil.get(map, "group").asInstanceOf[Map[String, Any]]

    this.uuid = MapUtil.get(groupMap,"uuid").asInstanceOf[String]
    this.name = MapUtil.get(groupMap,"name").asInstanceOf[String]

    //construct GroupBean List
    /*if(MapUtil.get(groupMap,"groups") != None){
      val groupList = MapUtil.get(groupMap,"groups").asInstanceOf[List[Map[String, Any]]]
      groupList.foreach( groupMap => {
        val group = GroupBean(groupMap.asInstanceOf[Map[String, Any]])
        this.groupEntries =   group +: this.groupEntries
      })
    }*/


    //construct FlowBean List
    if(MapUtil.get(groupMap,"flows") != None){
      val flowList = MapUtil.get(groupMap,"flows").asInstanceOf[List[Map[String, Any]]]
      flowList.foreach( flowMap => {
        val flow = FlowBean(flowMap.asInstanceOf[Map[String, Any]])
        this.groupEntries =   flow +: this.groupEntries
      })
    }

    //construct ConditionBean List
    if(MapUtil.get(groupMap,"conditions") != None){
      val conditionList = MapUtil.get(groupMap,"conditions").asInstanceOf[List[Map[String, Any]]]
      conditionList.foreach( conditionMap => {
        val conditionBean = ConditionBean(conditionMap.asInstanceOf[Map[String, Any]])
        if(!conditions.getOrElse(conditionBean.entry,"").equals("")){

          conditionBean.after = conditions(conditionBean.entry).after ::: conditionBean.after
        }
        conditions(conditionBean.entry) = conditionBean
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
            group.addGroupEntry(groupEntryBean.name,bean.constructFlow(),Condition.after(conditionBean.after(0)))
          }else{
            val groupBean = groupEntryBean.asInstanceOf[GroupBean]
            group.addGroupEntry(groupBean.name,groupBean.constructGroup(), Condition.after(conditionBean.after(0)))
          }

        }
        else {
          println(groupEntryBean.name + " after " + conditionBean.after.toSeq + "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

          var other = new Array[String](conditionBean.after.size-1)
          conditionBean.after.copyToArray(other,1)

          if (groupEntryBean.isInstanceOf[FlowBean]){
            val bean = groupEntryBean.asInstanceOf[FlowBean]
            group.addGroupEntry(groupEntryBean.name,bean.constructFlow(),Condition.after(conditionBean.after(0),other: _*))
          }else{
            val groupBean = groupEntryBean.asInstanceOf[GroupBean]
            group.addGroupEntry(groupBean.name,groupBean.constructGroup(), Condition.after(conditionBean.after(0),other: _*))
          }

        }
      }

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
