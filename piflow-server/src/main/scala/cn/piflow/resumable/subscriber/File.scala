package cn.piflow.resumable.subscriber

import java.io.FileOutputStream
import java.nio.file.{Files, Paths}

import cn.piflow.resumable.downloader.PartialResponse

import scala.util.Try

case class File(url: String) extends DownloadSubscriber {
  private val fileName = Paths.get(url).getFileName.toString
  private val fileWriter = new FileOutputStream(fileName, true)

  def downloadedSize(): Long = {
    Try(Files.size(Paths.get(fileName))).getOrElse(0)
  }

  override def notify(partialResponse: PartialResponse): Unit = {
    fileWriter.write(partialResponse.body)
  }

  override def completed(): Unit = {
    fileWriter.close()
  }
}
