package cn.piflow.bundle.util;

import org.apache.commons.net.ftp.FTP;
import org.apache.commons.net.ftp.FTPClient;
import org.apache.commons.net.ftp.FTPFile;
import org.apache.commons.net.ftp.FTPReply;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FSDataInputStream;
import org.apache.hadoop.fs.FSDataOutputStream;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.log4j.BasicConfigurator;
import org.apache.log4j.Logger;

import java.io.*;
import java.nio.charset.StandardCharsets;

public class FtpDownAndUploadUtil {
    Logger log = Logger.getRootLogger();
    String hdfsUrl ;
    FileSystem fs;

    /**
     * 上传文件到 Ftp 服务器
     * @param ftpClient ftp连接客户端
     * @param
     */
    public void uploadFtp(FTPClient ftpClient,String ftpPath, String hdfsSourcePath) throws Exception {
        String relativePath = fs.getFileStatus(new Path(hdfsSourcePath)).getPath().getName();

        if (ftpClient == null || hdfsSourcePath == null) {
            return;
        }
        // 中文目录处理存在问题， 转化为ftp能够识别中文的字符集
        String remotePath;
        try {
            remotePath = ftpPath+"/"+new String(relativePath.getBytes(StandardCharsets.UTF_8), FTP.DEFAULT_CONTROL_ENCODING);
        } catch (UnsupportedEncodingException e) {
            remotePath = ftpPath+"/"+relativePath;
        }
//        判断 FTP上是否存在同名文件
        if(ftpClient.listFiles(remotePath).length>0){
            log.warn("Ftp 服务器上存在同名文件："+remotePath);
            return;
        }
        log.info(hdfsSourcePath + "----------"+ remotePath);

//        判断 FTP上文件夹是否存在 ，不存在则创建
        mkdirsFtpPath(ftpClient,ftpPath);

        try {
            FSDataInputStream inputStream = fs.open(new Path(hdfsSourcePath));
            OutputStream outputStream = ftpClient.storeFileStream(remotePath);
            byte[] buffer = new byte[2048];
            int length;
            while ((length = inputStream.read(buffer)) != -1) {
                outputStream.write(buffer, 0, length);
                outputStream.flush();
            }
            outputStream.close();
            inputStream.close();
        } catch (Exception e) {
            log.error("文件上传异常" + e);
            return;
        }

        // 关闭流之后必须执行，否则下一个文件导致流为空
        boolean complete = ftpClient.completePendingCommand();
        if (complete) {
            log.info(remotePath+ "文件上传完成");
        } else {
            log.error(remotePath+"文件{}上传失败");
        }

    }


    /**
     * 获取一个ftp连接
     * @param host ip地址
     * @param port 端口
     * @param username 用户名
     * @param password 密码
     * @return 返回 ftp连接对象
     * @throws Exception 连接ftp时发生的各种异常
     */
    public  FTPClient getFtpClient(String host, Integer port, String username, String password,String defaultFSUrl) throws Exception {
        BasicConfigurator.configure();
        hdfsUrl = defaultFSUrl;
        //1 创建连接
        Configuration conf = new Configuration();
        //2 连接端口
        conf.set("fs.defaultFS", hdfsUrl);
        //3 获取连接对象
        fs = FileSystem.get(conf);

        FTPClient ftpClient = new FTPClient();
        // 连接服务器
        ftpClient.connect(host, port);

        int reply = ftpClient.getReplyCode();
        if (!FTPReply.isPositiveCompletion(reply)) {
            log.error("无法连接至ftp服务器， host:{"+ host +"}, port:{"+ port +"}"  );
            ftpClient.disconnect();
            return null;
        }
        // 登入服务器
        boolean login = ftpClient.login(username, password);
        if (!login) {
            log.error("登录失败， 用户名或密码错误");
            ftpClient.logout();
            ftpClient.disconnect();
            return null;
        }

        // 连接并且成功登陆ftp服务器
        log.info("login success ftp server, host:{"+ host +"}, port:{"+ port +"}, user:{"+ username +"}" );
        // 设置通道字符集， 要与服务端设置一致
        ftpClient.setControlEncoding("UTF-8");
        // 设置文件传输编码类型， 字节传输：BINARY_FILE_TYPE, 文本传输：ASCII_FILE_TYPE， 建议使用BINARY_FILE_TYPE进行文件传输
        ftpClient.setFileType(FTP.BINARY_FILE_TYPE);
        // 主动模式: enterLocalActiveMode(),被动模式: enterLocalPassiveMode(),一般选择被动模式
        ftpClient.enterLocalPassiveMode();

        return ftpClient;
    }

    /**
     * 在FTP服务器上级联创建文件夹
     * @param ftpClient
     * @param ftpPath
     */
    public void mkdirsFtpPath(FTPClient ftpClient,String ftpPath) {
        try {
            String directory = ftpPath.endsWith("/") ? ftpPath : ftpPath + "/";
            int start = 0;
            int end;
            if (directory.startsWith("/")) {
                start = 1;
            }
            end = directory.indexOf("/", start);
            while (end > start){
                String subDirectory = new String(ftpPath.substring(0, end).getBytes("GBK"), StandardCharsets.ISO_8859_1);
                if(!ftpClient.changeWorkingDirectory(subDirectory)){
                    ftpClient.makeDirectory(subDirectory);
                    log.info("FTP服务器文件夹"+subDirectory+"不存在，已经创建");
                }
                start= end+1;
                end = directory.indexOf("/", start);
            }

        } catch (Exception exception) {
            exception.printStackTrace();
        }
    }

    /**
     * 断开ftp连接
     * @param ftpClient
     */
    public  void disConnect(FTPClient ftpClient) {
        if (ftpClient == null) {
            return;
        }
        try {
            log.info("断开ftp连接, host:{" + ftpClient.getPassiveHost() + "}, port:{" + ftpClient.getPassivePort() + "}");
            ftpClient.logout();
            ftpClient.disconnect();
        } catch (IOException e) {
            e.printStackTrace();
            log.error("ftp连接断开异常， 请检查");
        }
    }


    /**
     * 从 FTP上下载数据到 HDFS
     * @param ftpClient
     * @param ftpPath
     * @param hdfsFolderPath
     * @throws Exception
     */
    public void downloadFromFtpAndUploadToHdfs(FTPClient ftpClient, String ftpPath, String hdfsFolderPath) throws Exception {
        if (ftpClient == null || ftpPath == null || hdfsFolderPath == null) {
            return;
        }
        if(ftpClient.changeWorkingDirectory(ftpPath)) {
            downloadFolder(ftpClient,ftpPath,hdfsFolderPath);
        } else {
            downloadFile(ftpClient,ftpPath,hdfsFolderPath);
        }
    }

    /**
     * 文件夹下载渠道
     * @param ftpClient
     * @param ftpPath
     * @param hdfsFolderPath
     * @throws Exception
     */
    public void downloadFolder(FTPClient ftpClient, String ftpPath, String hdfsFolderPath) throws Exception {
        FTPFile[] ftpFiles = ftpClient.listFiles(ftpPath);
        for(FTPFile ftpFile:ftpFiles){
            String fileName = ftpFile.getName();
            if(ftpFile.isDirectory()){
                String fullFtpPath = ftpPath.endsWith("/") ? ftpPath+fileName : ftpPath+"/"+fileName;
                String fullHdfsPath = hdfsFolderPath+File.separator + fileName;
                downloadFolder(ftpClient,fullFtpPath,fullHdfsPath);
            } else if(ftpFile.isFile()){
                String  hdfsFilePath = hdfsFolderPath + File.separator + fileName;
                downloadFile(ftpClient,ftpPath+"/"+fileName,hdfsFilePath);
            }
        }
    }

    /**
     * 文件下载渠道
     * @param ftpClient
     * @param ftpPath
     * @param localFolderPath
     * @throws Exception
     */
    public  void downloadFile(FTPClient ftpClient, String ftpPath, String localFolderPath) throws Exception {
        log.info("需要下载的文件为"+ftpPath+"---下载路径为"+localFolderPath);
        downloadFromFtpUtil(ftpClient,ftpPath,localFolderPath);
    }

    /**
     * 从 FTP上下载数据到 HDFS 工具类
     * @param ftpClient
     * @param path
     * @param hdfsPath
     * @throws Exception
     */
    public void downloadFromFtpUtil(FTPClient ftpClient, String path,String hdfsPath) throws Exception {

        boolean exists = fs.exists(new Path(hdfsPath));
        if(exists){
            log.info("同名文件已经存在---->>>"+hdfsPath);
            return;
        }
        // 中文目录处理存在问题， 转化为ftp能够识别中文的字符集
        String remotePath;
        try {
            remotePath = new String(path.getBytes(StandardCharsets.UTF_8), FTP.DEFAULT_CONTROL_ENCODING);
        } catch (UnsupportedEncodingException e) {
            remotePath = path;
        }

        InputStream inputStream = ftpClient.retrieveFileStream(remotePath);
        if (inputStream == null) {
            log.error(path + "在ftp服务器中不存在，请检查");
            return;
        }
        BufferedInputStream bufferedInputStream = new BufferedInputStream(inputStream);
        FSDataOutputStream bufferedOutputStream = fs.create(new Path(hdfsPath));//在hdfs上创建路径
        try {
            byte[] buffer = new byte[2048];
            int i;
            while ((i = bufferedInputStream.read(buffer)) != -1) {
                bufferedOutputStream.write(buffer, 0, i);
                bufferedOutputStream.flush();
            }
        } catch (Exception e) {
            log.error("文件下载异常" + e);
            log.error(path + "下载异常，请检查");
        }

        inputStream.close();
        bufferedOutputStream.close();
        bufferedInputStream.close();
        bufferedOutputStream.close();

        // 关闭流之后必须执行，否则下一个文件导致流为空
        boolean complete = ftpClient.completePendingCommand();
        if (complete) {
            log.info(remotePath + "文件下载完成");
        } else {
            log.error(remotePath + "文件下载失败");
        }
    }



//    /**
//     * 迭代遍历 HDFS 文件
//     * @param hdfsPath
//     * @throws Exception
//     */
//    List<String> list = new ArrayList<>();
//    public void iterationHdfsDir(String hdfsPath) throws Exception {
//        Path path = new Path(hdfsPath);
//        boolean exists = fs.exists(path);
//        if(exists){
//            FileStatus[] listStatus  = fs.listStatus(path);
//            for (FileStatus fileStatus : listStatus) {
//                String fsPath = fileStatus.getPath().toString();
//                if(fileStatus.isDirectory()){
//                    iterationHdfsDir(fsPath);
//                }else {
//                    String hdfsSourcePath = fsPath.replace(hdfsUrl,"");
//                    list.add(hdfsSourcePath);
//                }
//            }
//        } else {
//            log.info("输入路径不存在："+ hdfsPath);
//        }
//    }








}
