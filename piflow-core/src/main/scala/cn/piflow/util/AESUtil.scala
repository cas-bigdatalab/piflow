package cn.piflow.util

import java.io._
import java.security.SecureRandom

import javax.crypto.{Cipher, CipherInputStream, KeyGenerator, SecretKey}
import javax.crypto.spec.SecretKeySpec
import org.apache.commons.codec.binary.Hex

object AESUtil {
  private val KEY_ALGORITHM = "AES"
  private val DEFAULT_CIPHER_ALGORITHM = "AES/ECB/PKCS5Padding" //default encryption algorithm

  private val SECRET = "BIG_FLOW"

  /*def main(args: Array[String]): Unit = {
    val key:String = "doge"
    println(key)
    val wrapkey = wrap(key)
    println(wrapkey)
//    val a1 = wrapkey+System.getProperty("line.separator")
    val str = unwrap(wrapkey)
    println(str)
//    println(unwrap(a1))

    val path = "/opt/case/piflow-datacenter/piflow/piflow-server/src/main/resources/log4j.properties"
    val file:File = new File(path)
    val in:InputStream = new FileInputStream(file)

    val cipStream: CipherInputStream = aesInputStream(key,in)
    val decStream: CipherInputStream = decryptInputStream(cipStream,key)
    val reader:BufferedReader = new BufferedReader(new InputStreamReader(decStream,"utf-8"))
    //      val reader:BufferedReader = new BufferedReader(new InputStreamReader(inputStream,"utf-8"))
    var flag = true
    var line :String = null;
    //      val bytes: Array[Byte] = Array()[Byte]
    while (flag){
      //        inputStream.read(bytes)
      line = reader.readLine()
      if (line !=null){
        println(line)
      }else{
        flag = false;
      }
    }

  }*/

  //Generate a secret key based on key
  def getSecretKey(key: String): SecretKeySpec = {
      val kg: KeyGenerator = KeyGenerator.getInstance(KEY_ALGORITHM)
      val random = SecureRandom.getInstance("SHA1PRNG")
      random.setSeed(key.getBytes)
//      kg.init(128, new SecureRandom(key.getBytes))
      kg.init(128, random)
      val secretKey: SecretKey = kg.generateKey()
      new SecretKeySpec(secretKey.getEncoded, KEY_ALGORITHM)
  }


  def aesInputStream(key: String, in: InputStream): CipherInputStream = {
    val secretKeySpec = getSecretKey(key)
//    val secretKeySpec = new SecretKeySpec(key.getBytes("UTF-8"),DEFAULT_CIPHER_ALGORITHM)
    val cipher: Cipher = Cipher.getInstance(DEFAULT_CIPHER_ALGORITHM)
    cipher.init(Cipher.ENCRYPT_MODE, secretKeySpec)
    new CipherInputStream(in, cipher)
  }

  def decryptInputStream(in: InputStream, key: String): CipherInputStream = {
    val secretKeySpec = getSecretKey(key)
//    val secretKeySpec = new SecretKeySpec(key.getBytes("UTF-8"),DEFAULT_CIPHER_ALGORITHM)
    val cipher: Cipher = Cipher.getInstance(DEFAULT_CIPHER_ALGORITHM)
    cipher.init(Cipher.DECRYPT_MODE, secretKeySpec)
    new CipherInputStream(in, cipher)
  }

  /*def wrap(key: String, secrect: String): String = {
    val kg: KeyGenerator = KeyGenerator.getInstance(KEY_ALGORITHM)
    kg.init(128, new SecureRandom(secrect.getBytes))
    val secretKey: SecretKey = kg.generateKey()
    val secretKeySpec: SecretKeySpec = new SecretKeySpec(secretKey.getEncoded, KEY_ALGORITHM)
    val cipher: Cipher = Cipher.getInstance(KEY_ALGORITHM)
    cipher.init(Cipher.WRAP_MODE, secretKeySpec)
    val tempKey: SecretKeySpec = new SecretKeySpec(key.getBytes(),KEY_ALGORITHM)
    val bytes: Array[Byte] = cipher.wrap(tempKey)
    Hex.encodeHexString(bytes)
  }*/

  def wrap(keyString: String): String = {
    val kg: KeyGenerator = KeyGenerator.getInstance(KEY_ALGORITHM)
    val random = SecureRandom.getInstance("SHA1PRNG")
    random.setSeed(SECRET.getBytes)
    kg.init(128, random)
    val secretKey: SecretKey = kg.generateKey()
    val secretKeySpec: SecretKeySpec = new SecretKeySpec(secretKey.getEncoded, KEY_ALGORITHM)
    val cipher: Cipher = Cipher.getInstance(KEY_ALGORITHM)
    cipher.init(Cipher.WRAP_MODE, secretKeySpec)
    val tempKey: SecretKeySpec = new SecretKeySpec(keyString.getBytes(),KEY_ALGORITHM)
    val bytes: Array[Byte] = cipher.wrap(tempKey)
    Hex.encodeHexString(bytes)
  }

  /*def unwrap(key:String,secret:String) :String={
    val rawKey: Array[Byte] = Hex.decodeHex(key.toCharArray)
    val kg: KeyGenerator = KeyGenerator.getInstance(KEY_ALGORITHM)
    kg.init(128, new SecureRandom(secret.getBytes))
    val secretKey: SecretKey = kg.generateKey()
    val secretKeySpec: SecretKeySpec = new SecretKeySpec(secretKey.getEncoded, KEY_ALGORITHM)
    val cipher: Cipher = Cipher.getInstance(KEY_ALGORITHM)
    cipher.init(Cipher.UNWRAP_MODE, secretKeySpec)
    val returnKey: SecretKey = cipher.unwrap(rawKey,KEY_ALGORITHM,Cipher.SECRET_KEY).asInstanceOf[SecretKey]
    String.valueOf(returnKey.getEncoded)
  }*/

  def unwrap(keyString:String) :String={
    val rawKey = Hex.decodeHex(keyString.toCharArray)
    val kg: KeyGenerator = KeyGenerator.getInstance(KEY_ALGORITHM)
    val random = SecureRandom.getInstance("SHA1PRNG")
    random.setSeed(SECRET.getBytes)
    kg.init(128, random)
    val secretKey: SecretKey = kg.generateKey()
    val secretKeySpec: SecretKeySpec = new SecretKeySpec(secretKey.getEncoded, KEY_ALGORITHM)
    val cipher = Cipher.getInstance(KEY_ALGORITHM)
    cipher.init(Cipher.UNWRAP_MODE, secretKeySpec)
    val returnKey = cipher.unwrap(rawKey,KEY_ALGORITHM,Cipher.SECRET_KEY).asInstanceOf[SecretKey]
    new String(returnKey.getEncoded)
  }

}
