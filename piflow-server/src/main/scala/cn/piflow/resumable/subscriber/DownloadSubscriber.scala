package cn.piflow.resumable.subscriber

import cn.piflow.resumable.downloader.PartialResponse

trait DownloadSubscriber {
  def notify(partialResponse: PartialResponse)
  def completed(): Unit
}
