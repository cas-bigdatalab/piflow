package cn.piflow.schedule

import java.sql.Date

/**
  * Created by xjzhu@cnic.cn on 4/25/19
  */

trait Condition[T<:Execution] {
  def matches(pg: T): Boolean;

}

class AndCondition[T<:Execution](con1: Condition[T], con2: Condition[T]) extends Condition[T] {
  override def matches(pg: T): Boolean = {
    con1.matches(pg) && con2.matches(pg);
  }
}

class OrCondition[T<:Execution](con1: Condition[T], con2: Condition[T]) extends Condition[T] {
  override def matches(pg: T): Boolean = {
    con1.matches(pg) || con2.matches(pg);
  }
}

trait ComposableCondition[T<:Execution] extends Condition[T] {
  def and(others: Condition[T]*): ComposableCondition[T] = {
    new ComposableCondition[T]() {
      override def matches(pg: T): Boolean = {
        (this +: others).reduce((x, y) => new AndCondition(x, y)).matches(pg);
      }
    }
  }

  def or(others: Condition[T]*): ComposableCondition[T] = {
    new ComposableCondition[T]() {
      override def matches(pg: T): Boolean = {
        (this +: others).reduce((x, y) => new OrCondition(x, y)).matches(pg);
      }
    }
  }
}

object Condition {

  def AlwaysTrue[T<:Execution]() = new Condition[T]() {
    def matches(pg: T): Boolean = true;
  }

  def after[T<:Execution](processName: String, otherProcessNames: String*) = new ComposableCondition[T] {
    def matches(pg: T): Boolean = {
      val processNames = processName +: otherProcessNames;
      return processNames.map(pg.isEntryCompleted(_))
        .filter(_ == true).length == processNames.length;
    }
  }

  def after[T<:Execution](when: Date) = new ComposableCondition[T] {
    def matches(pg: T): Boolean = {
      return new Date(System.currentTimeMillis()).after(when);
    }
  }
}

