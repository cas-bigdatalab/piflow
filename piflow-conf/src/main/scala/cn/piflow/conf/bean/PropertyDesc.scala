package cn.piflow.conf.bean

class PropertyDescriptor {
  var name : String = _
  var displayName : String = _
  var description : String = _
  var defaultValue : String = _
  var allowableValues : List[String] = _
  var required : Boolean = false
  var sensitive : Boolean = false


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
}
object PropertyDescriptor{
  def apply(): PropertyDescriptor = {
    new PropertyDescriptor()
  }
}

