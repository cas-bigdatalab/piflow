package cn.piflow.conf.util

import java.io.{BufferedInputStream, FileInputStream}

import com.sksamuel.scrimage.Image


object ImageUtil {

  def getImage(imagePath:String) : Array[Byte] = {
    val input = new BufferedInputStream(new FileInputStream(imagePath))
    Image.fromStream(input).bytes
  }

  def saveImage(imageBytes :  Array[Byte], savePath : String) = {
    Image(imageBytes).output(savePath)
  }

}
