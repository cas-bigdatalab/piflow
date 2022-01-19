package com.piflow.sql.visitor;


import com.piflow.sql.out.SqlBaseLexer;
import com.piflow.sql.out.SqlBaseParser;
import org.antlr.v4.runtime.ANTLRInputStream;
import org.antlr.v4.runtime.CommonTokenStream;

public class ParserDriver {
    public static void main(String[] args) {
//        String query = "SELECT LastName,FirstName FROM Persons;";

       String  query = "SELECT Persons.LastName, Persons.FirstName, Orders.OrderNo\n" +
                "FROM Persons\n" +
                "INNER JOIN Orders\n" +
                "ON Persons.Id_P = Orders.Id_P\n" +
                "GROUP BY Persons.LastName";

        //String query = "SELECT * FROM Persons;";
        /*String query1 = "SELECT Students.id, Students.name\n" +
                "FROM Students\n" +
                "LEFT JOIN Scores\n" +
                "ON Students.id = Scores.id\n" +
                "GROUP BY Students.id";*/

        System.out.println(query);

        SqlBaseLexer lexer = new SqlBaseLexer(new ANTLRInputStream(query));
        SqlBaseParser parser = new SqlBaseParser(new CommonTokenStream(lexer));
        MyVisitor visitor = new MyVisitor();
        SqlBaseParser.SingleStatementContext bb = parser.singleStatement();
        String res = visitor.visitSingleStatement(bb);
        System.out.println("res="+res);
    }
}
