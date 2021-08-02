package cn.piflow.conf.bean


class DataCenterFlowBean{

  //flow json string
  var flowJson: String = _
  var flowBean : FlowBean = _
  var dataCenterGroupBean : DataCenterGroupBean = _

  def initFlowBean(map : Map[String, Any]):FlowBean = {
    this.flowBean = FlowBean(map)
    this.flowBean
  }
  //create Flow by FlowBean
  def constructTaskPlan() : FlowBean= {

    DataCenterTaskPlan().visit(this.flowBean)
    flowBean
  }
}

object DataCenterFlowBean{
  def apply(map : Map[String, Any]): DataCenterFlowBean = {
    val dcFlowBean = new DataCenterFlowBean()
    dcFlowBean.initFlowBean(map)
    dcFlowBean
  }
}


