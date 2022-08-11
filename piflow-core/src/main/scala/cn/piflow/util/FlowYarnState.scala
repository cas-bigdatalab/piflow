package cn.piflow.util

object FlowYarnState {

  val NEW = "NEW"
  val NEW_SAVING = "NEW_SAVING"
  val SUBMITTED = "SUBMITTED"
  val ACCEPTED = "ACCEPTED"
  val RUNNING = "RUNNING"
  val FINISHED = "FINISHED"
  val FAILED = "FAILED"
  val KILLED = "KILLED"
}