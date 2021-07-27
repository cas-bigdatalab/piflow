package cn.piflow.conf.bean


class DataCenterFlowBean{

  //flow json string
  var flowJson: String = _
  var flowBean : FlowBean = _
  var dataCenterGroupBean : DataCenterGroupBean = _

  def initFlowBean(map : Map[String, Any]):FlowBean = {
    FlowBean(map)
  }

  //create Flow by FlowBean
  def constructDataCenterGroupBean(flowBean:FlowBean) : DataCenterGroupBean= {

    null

  }

}


