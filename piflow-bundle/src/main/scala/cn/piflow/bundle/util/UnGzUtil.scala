//package cn.piflow.bundle.util
//
//import java.io._
//import java.util
//import java.util.zip.GZIPInputStream
//
//import org.apache.tools.tar.{TarEntry, TarInputStream}
//import sun.net.ftp.FtpProtocolException
//
//object UnGzUtil extends Serializable{
//
//  var filePath:String = null
//
//  def unTarGz(inputDir:String,savePath:String)={
//    var list = new util.ArrayList[String]()
//    try {
//      val fileInput = new FileInputStream(inputDir)
//      val gzip = new GZIPInputStream(new BufferedInputStream(fileInput))
//      val tarIn = new TarInputStream(gzip, 1024 * 2)
//
//      val outDir = new File(savePath)
//      outDir.mkdirs()
//
//      var entry: TarEntry = null
//
//      while ((entry = tarIn.getNextEntry) != null  && entry !=null) {
//
//        // 是目录
//        if (entry.isDirectory()) {
//          val outPath = savePath + "/" + entry.getName
//          // 创建输出目录
//          val outDir = new File(outPath)
//          outDir.mkdirs()
//        } else {
//          // 文件
//          val outDir = new File(savePath + "/" + entry.getName)
//
//          list.add(outDir.toString)
//          val out = new FileOutputStream(outDir)
//
//          var lenth = 0
//          val buff = new Array[Byte](1024)
//          while ((lenth = tarIn.read(buff)) != -1 && (lenth != -1)) {
//            out.write(buff, 0, lenth)
//          }
//          out.close()
//        }
//      }
//    }catch {
//      case  e: IOException =>
//        e.printStackTrace()
//    }
//
//    list
//  }
//
//
//
//  def unGz(inputDir:String,savePath:String,filename:String):String = {
//    try {
//      val fileInput = new FileInputStream(inputDir)
//      val gzip = new GZIPInputStream(fileInput)
//
//      val outDir = new File(savePath)
//      outDir.mkdirs()
//
//      if (savePath.endsWith("/")){
//        filePath = savePath+filename
//      } else {
//        filePath = savePath+"/"+filename
//      }
//
//      val buff = new Array[Byte](1024)
//      val out = new BufferedOutputStream(new FileOutputStream(new File(outDir,filename)))
//
//      var count = -1
//      while ((count = gzip.read(buff)) != -1 && (count != -1) ){
//
//        out.write(buff,0,count)
//      }
//      out.close()
//    } catch {
//      case  e:FtpProtocolException=>
//        e.printStackTrace()
//      case  e: IOException =>
//        e.printStackTrace()
//    }
//    return  filePath
//  }
//
//
//
//  def unGzStream(inputDir:String):Array[Byte] = {
//
//    var  gzip:GZIPInputStream = null
//    var byteArrayOutputStream:ByteArrayOutputStream=new ByteArrayOutputStream()
//    val buffer=new Array[Byte](1024*1024)
//
//    val fileInput = new FileInputStream(inputDir)
//    gzip = new GZIPInputStream(fileInput)
//
//    var count = -1
//    while ((count = gzip.read(buffer)) != -1 && (count != -1) ){
//
//      byteArrayOutputStream.write(buffer,0,count)
//
//    }
//
//    val byteArray: Array[Byte] = byteArrayOutputStream.toByteArray
//
//    return  byteArray
//  }
//
//}
