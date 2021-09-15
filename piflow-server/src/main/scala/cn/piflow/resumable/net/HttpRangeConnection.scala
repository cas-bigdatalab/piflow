package cn.piflow.resumable.net

import java.io.InputStream
import java.net.{HttpURLConnection, URL}

case class HttpRangeConnection(url: String, startOffset: Long = 0, endOffset: Long = 0) {
  val connection: HttpURLConnection = new URL(url).openConnection().asInstanceOf[HttpURLConnection]
  if (endOffset == 0)
    connection.setRequestProperty("Range", s"bytes=$startOffset-")
  else
    connection.setRequestProperty("Range", s"bytes=$startOffset-$endOffset")

  def getInputStream: InputStream = {
    connection.getInputStream
  }

  def getContentLength: Int = {
    connection.getContentLength
  }
}
