package cn.piflow.util

import java.text.SimpleDateFormat
import java.util.Date

import org.apache.commons.lang.StringUtils

object FormatUtils {
	def format(x: Any, nullString: String = "(null)"): String = {
		x match {
			case null => nullString
			case None => nullString
			case Some(m) => format(m, nullString);
			case date: Date => new SimpleDateFormat("yyyy-MM-dd HH:mm:SS").format(date)
			case _ => x.toString
		}
	}

	def printTable(columns: Seq[String], data: Seq[Seq[Any]], nullString: String = "(null)") = {
		val formatedColumns: Seq[String] = columns.map(format(_, nullString));
		val formatedData: Seq[Seq[String]] = data.map(_.map(format(_, nullString)));

		val sb = new StringBuilder
		val numCols = formatedColumns.length

		// Initialise the width of each column to a minimum value of '3'
		val colWidths = Array.fill(numCols)(3)

		// Compute the width of each column
		for (row ← formatedData :+ formatedColumns) {
			for ((cell, i) ← row.zipWithIndex) {
				colWidths(i) = math.max(colWidths(i), cell.length)
			}
		}

		// Create SeparateLine
		val sep: String = colWidths.map("-" * _).addString(sb, "+", "+", "+\n").toString()

		// column names
		formatedColumns.zipWithIndex.map {
			case (cell, i) ⇒
				StringUtils.rightPad(cell, colWidths(i))
		}.addString(sb, "|", "|", "|\n")

		sb.append(sep)

		// data
		formatedData.map {
			_.zipWithIndex.map {
				case (cell, i) ⇒
					StringUtils.rightPad(cell, colWidths(i))
			}.addString(sb, "|", "|", "|\n")
		}

		sb.append(sep);
		println(sb);
	}
}