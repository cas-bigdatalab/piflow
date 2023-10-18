package cn.piflow.bundle.ceph

import org.apache.spark.sql.{DataFrame, SparkSession}

object CephReadTest {

  var cephAccessKey: String = _
  var cephSecretKey: String = _
  var cephEndpoint: String = _
  var types: String = _
  var path: String = _
  var header: Boolean = _
  var delimiter: String = _

  def main(args: Array[String]): Unit = {
    val spark = SparkSession.builder().
      master("local[*]").
      appName("CephReadTest").
      getOrCreate()

    spark.conf.set("fs.s3a.access.key", cephAccessKey)
    spark.conf.set("fs.s3a.secret.key", cephSecretKey)
    spark.conf.set("fs.s3a.endpoint", cephEndpoint)
    spark.conf.set("fs.s3a.connection.ssl.enabled", "false")

    var df:DataFrame = null

    if (types == "parquet") {
      df = spark.read
        .parquet(path)
    }

    if (types == "csv") {

      df = spark.read
        .option("header", header)
        .option("inferSchema", "true")
        .option("delimiter", delimiter)
        .csv(path)
    }

    if (types == "json") {
      df = spark.read
        .json(path)
    }
    df.show()

  }

}
