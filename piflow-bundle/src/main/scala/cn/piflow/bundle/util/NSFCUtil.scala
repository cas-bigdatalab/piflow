package cn.piflow.bundle.util

import java.text.SimpleDateFormat
import java.util.{Date, UUID}

import org.apache.spark.sql.Row
import org.apache.spark.sql.types.{LongType, StringType, StructField, StructType}

object NSFCUtil {
  val dateFormat: SimpleDateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
  val add_field = Array(
    StructField("0", StringType, nullable = true),
    StructField("identity_card", StringType, nullable = true),
    StructField("military_id", StringType, nullable = true),
    StructField("passport", StringType, nullable = true),
    StructField("4", StringType, nullable = true),
    StructField("home_return_permit", StringType, nullable = true),
    StructField("mainland_travel_permit_for_taiwan_residents", StringType, nullable = true)
  )
  def buildNewOPersonRow (beforeRowSeq : Seq[Any], beforeSchema:StructType, afterSchema:StructType, idTypeField : String, idField :String, source:String): Row = {
    var afterSeq = scala.collection.mutable.ArraySeq[Any]()
    var afterMap = scala.collection.mutable.HashMap[String, Any]()

    var card_type: String = ""
    var card_code: String = ""

    var zero = "null"
    var one = "null"
    var two = "null"
    var three = "null"
    var four = "null"
    var five = "null"
    var six = "null"
    //Seq[V] -> Map[K,V]
    for (index <- 0 until beforeSchema.length) {
      val name = beforeSchema(index).name
      name match {
        case `idTypeField` => if (beforeRowSeq(index) == null)
          card_type = "null" else card_type = String.valueOf(beforeRowSeq(index))
        case `idField` => if (beforeRowSeq(index) == null)
          card_code = "null" else card_code = String.valueOf(beforeRowSeq(index))
        case _ => afterMap.put(beforeSchema(index).name, beforeRowSeq(index))
      }
    }
    card_type match {
      case id_type.MAINLAND.id => six = card_code //6
      case id_type.FOUR.id => four = card_code //4
      case id_type.HOMERETURN.id => five = card_code //5
      case id_type.MILITARY.id => two = card_code //2
      case id_type.IDENTITY_CARD.id => one = card_code //1
      case id_type.PASSPORT.id => three = card_code //3
      case id_type.ZERO.id => zero = card_code //0
      case _ =>
    }
    afterMap.put("0", ifNUll(zero))
    afterMap.put("identity_card", ifNUll(one))
    afterMap.put("military_id", ifNUll(two))
    afterMap.put("passport", ifNUll(three))
    afterMap.put("4", ifNUll(four))
    afterMap.put("home_return_permit", ifNUll(five))
    afterMap.put("mainland_travel_permit_for_taiwan_residents", ifNUll(six))
    afterMap.put("source", source) // 加入source字段
    afterMap.put("uuid", UUID.randomUUID().toString)
    afterMap.put("id_hash", (card_code + card_type).##.toString)
    for (index <- 0 until afterSchema.length) {
      if (!afterMap.keySet.contains(afterSchema(index).name)) {
        afterMap.put(afterSchema(index).name, null)
      }
    }
    for (field <- afterSchema) {
      afterSeq = afterSeq.:+(afterMap(field.name))
    }

    Row.fromSeq(afterSeq)
  }

  def ifNUll(value : String): Any = {
    if (value.equals("null")) null else value
  }

  def mkPersonSchemaWithID(beforeSchema : StructType, idTypeField : String, idField :String) : StructType ={
    var afterSchema = new StructType(beforeSchema.filter(field => {field.name != idField && field.name != idTypeField}).toArray)
    add_field.foreach(f => {
      afterSchema = afterSchema.add(f.name, f.dataType,nullable = true)
    })
    afterSchema = afterSchema.add("source", StringType, nullable = true)
    afterSchema = afterSchema.add("uuid", StringType, nullable = true)
    afterSchema.add("id_hash", StringType, nullable = true)
  }


  def getTime(row : Row, timeIndex : Int) : Date = {
    if (row.isNullAt(timeIndex)) new Date(0)
    else {
      var date:java.util.Date = null
      val s = row.getString(timeIndex)
      try {
        date = dateFormat.parse(s)
      } catch {
        case _ => date = new Date(0)
      }
      date
    }
  }
  def mkRowKey(schema_result:StructType, row: Row, key : String): String = {
    var hasNull = false
    var s = ""
    if (key.contains("&")) {
      val sl = key.split("&")
      sl.foreach(s_ => {
        val index = schema_result.fieldIndex(s_)
        if (!row.isNullAt(index)) {
          s += row.getAs[String](index)
        } else {
          hasNull = true
        }
      })
    } else {
      val index = schema_result.fieldIndex(key)
      if (!row.isNullAt(index)) {
        s = row.getAs[String](index)
      } else {
        hasNull = true
      }
    }
    if (hasNull) {
      s = generateUUID() // key 为空则生产uuid
    }
    s
  }
  def generateUUID(): String = {
    UUID.randomUUID().toString
  }
}
object id_type extends Enumeration {
  val MAINLAND: id = id("6", "mainland_travel_permit_for_taiwan_residents")
  val IDENTITY_CARD: id = id("1", "identity_card")
  val MILITARY: id = id("2", "military_id")
  val PASSPORT: id = id("3", "passport")
  val HOMERETURN: id = id("5", "home_return_permit")
  val ZERO: id = id("0", "ZERO")
  val FOUR: id = id("4", "FOUR")
  type id_type = id
}
case class id(id :String, name :String) extends Serializable {
  override def equals(obj: scala.Any): Boolean = {
    if (this == obj) return true
    obj match {
      case anotherId: id => this.id == anotherId.id
      case _ => false
    }
  }
}
