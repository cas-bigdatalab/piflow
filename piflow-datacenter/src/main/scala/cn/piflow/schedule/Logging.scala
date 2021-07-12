package cn.piflow.schedule

import org.apache.log4j.Logger

trait Logging {
  protected lazy val logger = Logger.getLogger(this.getClass);
}
