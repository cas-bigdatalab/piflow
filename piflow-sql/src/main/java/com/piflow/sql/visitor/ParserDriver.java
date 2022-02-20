package com.piflow.sql.visitor;


import cn.piflow.conf.bean.FlowBean;
import com.piflow.sql.out.SqlBaseLexer;
import com.piflow.sql.out.SqlBaseParser;
import org.antlr.v4.runtime.ANTLRInputStream;
import org.antlr.v4.runtime.CommonTokenStream;

public class ParserDriver {
    public static void main(String[] args) {
//        String query = "SELECT LastName,FirstName FROM Persons;";

       String  query = "SELECT Id, Name, AVG(Score)\n" +
                "FROM Persons\n" +
                "INNER JOIN Scores\n" +
                "ON Persons.id = Scores.pId\n" +
                "GROUP BY Persons.id, Persons.Name";

        System.out.println(query);

        SqlBaseLexer lexer = new SqlBaseLexer(new ANTLRInputStream(query));
        SqlBaseParser parser = new SqlBaseParser(new CommonTokenStream(lexer));
        //MyVisitor visitor = new MyVisitor();
        FlowBeanVisitor visitor = new FlowBeanVisitor();
        SqlBaseParser.SingleStatementContext bb = parser.singleStatement();
        FlowBean res = visitor.visitSingleStatement(bb);
        String flowJson = res.toJson();
        System.out.println("res="+flowJson);
    }
}
