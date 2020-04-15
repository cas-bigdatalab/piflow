package cn.piflow.conf.util

import java.io.{BufferedInputStream, FileInputStream}

import com.sksamuel.scrimage.Image


object ImageUtil {

  def getImage(imagePath:String) : Array[Byte] = {
    try{
      val classLoader = this.getClass.getClassLoader
      val imageInputStream = classLoader.getResourceAsStream(imagePath)
      val input = new BufferedInputStream(imageInputStream)
      Image.fromStream(input).bytes
    }catch {
      case ex => println(ex); Array[Byte]()
    }
  }

  def saveImage(imageBytes :  Array[Byte], savePath : String) = {
    Image(imageBytes).output(savePath)
  }

}
