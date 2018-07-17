package cn.piflow.conf

sealed class StopGroup
case object CommonGroup extends StopGroup
case object CsvGroup extends StopGroup
case object HiveGroup extends StopGroup
case object JdbcGroup extends StopGroup
case object JsonGroup extends StopGroup
case object XmlGroup extends StopGroup
case object HttpGroup extends StopGroup
case object FtpGroup extends StopGroup
case object ScriptGroup extends StopGroup
