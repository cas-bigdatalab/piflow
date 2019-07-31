package cn.piflow.bundle.util
import java.io.{File, FileInputStream}

import org.apache.poi.hssf.usermodel.HSSFWorkbook
import org.apache.poi.ss.usermodel.Workbook
import org.apache.poi.xssf.usermodel.XSSFWorkbook

object XLSUtil {
  def processFile (file : File) : Workbook = {
    val split = file.getName.split("\\.") //.是特殊字符，需要转义！！！！！
    var wb : Workbook = null
    //根据文件后缀（xls/xlsx）进行判断
    if ("xls" == split(1)) {
      val fis = new FileInputStream(file) //文件流对象
      wb = new HSSFWorkbook(fis)
    }
    else if ("xlsx" == split(1)) wb = new XSSFWorkbook(file);
    else {
      throw new Exception("文件类型错误!")
    }
    wb
  }
}
