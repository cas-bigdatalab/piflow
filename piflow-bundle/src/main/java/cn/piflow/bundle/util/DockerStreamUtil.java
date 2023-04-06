package cn.piflow.bundle.util;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.Charset;

public class DockerStreamUtil {

    public static void execRuntime(String cmd)  {
        Process process = null ;
        try {
            //execute
//            process = Runtime.getRuntime().exec(cmd);
            process = (new ProcessBuilder(new String[] {"/bin/sh","-c",cmd})).redirectErrorStream(true).start();

            //get process inputStream
            InputStream inputStream;
            InputStreamReader isr;
            BufferedReader br;
            String line=null;

//            if(exitVal == 0){
            inputStream = process.getInputStream();
//            } else {
//                inputStream = process.getErrorStream();
//            }
            //create a new inputStreamReader
            isr = new InputStreamReader(inputStream, Charset.forName("utf-8"));
            //create a new bufferedReader to read stream
            br = new BufferedReader(isr);
            while ((line=br.readLine())!= null){
                System.out.println(line);
                if(line.contains("# Fatal error,")){
                    throw new Exception("Error "+line);
                }
            }
            // get child process exitValue
            process.waitFor();
            int exitVal = process.exitValue();
            System.out.println(exitVal == 0 ? "execute success!" : "execute error!");
            if(exitVal != 0){
                System.out.println("execute error!-----"+exitVal);
                inputStream = process.getErrorStream();
                isr = new InputStreamReader(inputStream, Charset.forName("utf-8"));
                br = new BufferedReader(isr);
                while ((line=br.readLine())!= null){
                    System.out.println(line);
                    throw new Exception("Error "+line);
                }
            }

        }catch (Exception e){
            if (process != null) {
                // stop process
                process.destroy();
            }
            e.printStackTrace();
        }
    }

}

