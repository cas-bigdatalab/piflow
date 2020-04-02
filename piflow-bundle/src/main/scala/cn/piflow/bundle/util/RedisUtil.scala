package cn.piflow.bundle.util
import java.util

import org.apache.spark.sql.types.StructType
import org.apache.spark.sql.{Dataset, Row}
import redis.clients.jedis.JedisCluster

import scala.util.control.Breaks.{break, breakable}
object RedisUtil extends Serializable {

  def manipulateRow(row:Row,column_name:String,jedisClusterImplSer: JedisClusterImplSer):Unit={
    var hm:util.HashMap[String,String]=new util.HashMap()

    val key=row.getAs(column_name).asInstanceOf[String]

    row.schema.fields.foreach(f=>{
      if (row.getAs(f.name).asInstanceOf[String] == null ) hm.put(f.name,"None")
      else hm.put(f.name,row.getAs(f.name).asInstanceOf[String])

    })

    println(hm)

    jedisClusterImplSer.getJedisCluster.hmset(key,hm)

  }
  /**
    *
    * @param row 存入redis的行
    * @param map 字段名称与位置索引
    * @param build 字段名 <- 用以去重的字段
    * @param valueIndex PSNCODE的位置
    * @param jedisCluster
    */
  def putRedis(row: Row, map: Map[String, Int], build :String, valueIndex:Int, jedisCluster: JedisCluster): Unit = {
    var hasNull = false
    var value = row.getString(valueIndex) //get the primary key
    build.split(",").foreach(idKey => { //name&tel,name&email
      var field = idKey
      var key = ""
      if (idKey.contains("&")) { //name&tel
        val sl = idKey.split("&")
        sl.foreach(s_ => {
          if (!row.isNullAt(map(s_))) {
            key += row.getString(map(s_))
          } else {hasNull = true}
        })
      }
      else {
        if (!row.isNullAt(map(idKey))) {
          key += row.getString(map(idKey))
        } else {hasNull = true}
      }
      if (!hasNull) {
        jedisCluster.hset(key,field,value) // combined keys - fields - psn_code
        //        println(key + ":" + field + ":" + value)   test pass
      }
    })
  }

  /**
    *
    * @param row 需要检查的row
    * @param schema 该row对应的schema
    * @param checkField 需要检查的字段
    * @return id(如果不存在psn)或者psn code
    */
  def checkRedis(row:(String, Row), schema:StructType, tableName : String ,psnType : String,checkField:Seq[String], jedisCluster: JedisCluster) : String = {
    var Psn = ""
    var hasPSN = false
    var hasNull = false
    breakable {
      checkField.foreach(idKey => {
        var field = idKey
        var key = ""
        if (idKey.contains("&")) {
          val sl = idKey.split("&")
          sl.foreach(s_ => {
            if (!row._2.isNullAt(schema.fieldIndex(s_))) {
              key += row._2.getString(schema.fieldIndex(s_))
            } else {hasNull = true}
          })
        } else {
          if (!row._2.isNullAt(schema.fieldIndex(idKey))) {
            key += row._2.getString(schema.fieldIndex(idKey))
          } else {hasNull = true}
        }
        if (!hasNull) {
          if(jedisCluster.hexists(key, field)) {
            Psn = jedisCluster.hget(key, field)
            jedisCluster.hset(tableName + "@" + row._1, psnType + "PSNExist",Psn)//存储匹配到的ID，这部分不需要插入M_PERSON
            hasPSN = true
            break()
          }
        }
      })
    }
    if (hasPSN) {
      Psn
    } else {
      psnType + generatePSN(row._1, psnType)
    }
  }

  def generatePSN(s : String, psnType : String) : String = {
    var a = ("psn" + s + psnType).##
    if (a < 0) "n" + (a * -1).toString
    else a.toString
  }

  def recordMKDup(rows: Iterable[(String,Row)], tableName : String, jedisCluster: JedisCluster) :(String,Row) = {
    var f = rows.head //rows length >= 1
    if (rows.size < 2) return f //only one elem
    for (row <- rows) {
      jedisCluster.hset(tableName + "@" + row._1 ,tableName + ":MK - S", f._1) //set son =:MK - S=> father (1 -> 1)
    }
    f
  }

  def getMKFather(key:String, tableName : String,psnType : String, jedisCluster: JedisCluster): String = {
    val s = jedisCluster.hget(tableName + "@" + key, tableName + ":MK - S")
    if (s == null || s == key) jedisCluster.hget(tableName + "@" + key,psnType + "IdPSN") //not son of any return itself
    // I know you will feel confuse , just relax :-)
    else getMKFather(s,psnType, tableName, jedisCluster)
  }
  //use record first
  def gatherDup(rows : Array[Row], primaryKeyIndex:Int, primaryKey : String): Row = {
    var f = rows.head //rows length >= 1
    if (rows.length < 2) return f //only one elem
    var father = f.toSeq.toArray
    for (index <- 1 until rows.length) {
      var row = rows(index)
      if (row != null && f != null){ //null pointer
        father = gatherDup_(father, row.toSeq.toArray, onlyNullReplace = true, primaryKeyIndex, primaryKey)
      }
    }
    Row.fromSeq(father.toSeq)
  }

  def getKey(row:Row, index:Int): String = {
    var temp = row.get(index)
    if (temp == null) ""
    else temp.toString
  }


  def gatherDup_(a: Array[Any], b: Array[Any],  onlyNullReplace: Boolean, Pindex:Int, PK: String): Array[Any] = {
    if (onlyNullReplace) {
      var index = 0
      for (a_ <- a) {
        if (a_ == null) a.update(index, b(index))
        index += 1
      }
    } else {
      var index = 0
      for (a_ <- a; b_ <- b) {
        a.update(index, a_ + "," + b_)
        index += 1
      }
    }
    a.update(Pindex, PK)
    a
  }

  def resetRedis(jedisCluster: JedisCluster): Unit = {
    import scala.collection.JavaConversions._
    for (pool <- jedisCluster.getClusterNodes.values) {
      try {
        val jedis = pool.getResource
        try
          jedis.flushAll
        catch {
          case ex: Exception =>
            System.out.println(ex.getMessage)
        } finally if (jedis != null) jedis.close()
      }
    }
  }
}
