package cn.piflow.bundle.util

import java.text.SimpleDateFormat
import java.util.regex.Pattern
import java.util.{Calendar, Date}

import scala.reflect.macros.ParseException

object CleanUtil extends Serializable {
  def processEmail(oriEmail: String): String = { //全角转半角
    var res:String = someTwoBytesCharToOneByte(oriEmail)
    if (res == null) return null
    //字母小写
    res = oriEmail.toLowerCase
    val regularExp = "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-_]+.[A-Za-z0-9.-_]$"
    if (!res.matches(regularExp)) return ""
    res
  }

  def processPhonenum(oriPhonenum: String): String = { //全角转半角
    var res:String = someTwoBytesCharToOneByte(oriPhonenum)
    if (res == null) return null
    //删除非数字
    res = res.replaceAll("[^0-9]", "")
    //正则表达式
    val regularExp = "^1[3|4|5|7|8][0-9]{9}$"
    if (!res.matches(regularExp)) return null
    res
  }

  def processTitle(oriTitle: String): String = { //全角转半角
    val res:String = someTwoBytesCharToOneByte(oriTitle)
    //若不包含空格则输出NULL
    //if (!res.contains(" ")) return null
    res
  }

  def processProvince(word: String): String = {
    var str = ""
    if (word==null) str=""
    else if (word.indexOf("北京") > -1 || word.indexOf("天津") > -1 || word.indexOf("上海") > -1 || word.indexOf("重庆") > -1) str = word.replace("市", "")
    else if (word.indexOf("云南") > -1 || word.indexOf("吉林") > -1 || word.indexOf("四川") > -1 || word.indexOf("安徽") > -1 || word.indexOf("山东") > -1 || word.indexOf("山西") > -1 || word.indexOf("广东") > -1 || word.indexOf("江苏") > -1 || word.indexOf("江西") > -1 || word.indexOf("河北") > -1 || word.indexOf("河南") > -1 || word.indexOf("浙江") > -1 || word.indexOf("海南") > -1 || word.indexOf("湖北") > -1 || word.indexOf("湖南") > -1 || word.indexOf("甘肃") > -1 || word.indexOf("福建") > -1 || word.indexOf("贵州") > -1 || word.indexOf("辽宁") > -1 || word.indexOf("重庆") > -1 || word.indexOf("陕西") > -1 || word.indexOf("青海") > -1 || word.indexOf("黑龙江") > -1) str = word.replace("省", "")
    else if (word.toLowerCase.indexOf("anhui") > -1) str = "安徽"
    else if (word.toLowerCase.indexOf("beijing") > -1) str = "北京"
    else if (word.toLowerCase.indexOf("chongqing") > -1) str = "重庆"
    else if (word.toLowerCase.indexOf("fujian") > -1) str = "福建"
    else if (word.toLowerCase.indexOf("gansu") > -1) str = "甘肃"
    else if (word.toLowerCase.indexOf("guangdong") > -1 || word.toLowerCase.indexOf("guizhou") > -1) str = "广东"
    else if (word.toLowerCase.indexOf("hainan") > -1) str = "海南"
    else if (word.toLowerCase.indexOf("hebei") > -1) str = "河北"
    else if (word.toLowerCase.indexOf("heilongjiang") > -1) str = "黑龙江"
    else if (word.toLowerCase.indexOf("henan") > -1) str = "河南"
    else if (word.toLowerCase.indexOf("hunan") > -1) str = "湖南"
    else if (word.toLowerCase.indexOf("jiangsu") > -1) str = "江苏"
    else if (word.toLowerCase.indexOf("jiangxi") > -1) str = "江西"
    else if (word.toLowerCase.indexOf("jilin") > -1) str = "吉林"
    else if (word.toLowerCase.indexOf("liaoning") > -1) str = "辽宁"
    else if (word.toLowerCase.indexOf("qinghai") > -1) str = "青海"
    else if (word.toLowerCase.indexOf("shaanxi") > -1 || word.toLowerCase.indexOf("shanxi") > -1) str = "陕西"
    else if (word.toLowerCase.indexOf("shandong") > -1) str = "山东"
    else if (word.toLowerCase.indexOf("shanghai") > -1) str = "上海"
    else if (word.toLowerCase.indexOf("sichuan") > -1) str = "四川"
    else if (word.toLowerCase.indexOf("tianjin") > -1) str = "天津"
    else if (word.toLowerCase.indexOf("yunnan") > -1) str = "云南"
    else if (word.toLowerCase.indexOf("zhejiang") > -1) str = "浙江"
    else if (word.indexOf("内蒙古") > -1 || word.toLowerCase.indexOf("inner mongolia") > -1) str = "内蒙古自治区"
    else if (word.indexOf("宁夏") > -1) str = "宁夏回族自治区"
    else if (word.indexOf("广西") > -1 || word.toLowerCase.indexOf("guangxi") > -1) str = "广西壮族自治区"
    else if (word.indexOf("新疆") > -1 || word.toLowerCase.indexOf("xinjiang") > -1) str = "新疆维吾尔自治区"
    else if (word.indexOf("西藏") > -1) str = "西藏自治区"
    else if (!"".equals(word)) str = word
    str
  }

  def someTwoBytesCharToOneByte(oriString: String): String = { //TODO 汉字和全角字符混合是否正常
    if (oriString == null) return null
    var c:Array[Char] = oriString.toCharArray
    for (index <- 0 to c.length-1) {
      if (c(index) == '\u3000') {
        c(index) = ' ';
      } else if (c(index) > '\uFF00' && c(index) < '\uFF5F') {
        c(index) = (c(index) - 65248).toChar;

      }
    }
    return new String(c);

  }


  def processCardCode(cardcode:String):String={
     if (cardcode==null) return null
    //全角转半角
    var res = someTwoBytesCharToOneByte(cardcode)
    //将身份证号末尾X转变为大写
    res = res.toUpperCase
    //去除非数字及末尾x
    res = res.replaceAll("[^0-9Xx]", "")
    //去除首位为0的
    res = res.replaceAll("^0*", "")

    //数字15位，18位，末尾有X
    val regularExp = "^\\d{15}$|^\\d{17}[0-9Xx]$"
    if (res.matches(regularExp) == false) return null

    if (isValidatedAllIdcard(res) == false) return null
    else return res

  }

  protected var codeAndCity = Array(Array("11", "北京"), Array("12", "天津"), Array("13", "河北"), Array("14", "山西"), Array("15", "内蒙古"), Array("21", "辽宁"), Array("22", "吉林"), Array("23", "黑龙江"), Array("31", "上海"), Array("32", "江苏"), Array("33", "浙江"), Array("34", "安徽"), Array("35", "福建"), Array("36", "江西"), Array("37", "山东"), Array("41", "河南"), Array("42", "湖北"), Array("43", "湖南"), Array("44", "广东"), Array("45", "广西"), Array("46", "海南"), Array("50", "重庆"), Array("51", "四川"), Array("52", "贵州"), Array("53", "云南"), Array("54", "西藏"), Array("61", "陕西"), Array("62", "甘肃"), Array("63", "青海"), Array("64", "宁夏"), Array("65", "新疆"), Array("71", "台湾"), Array("81", "香港"), Array("82", "澳门"), Array("91", "国外"))

  private val cityCode = Array("11", "12", "13", "14", "15", "21", "22", "23", "31", "32", "33", "34", "35", "36", "37", "41", "42", "43", "44", "45", "46", "50", "51", "52", "53", "54", "61", "62", "63", "64", "65", "71", "81", "82", "91")

  // 每位加权因子
  private val power = Array(7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)

  // 第18位校检码
  private val verifyCode = Array("1", "0", "X", "9", "8", "7", "6", "5", "4", "3", "2")

  /**
    * 验证所有的身份证的合法性
    *
    * @param idcard
    * @return
    */
  def isValidatedAllIdcard(idcard: String): Boolean = if (idcard.length == 15) true
  else this.isValidate18Idcard(idcard)

  def isValidate18Idcard(idcard: String): Boolean = { // 非18位为假
    if (idcard.length != 18) return false
    // 获取前17位
    val idcard17:String = idcard.substring(0, 17)
    // 获取第18位
    val idcard18Code = idcard.substring(17, 18)
    var c:Array[Char] = null
    var checkCode = ""
    // 是否都为数字
    if (isDigital(idcard17)) {
      c = idcard17.toCharArray
    } else return false
    if (null != c) {
      var bit = new Array[Int](idcard17.length)
      bit = converCharToInt(c)
      var sum17 = 0
      sum17 = getPowerSum(bit)
      // 将和值与11取模得到余数进行校验码判断
      checkCode = getCheckCodeBySum(sum17)
      if (null == checkCode) return false
      // 将身份证的第18位与算出来的校码进行匹配，不相等就为假
      if (!idcard18Code.equalsIgnoreCase(checkCode)) return false
    }
    true
  }

  /**
    * 将15位的身份证转成18位身份证
    *
    * @param idcard
    * @return
    */
  def convertIdcarBy15bit(idcard: String): String = {
    var idcard17:String = null
    // 非15位身份证
    if (idcard.length != 15) return null
    if (isDigital(idcard)) { // 获取出生年月日
      val birthday = idcard.substring(6, 12)
      var birthdate:Date = null
      try
        birthdate = new SimpleDateFormat("yyMMdd").parse(birthday)
      catch {
        case e: ParseException =>
          e.printStackTrace
      }
      val cday = Calendar.getInstance
      cday.setTime(birthdate)
      val year = String.valueOf(cday.get(Calendar.YEAR))
      idcard17 = idcard.substring(0, 6) + year + idcard.substring(8)
      val c = idcard17.toCharArray
      var checkCode = ""
      if (null != c) {
        var bit = new Array[Int](idcard17.length)
        // 将字符数组转为整型数组
        bit = converCharToInt(c)
        var sum17 = 0
        sum17 = getPowerSum(bit)
        // 获取和值与11取模得到余数进行校验码
        checkCode = getCheckCodeBySum(sum17)
        // 获取不到校验位
        if (null == checkCode) return null
        // 将前17位与第18位校验码拼接
        idcard17 += checkCode
      }
    }
    else { // 身份证包含数字
      return null
    }
    idcard17
  }

  /**
    * 15位和18位身份证号码的基本数字和位数验校
    *
    * @param idcard
    * @return
    */
  def isIdcard(idcard: String): Boolean = if (idcard == null || "" == idcard) false
  else Pattern.matches("(^\\d{15}$)|(\\d{17}(?:\\d|x|X)$)", idcard)

  /**
    * 15位身份证号码的基本数字和位数验校
    *
    * @param idcard
    * @return
    */
  def is15Idcard(idcard: String): Boolean = if (idcard == null || "" == idcard) false
  else Pattern.matches("^[1-9]\\d{7}((0\\d)|(1[0-2]))(([0|1|2]\\d)|3[0-1])\\d{3}$", idcard)

  /**
    * 18位身份证号码的基本数字和位数验校
    *
    * @param idcard
    * @return
    */
  def is18Idcard(idcard: String): Boolean = Pattern.matches("^[1-9]\\d{5}[1-9]\\d{3}((0\\d)|(1[0-2]))(([0|1|2]\\d)|3[0-1])\\d{3}([\\d|x|X]{1})$", idcard)

  /**
    * 数字验证
    *
    * @param str
    * @return
    */
  def isDigital(str: String): Boolean = if (str == null || "" == str) false
  else str.matches("^[0-9]*$")

  /**
    * 将身份证的每位和对应位的加权因子相乘之后，再得到和值
    *
    * @param bit
    * @return
    */
  def getPowerSum(bit: Array[Int]): Int = {
    var sum = 0
    if (power.length != bit.length) return sum
    var i = 0
    while ( {
      i < bit.length
    }) {
      var j = 0
      while ( {
        j < power.length
      }) {
        if (i == j) sum = sum + bit(i) * power(j)

        {
          j += 1; j - 1
        }
      }

      {
        i += 1; i - 1
      }
    }
    sum
  }

  /**
    * 将和值与11取模得到余数进行校验码判断
    *
    * @param sum17
    * @return 校验位
    */
  def getCheckCodeBySum(sum17: Int): String = {
    var checkCode:String = null
    import scala.util.control.Breaks._
    breakable {
      sum17 % 11 match {
        case 10 =>
          checkCode = "2"
          break //todo: break is not supported
        case 9 =>
          checkCode = "3"
          break //todo: break is not supported
        case 8 =>
          checkCode = "4"
          break //todo: break is not supported
        case 7 =>
          checkCode = "5"
          break //todo: break is not supported
        case 6 =>
          checkCode = "6"
          break //todo: break is not supported
        case 5 =>
          checkCode = "7"
          break //todo: break is not supported
        case 4 =>
          checkCode = "8"
          break //todo: break is not supported
        case 3 =>
          checkCode = "9"
          break //todo: break is not supported
        case 2 =>
          checkCode = "x"
          break //todo: break is not supported
        case 1 =>
          checkCode = "0"
          break //todo: break is not supported
        case 0 =>
          checkCode = "1"
          break //todo: break is not supported
      }
    }
    checkCode
  }

  /**
    * 将字符数组转为整型数组
    *
    * @param c
    * @return
    * @throws NumberFormatException
    */
  @throws[NumberFormatException]
  def converCharToInt(c: Array[Char]): Array[Int] = {
    val a = new Array[Int](c.length)
    var k = 0
    for (temp <- c) {
      a({
        k += 1; k - 1
      }) = String.valueOf(temp).toInt
    }
    a
  }


}
