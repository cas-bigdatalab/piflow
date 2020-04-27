package cn.piflow.conf.util;

import java.io.IOException;
import java.net.JarURLConnection;
import java.net.URL;
import java.net.URLClassLoader;
import java.net.URLConnection;
import java.util.ArrayList;
import java.util.List;

public class PluginClassLoader extends URLClassLoader {

    private List<JarURLConnection> cachedJarFiles = new ArrayList<JarURLConnection>();

    public PluginClassLoader() {
        super(new URL[]{}, findParentClassLoader());
    }
    public void addURLFile(URL file){
        try{
            URLConnection uc = file.openConnection();
            if( uc instanceof  JarURLConnection){
                uc.setUseCaches(true);
                ((JarURLConnection)uc).getManifest();
                cachedJarFiles.add((JarURLConnection)uc);
            }
        } catch (IOException e) {
            System.out.println("Failed to cache plugin Jar file:" + file.toExternalForm());
        }
        addURL(file);
    }
    public void unloadJarFiles(){
        for(JarURLConnection url : cachedJarFiles){
            try{
                System.err.println("Unloading plugin JAR file " + url.getJarFile().getName());
                url.getJarFile().close();
            } catch (IOException e) {
                System.out.println("Failed to unload JAR file \n" + e);
            }
        }
    }

    private static ClassLoader findParentClassLoader(){
        ClassLoader parent = PluginManager.class.getClassLoader();
        if(parent == null){
            parent = PluginClassLoader.class.getClassLoader();
        }
        if(parent == null){
            parent = ClassLoader.getSystemClassLoader();
        }
        return parent;
    }
}
