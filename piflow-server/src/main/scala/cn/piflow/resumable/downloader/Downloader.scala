package cn.piflow.resumable.downloader

trait Downloader {
  def download(remoteResource: RemoteResource): Unit
}
