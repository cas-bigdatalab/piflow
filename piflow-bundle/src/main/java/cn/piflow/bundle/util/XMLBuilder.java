package cn.piflow.bundle.util;

import org.w3c.dom.Document;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.xpath.*;
import java.io.Serializable;
import java.io.StringReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Created by SongDz on 2019/7/24.
 *
 * @author SongDz
 */
public class XMLBuilder implements Serializable {

    public static Document buildDocument(String xmlString){
        Document document = null;

        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        DocumentBuilder builder;
        try
        {
            builder = factory.newDocumentBuilder();
            document = builder.parse( new InputSource( new StringReader( xmlString ) ) );
        } catch (Exception e) {
            e.printStackTrace();
        }
        return document;
    }

    public static List<String> getNodeByXPath(Document document, String xpath_expression){
        List<String> nodeTextList = new ArrayList<String>();
        NodeList nodeList;

        XPathFactory xPathfactory = XPathFactory.newInstance();
        XPath xpath = xPathfactory.newXPath();
        XPathExpression expr = null;
        try {
            expr = xpath.compile(xpath_expression);
            nodeList = (NodeList)expr.evaluate(document, XPathConstants.NODESET);

            for (int i = 0; i < nodeList.getLength(); i++) {
                nodeTextList.add(nodeList.item(i).getTextContent());
                //System.out.print(nodeList.item(i).getTextContent() + " ");
            }
        } catch (XPathExpressionException e) {
            e.printStackTrace();
        }

        return nodeTextList;
    }

    public static Map<String,String> getNodeByXPath(Document document, Map<String, String> schema_xpathExpressions){
        Map<String,String> nodeText = new HashMap<String,String>(schema_xpathExpressions.size());
        NodeList nodeList;
        List<String> contents;
        XPathFactory xPathfactory = XPathFactory.newInstance();
        XPath xpath = xPathfactory.newXPath();
        for (Map.Entry<String,String> schema_xpathExpression : schema_xpathExpressions.entrySet()) {
            try {
                nodeList = (NodeList)xpath.evaluate(schema_xpathExpression.getValue(), document, XPathConstants.NODESET);
                contents = new ArrayList<String>(nodeList.getLength());
                for (int i = 0; i < nodeList.getLength(); i++) {
                    contents.add(nodeList.item(i).getTextContent());
                }
                nodeText.put(schema_xpathExpression.getKey(), String.join("#",contents));

            } catch (XPathExpressionException e) {
                e.printStackTrace();
            }
        }

        return nodeText;
    }

    public static void main(String [] args){

        String str1 = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" +
                "<articles>\n" +
                "  <article>\n" +
                "    <cscd_id>3938784</cscd_id>\n" +
                "    <title>网构软件模型中的抽象状态机设计</title>\n" +
                "    <page_string>923-929</page_string>\n" +
                "    <authorlist>\n" +
                "      <author>\n" +
                "        <author_name>张引</author_name>\n" +
                "        <institute>浙江大学</institute>\n" +
                "      </author>\n" +
                "      <author>\n" +
                "        <author_name>何浩</author_name>\n" +
                "        <institute>浙江大学</institute>\n" +
                "      </author>\n" +
                "      <author>\n" +
                "        <author_name>赵丽娜</author_name>\n" +
                "        <institute>浙江大学</institute>\n" +
                "      </author>\n" +
                "      <author>\n" +
                "        <author_name>张三元</author_name>\n" +
                "        <institute>浙江大学</institute>\n" +
                "      </author>\n" +
                "    </authorlist>\n" +
                "    <journal>\n" +
                "      <issn>1008-973X</issn>\n" +
                "      <journal_name>浙江大学学报. 工学版</journal_name>\n" +
                "    </journal>\n" +
                "    <issue>\n" +
                "      <year>2010</year>\n" +
                "      <volume>44</volume>\n" +
                "      <issue>5</issue>\n" +
                "    </issue>\n" +
                "    <cited_num>0</cited_num>\n" +
                "    <doi />\n" +
                "    <abstract>为了更好地支持和实现网构软件的自动化,提出在网构软件模型中使用抽象状态机(ASM).在Internet的计算环境下,采用peer-to-peer(P2P)拓扑结构作为网构软件模型的支撑网络环境,使用ASM的方法从较高的抽象层次(概念层)描述整个系统的行为与状态变迁,使系统特征易于把握.分析网构软件模型中ASM的架构,详细阐述ASM的运行规则,说明了系统状态特征的变迁情况.根据ASM方法所涉及到的各种状态、事件、方法、数据、规则等进行相应的设计和实现,已经初步形成一个网构软件设计和运行的支撑平台,证明了ASM在网构软件模型中的可行性以及ASM能够实现网构软件的自动化特性</abstract>\n" +
                "    <keywords>网构软件;;抽象状态机(ASM);;peer-to-peer (P2P);;Agent</keywords>\n" +
                "    <citation>张引,何浩,赵丽娜,张三元. 浙江大学学报. 工学版[J],2010,44(5),923-929</citation>\n" +
                "    <article_url>http://sciencechina.cn/gw.jsp?action=detail.jsp&amp;internal_id=3938784&amp;detailType=1</article_url>\n" +
                "    <citing_articles_url>http://sciencechina.cn/gw.jsp?action=cited_outline.jsp&amp;type=1&amp;id=3938784&amp;internal_id=3938784</citing_articles_url>\n" +
                "  </article>\n" +
                "</articles>\n";

        String str = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" +
                "<result total=\"5359\">\n" +
                "  <cscd_id>6009525</cscd_id>\n" +
                "  <cscd_id>6009515</cscd_id>\n" +
                "  <cscd_id>6009447</cscd_id>\n" +
                "  <cscd_id>6008062</cscd_id>\n" +
                "  <cscd_id>6006978</cscd_id>\n" +
                "  <cscd_id>6006896</cscd_id>\n" +
                "  <cscd_id>6006891</cscd_id>\n" +
                "  <cscd_id>6006835</cscd_id>\n" +
                "  <cscd_id>6006831</cscd_id>\n" +
                "  <cscd_id>6006618</cscd_id>\n" +
                "  <cscd_id>6004469</cscd_id>\n" +
                "  <cscd_id>6003925</cscd_id>\n" +
                "  <cscd_id>6003898</cscd_id>\n" +
                "  <cscd_id>6002690</cscd_id>\n" +
                "  <cscd_id>6001793</cscd_id>\n" +
                "  <cscd_id>6000786</cscd_id>\n" +
                "  <cscd_id>5999905</cscd_id>\n" +
                "  <cscd_id>5999297</cscd_id>\n" +
                "  <cscd_id>5999257</cscd_id>\n" +
                "  <cscd_id>5999199</cscd_id>\n" +
                "  <cscd_id>5999017</cscd_id>\n" +
                "  <cscd_id>5998795</cscd_id>\n" +
                "  <cscd_id>5998053</cscd_id>\n" +
                "  <cscd_id>5997509</cscd_id>\n" +
                "  <cscd_id>5997155</cscd_id>\n" +
                "  <cscd_id>5996401</cscd_id>\n" +
                "  <cscd_id>5996199</cscd_id>\n" +
                "  <cscd_id>5995525</cscd_id>\n" +
                "  <cscd_id>5994528</cscd_id>\n" +
                "  <cscd_id>5994122</cscd_id>\n" +
                "  <cscd_id>5992820</cscd_id>\n" +
                "  <cscd_id>5992701</cscd_id>\n" +
                "  <cscd_id>5992182</cscd_id>\n" +
                "  <cscd_id>5990076</cscd_id>\n" +
                "  <cscd_id>5989741</cscd_id>\n" +
                "  <cscd_id>5989271</cscd_id>\n" +
                "  <cscd_id>5988827</cscd_id>\n" +
                "  <cscd_id>5984424</cscd_id>\n" +
                "  <cscd_id>5983618</cscd_id>\n" +
                "  <cscd_id>5983120</cscd_id>\n" +
                "  <cscd_id>5982056</cscd_id>\n" +
                "  <cscd_id>5981679</cscd_id>\n" +
                "  <cscd_id>5981643</cscd_id>\n" +
                "  <cscd_id>5981268</cscd_id>\n" +
                "  <cscd_id>5980476</cscd_id>\n" +
                "  <cscd_id>5979180</cscd_id>\n" +
                "  <cscd_id>5979168</cscd_id>\n" +
                "  <cscd_id>5979162</cscd_id>\n" +
                "  <cscd_id>5979150</cscd_id>\n" +
                "  <cscd_id>5979015</cscd_id>\n" +
                "  <cscd_id>5977883</cscd_id>\n" +
                "  <cscd_id>5977364</cscd_id>\n" +
                "  <cscd_id>5977048</cscd_id>\n" +
                "  <cscd_id>5976870</cscd_id>\n" +
                "  <cscd_id>5976722</cscd_id>\n" +
                "  <cscd_id>5975958</cscd_id>\n" +
                "  <cscd_id>5975740</cscd_id>\n" +
                "  <cscd_id>5973779</cscd_id>\n" +
                "  <cscd_id>5973383</cscd_id>\n" +
                "  <cscd_id>5973356</cscd_id>\n" +
                "  <cscd_id>5973327</cscd_id>\n" +
                "  <cscd_id>5973101</cscd_id>\n" +
                "  <cscd_id>5973079</cscd_id>\n" +
                "  <cscd_id>5972699</cscd_id>\n" +
                "  <cscd_id>5972215</cscd_id>\n" +
                "  <cscd_id>5971808</cscd_id>\n" +
                "  <cscd_id>5971037</cscd_id>\n" +
                "  <cscd_id>5970166</cscd_id>\n" +
                "  <cscd_id>5968952</cscd_id>\n" +
                "  <cscd_id>5967425</cscd_id>\n" +
                "  <cscd_id>5967420</cscd_id>\n" +
                "  <cscd_id>5967411</cscd_id>\n" +
                "  <cscd_id>5967201</cscd_id>\n" +
                "  <cscd_id>5965348</cscd_id>\n" +
                "  <cscd_id>5964027</cscd_id>\n" +
                "  <cscd_id>5963537</cscd_id>\n" +
                "  <cscd_id>5962965</cscd_id>\n" +
                "  <cscd_id>5962840</cscd_id>\n" +
                "  <cscd_id>5962634</cscd_id>\n" +
                "  <cscd_id>5961867</cscd_id>\n" +
                "  <cscd_id>5961551</cscd_id>\n" +
                "  <cscd_id>5960992</cscd_id>\n" +
                "  <cscd_id>5960943</cscd_id>\n" +
                "  <cscd_id>5959525</cscd_id>\n" +
                "  <cscd_id>5959459</cscd_id>\n" +
                "  <cscd_id>5959369</cscd_id>\n" +
                "  <cscd_id>5958820</cscd_id>\n" +
                "  <cscd_id>119818</cscd_id>\n" +
                "</result>\n" +
                "\n";
        Document document = XMLBuilder.buildDocument(str);
        //List resultList = (List) result;
        List<String> cscdIdsList = XMLBuilder.getNodeByXPath(document,"/result/cscd_id");
        //cscdIdsList.forEach(System.out::println);

        document = XMLBuilder.buildDocument(str1);
        List<String> institutes = XMLBuilder.getNodeByXPath(document,"/articles/article/authorlist/author/institute");
    }
}