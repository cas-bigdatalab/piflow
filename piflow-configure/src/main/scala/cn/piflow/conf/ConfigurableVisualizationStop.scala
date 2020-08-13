package cn.piflow.conf

import cn.piflow.{IncrementalStop, VisualizationStop}
import cn.piflow.util.{ConfigureUtil, HdfsUtil}
import org.apache.spark.sql.{DataFrame, SaveMode, SparkSession}

/**
  * Created by xjzhu@cnic.cn on 8/11/202
  */
abstract class ConfigurableVisualizationStop extends ConfigurableStop with VisualizationStop {


  override var visualizationPath: String = _
  override var processId : String = _
  override var stopName : String = _

  override def init(stopName : String): Unit = {
    this.stopName = stopName
  }


  override def getVisualizationPath(processId : String) : String = {
    visualizationPath = ConfigureUtil.getVisualizationPath().stripSuffix("/") + "/" + processId + "/" + stopName
    visualizationPath
  }

}
