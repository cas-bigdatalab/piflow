package cn.piflow.conf.bean

import cn.piflow._
import cn.piflow.conf.util.MapUtil

/**
  * Created by xjzhu@cnic.cn on 4/25/19
  */
class FlowGroupBean extends ProjectEntryBean {

  var uuid : String = _
  var name : String = _
  var flows : List[FlowBean] = List()
  var conditions = scala.collection.mutable.Map[String, ConditionBean]()

  def init(map : Map[String, Any]) = {

    val groupMap = MapUtil.get(map, "group").asInstanceOf[Map[String, Any]]

    this.uuid = MapUtil.get(groupMap,"uuid").asInstanceOf[String]
    this.name = MapUtil.get(groupMap,"name").asInstanceOf[String]

    //construct FlowBean List
    val flowList = MapUtil.get(groupMap,"flows").asInstanceOf[List[Map[String, Any]]]
    flowList.foreach( flowMap => {
      val flow = FlowBean(flowMap.asInstanceOf[Map[String, Any]])
      this.flows =   flow +: this.flows
    })

    //construct ConditionBean List
    val conditionList = MapUtil.get(groupMap,"conditions").asInstanceOf[List[Map[String, Any]]]
    conditionList.foreach( conditionMap => {
      val conditionBean = ConditionBean(conditionMap.asInstanceOf[Map[String, Any]])
      conditions(conditionBean.entry) =  conditionBean
    })

  }

  //create Flow group by GroupBean
  def constructFlowGroup()= {
    val flowGroup = new FlowGroupImpl();
    flowGroup.setFlowGroupName(this.name)

    this.flows.foreach( flowBean => {
      if( !conditions.contains(flowBean.name) ){
        flowGroup.addFlow(flowBean.name,flowBean.constructFlow())
      }
      else{
        val conditionBean = conditions(flowBean.name)

        if(conditionBean.after.size == 0){
          println(flowBean.name + " do not have after flow "  + "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
          flowGroup.addFlow(flowBean.name,flowBean.constructFlow())
        }
        else if(conditionBean.after.size == 1){
          println(flowBean.name + " after " + conditionBean.after(0) + "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
          flowGroup.addFlow(flowBean.name,flowBean.constructFlow(), Condition.after(conditionBean.after(0)))
        }
        else {
          println(flowBean.name + " after " + conditionBean.after.toSeq + "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
          var other = new Array[String](conditionBean.after.size-1)
          conditionBean.after.copyToArray(other,1)
          flowGroup.addFlow(flowBean.name,flowBean.constructFlow(), Condition.after(conditionBean.after(0),other: _*))
        }
      }

    })

    flowGroup
  }
}

object FlowGroupBean{
  def apply(map : Map[String, Any]): FlowGroupBean = {
    val flowGroupBean = new FlowGroupBean()
    flowGroupBean.init(map)
    flowGroupBean
  }

}
