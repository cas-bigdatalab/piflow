package cn.piflow.resumable

import cn.piflow.resumable.downloader.{ParallelDownloader, RemoteResource}
import cn.piflow.resumable.subscriber.CommandLineProgressBar

object Test {

  def main(args: Array[String]): Unit = {

    val url = "http://mirrors.standaloneinstaller.com/video-sample/jellyfish-25-mbps-hd-hevc.3gp"
    val resource = RemoteResource(url)
    val progressBar = CommandLineProgressBar(resource.size())

    ParallelDownloader(progressBar).download(resource)
  }
}
