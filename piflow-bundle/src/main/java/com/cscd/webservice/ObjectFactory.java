
package com.cscd.webservice;

import javax.xml.bind.JAXBElement;
import javax.xml.bind.annotation.XmlElementDecl;
import javax.xml.bind.annotation.XmlRegistry;
import javax.xml.namespace.QName;


/**
 * This object contains factory methods for each 
 * Java content interface and Java element interface 
 * generated in the com.cscd.webservice package. 
 * <p>An ObjectFactory allows you to programatically 
 * construct new instances of the Java representation 
 * for XML content. The Java representation of XML 
 * content can consist of schema derived interfaces 
 * and classes representing the binding of schema 
 * type definitions, element declarations and model 
 * groups.  Factory methods for each of these are 
 * provided in this class.
 * 
 */
@XmlRegistry
public class ObjectFactory {

    private final static QName _SearchByExprCode_QNAME = new QName("http://webservice.cscd.com", "code");
    private final static QName _SearchByExprExpr_QNAME = new QName("http://webservice.cscd.com", "expr");
    private final static QName _SearchByExprResponseReturn_QNAME = new QName("http://webservice.cscd.com", "return");
    private final static QName _CscdServiceExceptionCscdServiceException_QNAME = new QName("http://webservice.cscd.com", "CscdServiceException");
    private final static QName _GetArticlesCscdIds_QNAME = new QName("http://webservice.cscd.com", "cscdIds");
    private final static QName _GetCitedInfoCscdId_QNAME = new QName("http://webservice.cscd.com", "cscdId");
    private final static QName _SearchArticlesAuthor_QNAME = new QName("http://webservice.cscd.com", "author");
    private final static QName _SearchArticlesInstitute_QNAME = new QName("http://webservice.cscd.com", "institute");
    private final static QName _SearchArticlesTitle_QNAME = new QName("http://webservice.cscd.com", "title");
    private final static QName _SearchArticlesOrcId_QNAME = new QName("http://webservice.cscd.com", "orcId");
    private final static QName _GetCodeUser_QNAME = new QName("http://webservice.cscd.com", "user");
    private final static QName _GetCodePasswd_QNAME = new QName("http://webservice.cscd.com", "passwd");
    private final static QName _ExceptionMessage_QNAME = new QName("http://webservice.cscd.com", "Message");

    /**
     * Create a new ObjectFactory that can be used to create new instances of schema derived classes for package: com.cscd.webservice
     * 
     */
    public ObjectFactory() {
    }

    /**
     * Create an instance of {@link SearchByExpr }
     * 
     */
    public SearchByExpr createSearchByExpr() {
        return new SearchByExpr();
    }

    /**
     * Create an instance of {@link SearchByExprResponse }
     * 
     */
    public SearchByExprResponse createSearchByExprResponse() {
        return new SearchByExprResponse();
    }

    /**
     * Create an instance of {@link SearchByExprRange }
     * 
     */
    public SearchByExprRange createSearchByExprRange() {
        return new SearchByExprRange();
    }

    /**
     * Create an instance of {@link SearchByExprRangeResponse }
     * 
     */
    public SearchByExprRangeResponse createSearchByExprRangeResponse() {
        return new SearchByExprRangeResponse();
    }

    /**
     * Create an instance of {@link ReleaseCode }
     * 
     */
    public ReleaseCode createReleaseCode() {
        return new ReleaseCode();
    }

    /**
     * Create an instance of {@link CscdServiceException }
     * 
     */
    public CscdServiceException createCscdServiceException() {
        return new CscdServiceException();
    }

    /**
     * Create an instance of {@link Exception }
     * 
     */
    public Exception createException() {
        return new Exception();
    }

    /**
     * Create an instance of {@link GetArticles }
     * 
     */
    public GetArticles createGetArticles() {
        return new GetArticles();
    }

    /**
     * Create an instance of {@link GetArticlesResponse }
     * 
     */
    public GetArticlesResponse createGetArticlesResponse() {
        return new GetArticlesResponse();
    }

    /**
     * Create an instance of {@link GetCitedInfo }
     * 
     */
    public GetCitedInfo createGetCitedInfo() {
        return new GetCitedInfo();
    }

    /**
     * Create an instance of {@link GetCitedInfoResponse }
     * 
     */
    public GetCitedInfoResponse createGetCitedInfoResponse() {
        return new GetCitedInfoResponse();
    }

    /**
     * Create an instance of {@link SearchArticles }
     * 
     */
    public SearchArticles createSearchArticles() {
        return new SearchArticles();
    }

    /**
     * Create an instance of {@link SearchArticlesResponse }
     * 
     */
    public SearchArticlesResponse createSearchArticlesResponse() {
        return new SearchArticlesResponse();
    }

    /**
     * Create an instance of {@link GetCode }
     * 
     */
    public GetCode createGetCode() {
        return new GetCode();
    }

    /**
     * Create an instance of {@link GetCodeResponse }
     * 
     */
    public GetCodeResponse createGetCodeResponse() {
        return new GetCodeResponse();
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "code", scope = SearchByExpr.class)
    public JAXBElement<String> createSearchByExprCode(String value) {
        return new JAXBElement<String>(_SearchByExprCode_QNAME, String.class, SearchByExpr.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "expr", scope = SearchByExpr.class)
    public JAXBElement<String> createSearchByExprExpr(String value) {
        return new JAXBElement<String>(_SearchByExprExpr_QNAME, String.class, SearchByExpr.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "return", scope = SearchByExprResponse.class)
    public JAXBElement<String> createSearchByExprResponseReturn(String value) {
        return new JAXBElement<String>(_SearchByExprResponseReturn_QNAME, String.class, SearchByExprResponse.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "code", scope = SearchByExprRange.class)
    public JAXBElement<String> createSearchByExprRangeCode(String value) {
        return new JAXBElement<String>(_SearchByExprCode_QNAME, String.class, SearchByExprRange.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "expr", scope = SearchByExprRange.class)
    public JAXBElement<String> createSearchByExprRangeExpr(String value) {
        return new JAXBElement<String>(_SearchByExprExpr_QNAME, String.class, SearchByExprRange.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "return", scope = SearchByExprRangeResponse.class)
    public JAXBElement<String> createSearchByExprRangeResponseReturn(String value) {
        return new JAXBElement<String>(_SearchByExprResponseReturn_QNAME, String.class, SearchByExprRangeResponse.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "code", scope = ReleaseCode.class)
    public JAXBElement<String> createReleaseCodeCode(String value) {
        return new JAXBElement<String>(_SearchByExprCode_QNAME, String.class, ReleaseCode.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link Exception }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "CscdServiceException", scope = CscdServiceException.class)
    public JAXBElement<Exception> createCscdServiceExceptionCscdServiceException(Exception value) {
        return new JAXBElement<Exception>(_CscdServiceExceptionCscdServiceException_QNAME, Exception.class, CscdServiceException.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "code", scope = GetArticles.class)
    public JAXBElement<String> createGetArticlesCode(String value) {
        return new JAXBElement<String>(_SearchByExprCode_QNAME, String.class, GetArticles.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "cscdIds", scope = GetArticles.class)
    public JAXBElement<String> createGetArticlesCscdIds(String value) {
        return new JAXBElement<String>(_GetArticlesCscdIds_QNAME, String.class, GetArticles.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "return", scope = GetArticlesResponse.class)
    public JAXBElement<String> createGetArticlesResponseReturn(String value) {
        return new JAXBElement<String>(_SearchByExprResponseReturn_QNAME, String.class, GetArticlesResponse.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "code", scope = GetCitedInfo.class)
    public JAXBElement<String> createGetCitedInfoCode(String value) {
        return new JAXBElement<String>(_SearchByExprCode_QNAME, String.class, GetCitedInfo.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "cscdId", scope = GetCitedInfo.class)
    public JAXBElement<String> createGetCitedInfoCscdId(String value) {
        return new JAXBElement<String>(_GetCitedInfoCscdId_QNAME, String.class, GetCitedInfo.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "return", scope = GetCitedInfoResponse.class)
    public JAXBElement<String> createGetCitedInfoResponseReturn(String value) {
        return new JAXBElement<String>(_SearchByExprResponseReturn_QNAME, String.class, GetCitedInfoResponse.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "code", scope = SearchArticles.class)
    public JAXBElement<String> createSearchArticlesCode(String value) {
        return new JAXBElement<String>(_SearchByExprCode_QNAME, String.class, SearchArticles.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "author", scope = SearchArticles.class)
    public JAXBElement<String> createSearchArticlesAuthor(String value) {
        return new JAXBElement<String>(_SearchArticlesAuthor_QNAME, String.class, SearchArticles.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "institute", scope = SearchArticles.class)
    public JAXBElement<String> createSearchArticlesInstitute(String value) {
        return new JAXBElement<String>(_SearchArticlesInstitute_QNAME, String.class, SearchArticles.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "title", scope = SearchArticles.class)
    public JAXBElement<String> createSearchArticlesTitle(String value) {
        return new JAXBElement<String>(_SearchArticlesTitle_QNAME, String.class, SearchArticles.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "orcId", scope = SearchArticles.class)
    public JAXBElement<String> createSearchArticlesOrcId(String value) {
        return new JAXBElement<String>(_SearchArticlesOrcId_QNAME, String.class, SearchArticles.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "return", scope = SearchArticlesResponse.class)
    public JAXBElement<String> createSearchArticlesResponseReturn(String value) {
        return new JAXBElement<String>(_SearchByExprResponseReturn_QNAME, String.class, SearchArticlesResponse.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "user", scope = GetCode.class)
    public JAXBElement<String> createGetCodeUser(String value) {
        return new JAXBElement<String>(_GetCodeUser_QNAME, String.class, GetCode.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "passwd", scope = GetCode.class)
    public JAXBElement<String> createGetCodePasswd(String value) {
        return new JAXBElement<String>(_GetCodePasswd_QNAME, String.class, GetCode.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "return", scope = GetCodeResponse.class)
    public JAXBElement<String> createGetCodeResponseReturn(String value) {
        return new JAXBElement<String>(_SearchByExprResponseReturn_QNAME, String.class, GetCodeResponse.class, value);
    }

    /**
     * Create an instance of {@link JAXBElement }{@code <}{@link String }{@code >}}
     * 
     */
    @XmlElementDecl(namespace = "http://webservice.cscd.com", name = "Message", scope = Exception.class)
    public JAXBElement<String> createExceptionMessage(String value) {
        return new JAXBElement<String>(_ExceptionMessage_QNAME, String.class, Exception.class, value);
    }

}
