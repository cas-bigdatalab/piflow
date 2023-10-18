package com.dkl.s3.spark

import org.apache.spark.sql.{DataFrame, SparkSession}

object CephWriteTest {
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
      appName("SparkS3Demo").
      getOrCreate()

    spark.conf.set("fs.s3a.access.key", cephAccessKey)
    spark.conf.set("fs.s3a.secret.key", cephSecretKey)
    spark.conf.set("fs.s3a.endpoint", cephEndpoint)
    spark.conf.set("fs.s3a.connection.ssl.enabled","false")


    import spark.implicits._
    val df = Seq((1, "json", 10, 1000, "2022-09-27")).toDF("id", "name", "value", "ts", "dt")

    if (types == "parquet") {
      df.write
        .format("parquet")
        .mode("overwrite") // only overwrite
        .save(path)
    }

    if (types == "csv") {
      df.write
        .format("csv")
        .option("header", header)
        .option("delimiter", delimiter)
        .mode("overwrite")
        .save(path)
    }

    if (types == "json") {
      df.write
        .format("json")
        .mode("overwrite")
        .save(path)
    }

  }

}
