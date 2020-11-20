package cn.piflow.conf.bean

import cn.piflow.conf.Language
import net.liftweb.json.JsonDSL._
import net.liftweb.json._

class PropertyDescriptor {
  var name : String = _
  var displayName : String = _
  var description : String = _
  var defaultValue : String = _
  var allowableValues : List[String] = _
  var required : Boolean = false
  var sensitive : Boolean = false
  var example : String = _
  var language : String = Language.Text


  def name(name:String) : PropertyDescriptor = {
    this.name = name
    this
  }
  def displayName(displayName:String) : PropertyDescriptor = {
    this.displayName = displayName
    this
  }
  def description(description:String) : PropertyDescriptor = {
    this.description = description
    this
  }
  def example(example: String) : PropertyDescriptor = {
    this.example = example
    this
  }
  def defaultValue(defaultValue:String) : PropertyDescriptor = {
    this.defaultValue = defaultValue
    this
  }
  def allowableValues(allowableValues:Set[String]) : PropertyDescriptor = {
    this.allowableValues = allowableValues.toList
    this
  }
  def required(required:Boolean) : PropertyDescriptor = {
    this.required = required
    this
  }
  def sensitive(sensitive:Boolean) : PropertyDescriptor = {
    this.sensitive = sensitive
    this
  }
  def language(language: String) : PropertyDescriptor = {
    this.language = language
    this
  }
  def toJson():String = {
    val allowableValueStr = if(this.allowableValues == null)  "" else this.allowableValues.mkString(",")
    val json =
      ("property" ->
        ("name" -> this.name) ~
          ("displayName" -> this.displayName) ~
          ("description" -> this.description) ~
          ("defaultValue" -> this.defaultValue) ~
          ("allowableValues" -> allowableValueStr) ~
          ("required" -> this.required.toString) ~
          ("sensitive" -> this.sensitive.toString))


    val jsonString = compactRender(json)
    jsonString
  }
}

object PropertyDescriptor{
  def apply(): PropertyDescriptor = {
    new PropertyDescriptor()
  }
}

