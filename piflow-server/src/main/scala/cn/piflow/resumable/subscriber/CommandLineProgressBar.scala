package cn.piflow.resumable.subscriber

import cn.piflow.resumable.downloader.PartialResponse

case class CommandLineProgressBar(totalSize: Float) extends DownloadSubscriber {
  var progress: Float = 0

  def tick(chunkSize: Float): Unit = {
    progress += (chunkSize * 100.0f) / totalSize
    System.out.printf(s"\r\b Download Progress [ ${progress.asInstanceOf[Int]}%% ]")
  }

  override def notify(partialResponse: PartialResponse): Unit = {
    tick(partialResponse.size)
  }

  override def completed(): Unit = {
    System.out.printf("\r\b Downloaded completed")
  }
}