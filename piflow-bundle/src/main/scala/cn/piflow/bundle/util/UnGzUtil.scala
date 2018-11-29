package cn.piflow.bundle.util

import java.io._
import java.util.zip.GZIPInputStream

import org.apache.spark.sql.DataFrame
import sun.net.ftp.FtpProtocolException

object UnGzUtil extends Serializable{

  var filePath:String = null

  def unGz(inputDir:String,savePath:String,filename:String):String = {

    try {
      val fileInput = new FileInputStream(inputDir)
      val gzip = new GZIPInputStream(fileInput)

      val outDir = new File(savePath)
      outDir.mkdirs()

      if (savePath.endsWith("/")){
        filePath = savePath+filename
      } else {
        filePath = savePath+"/"+filename
      }

      val buff = new Array[Byte](1024)
      val out = new BufferedOutputStream(new FileOutputStream(new File(outDir,filename)))

      var count = -1
      while ((count = gzip.read(buff)) != -1 && (count != -1) ){

        out.write(buff,0,count)
      }
      out.close()
    } catch {
      case  e:FtpProtocolException=>
        e.printStackTrace()
      case  e: IOException =>
        e.printStackTrace()
    }

    return  filePath
  }



  def unGzStream(inputDir:String):Array[Byte] = {

    var  gzip:GZIPInputStream = null
    var byteArrayOutputStream:ByteArrayOutputStream=new ByteArrayOutputStream()
    val buffer=new Array[Byte](1024*1024)

    val fileInput = new FileInputStream(inputDir)
    gzip = new GZIPInputStream(fileInput)

    var count = -1
    while ((count = gzip.read(buffer)) != -1 && (count != -1) ){

      byteArrayOutputStream.write(buffer,0,count)

    }

    val byteArray: Array[Byte] = byteArrayOutputStream.toByteArray

    return  byteArray
  }

}
