package cn.piflow.conf

object PortEnum extends Enumeration {

  type Port = Value
  val AnyPort = Value("Any")
  val DefaultPort = Value("Default")
  val NonePort = Value("None")
}
