package cn.piflow.conf.util


import java.io.{BufferedInputStream, ByteArrayOutputStream, FileInputStream}
import com.sksamuel.scrimage.Image



object ImageUtil {

  def getImage(imagePath:String, bundle:String = "") : Array[Byte] = {
    if(bundle == ""){
      try{
        val classLoader = this.getClass.getClassLoader
        val imageInputStream = classLoader.getResourceAsStream(imagePath)
        val input = new BufferedInputStream(imageInputStream)
        return Image.fromStream(input).bytes
      }catch {
        case ex => {
          println(ex);
          Array[Byte]()
        }
      }
    }else{
      val pluginManager = PluginManager.getInstance
      return pluginManager.getConfigurableStopIcon(imagePath, bundle)
    }
  }

  def saveImage(imageBytes :  Array[Byte], savePath : String) = {
    Image(imageBytes).output(savePath)
  }

}
