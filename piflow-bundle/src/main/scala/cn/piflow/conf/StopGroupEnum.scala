package cn.piflow.conf

object StopGroupEnum extends Enumeration {

  type StopGroup = Value
  val CommonGroup = Value("CommonGroup")
  val CsvGroup = Value("CsvGroup")
  val HiveGroup = Value("HiveGroup")
  val JdbcGroup = Value("JdbcGroup")
  val JsonGroup = Value("JsonGroup")
  val XmlGroup = Value("XmlGroup")
  val HttpGroup = Value("HttpGroup")
  val FtpGroup = Value("FtpGroup")
  val ScriptGroup = Value("ScriptGroup")
  val FileGroup = Value("FileGroup")
  val CleanGroup = Value("CleanGroup")
  val KafkaGroup = Value("kafkaGroup")
  val RedisGroup = Value("RedisGroup")
  val SolrGroup = Value("SolrGroup")
  val ESGroup = Value("ESGroup")
  val MLGroup = Value("MLGroup")
  val RDFGroup = Value("RDFGroup")
  val UrlGroup= Value("UrlGroup")

}
