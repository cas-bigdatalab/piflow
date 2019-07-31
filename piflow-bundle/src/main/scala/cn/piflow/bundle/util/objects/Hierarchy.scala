package cn.piflow.bundle.util.objects

/**
  * Here are four common pitfalls2
  * that can cause inconsistent behavior when
  * overriding equals:
  * 1. Defining equals with the wrong signature.
  * 2. Changing equals without also changing hashCode.
  * 3. Defining equals in terms of mutable fields.
  * 4. Failing to define equals as an equivalence relation.
  *
  * @param FOS
  * @param ApplyID
  */
class Hierarchy (val FOS: String, val ApplyID : String)extends Serializable {
  override def hashCode(): Int = {
    (FOS + ApplyID).hashCode
  }

  override def equals(obj: Any): Boolean = {
    if (obj == null) false
    else {
      if (!obj.isInstanceOf[Hierarchy]) {
        false
      } else {
        val tmp = obj.asInstanceOf[Hierarchy]
        if (tmp.ApplyID == this.ApplyID && tmp.FOS == this.FOS) true else false
      }
    }
  }

  override def clone(): AnyRef = {
    new Hierarchy(FOS, ApplyID)
  }

  override def toString: String = {
    s"FOS : $FOS , ApplyID : $ApplyID"
  }
}

class HierarchyKeyword (val keyword: String, val hierarchy: Hierarchy) extends Serializable {
  override def hashCode(): Int = {
    (keyword + hierarchy.FOS + hierarchy.ApplyID).hashCode
  }

  override def equals(obj: Any): Boolean = {
    if (obj == null) false
    else {
      if (!obj.isInstanceOf[HierarchyKeyword]) {
        false
      } else {
        val tmp = obj.asInstanceOf[HierarchyKeyword]
        if (tmp.hierarchy.ApplyID == this.hierarchy.ApplyID &&
          tmp.hierarchy.FOS == this.hierarchy.FOS &&
          tmp.keyword == this.keyword ) true
        else false
      }
    }
  }

  override def clone(): AnyRef = {
    new HierarchyKeyword(keyword, new Hierarchy(this.hierarchy.FOS, this.hierarchy.ApplyID))
  }

  override def toString: String = {
    s"keyword info => \n" +
      s"name : ${this.keyword} , FOS : ${this.hierarchy.FOS} , ApplyID : ${this.hierarchy.ApplyID}"
  }

  def toSimpleHash : Int = {
    (this.keyword + hierarchy.FOS).hashCode
  }
}