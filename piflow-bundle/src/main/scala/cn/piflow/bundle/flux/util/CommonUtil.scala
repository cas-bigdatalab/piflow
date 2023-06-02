package cn.piflow.bundle.flux.util

import org.apache.derby.catalog.SystemProcedures.PI

import java.text.SimpleDateFormat
import scala.math.{acos, atan, sin, tan}

object CommonUtil {
  //将传入的年月日字符串转换成时间戳
  def toTimeStamp(year: String, month: String, day: String, hour: String): Long = {
    val fm = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
    var tm = ""
    if (hour.contains(".5")) {
      tm = s"${year}-${month}-${day} ${hour.split("\\.")(0)}:30:00"
    } else {
      tm = s"${year}-${month}-${day} ${hour.split("\\.")(0)}:00:00"
    }
    val dt = fm.parse(tm)
    dt.getTime
  }


  /**
   * 根据经纬度计算日落日出时间
   *
   * @param longitude
   * @param latitude
   * @param J 日序数，为1到365或366之间整数
   * @return
   */
  def SunriseAndSunsetTime(longitude: Double, latitude: Double, J: Int): String = {
    //    计算赤纬正切值
    val δ = 0.409 * sin((2 * PI * J / 365) - 1.39)
    //    计算赤纬（弧度）
    val δ_rad = atan(δ)
    //    计算日照时间
    val t = 24 * acos((-1) * tan(latitude * PI / 180) * tan(δ_rad)) / PI
    //    日出时间（以北京时间计）
    val sunrise = (12 - t / 2) - ((longitude - 120) * 24 / 360)

    //    日落时间（以北京时间计）
    val sunset = (12 + t / 2) - ((longitude - 120) * 24 / 360)

    sunrise.formatted("%.2f") + "," + sunset.formatted("%.2f")
  }


}
