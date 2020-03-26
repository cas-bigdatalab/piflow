package cn.piflow.bundle.test

import cn.piflow.conf.util.ImageUtil.{getImage, saveImage}
import org.junit.Test

class ImageTest {

  @Test
  def testGetImage() : Unit = {
    //println(new File(".").getAbsolutePath)
    val imagePath : String = "./src/test/resources/test.jpg"
    val imageSavePath : String = "./src/test/resources/test_copy.jpg"

    val imageByte = getImage(imagePath)

    println(imageByte)

    saveImage(imageByte, imageSavePath)

  }


}
