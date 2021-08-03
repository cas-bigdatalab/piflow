package cn.piflow.conf.bean


class DataCenterFlowBean{

  //flow json string
  var flowJson: String = _
  var flowBean : FlowBean = _


  def initFlowBean(map : Map[String, Any]) = {
    this.flowBean = FlowBean(map)
  }

  //create Flow by FlowBean
  def constructDataCenterGroupBean() : DataCenterGroupBean= {

    DataCenterTaskPlan(this.flowBean).plan()
  }

}

object DataCenterFlowBean{
  def apply(map : Map[String, Any]): DataCenterFlowBean = {
    val dcFlowBean = new DataCenterFlowBean()
    dcFlowBean.initFlowBean(map)
    dcFlowBean
  }
}


