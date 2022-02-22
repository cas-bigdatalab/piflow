package com.piflow.sql.util


import java.security.MessageDigest

object MD5Util {
  def encode(input: String): String = {


    val md5 = MessageDigest.getInstance("MD5")
    val encoded = md5.digest(input.getBytes)
    encoded.map("%02x".format(_)).mkString
  }

}
