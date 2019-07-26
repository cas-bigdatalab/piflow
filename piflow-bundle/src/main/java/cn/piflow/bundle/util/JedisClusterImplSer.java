package cn.piflow.bundle.util;

import redis.clients.jedis.HostAndPort;
import redis.clients.jedis.JedisCluster;
import redis.clients.jedis.JedisPoolConfig;

import java.io.IOException;
import java.io.ObjectStreamException;
import java.io.Serializable;

public class JedisClusterImplSer implements Serializable {

    private static final long serialVersionUID = -51L;

    private static final int DEFAULT_TIMEOUT = 2000;
    private static final int DEFAULT_REDIRECTIONS = 5;
    private static final JedisPoolConfig DEFAULT_CONFIG = new JedisPoolConfig();

    private HostAndPort hostAndPort;
    private String password;
    transient private JedisCluster jedisCluster;

    /*public JedisClusterImplSer(HostAndPort hostAndPort) {
        this.hostAndPort = hostAndPort;
        this.jedisCluster = new JedisCluster(hostAndPort, 3000000);
    }*/

    public JedisClusterImplSer(HostAndPort hostAndPort, String password){
        this.hostAndPort = hostAndPort;
        this.password = password;
        this.jedisCluster = new JedisCluster(hostAndPort,DEFAULT_TIMEOUT,DEFAULT_TIMEOUT,DEFAULT_REDIRECTIONS,this.password,DEFAULT_CONFIG);
    }

    private void writeObject(java.io.ObjectOutputStream out) throws IOException {
        out.defaultWriteObject();
    }

    private void readObject(java.io.ObjectInputStream in) throws IOException, ClassNotFoundException{
        in.defaultReadObject();
        //setJedisCluster(new JedisCluster(hostAndPort));
        setJedisCluster(new JedisCluster(hostAndPort,DEFAULT_TIMEOUT,DEFAULT_TIMEOUT,DEFAULT_REDIRECTIONS,this.password,DEFAULT_CONFIG));
    }

    private void readObjectNoData() throws ObjectStreamException {

    }

    public JedisCluster getJedisCluster() {
        if (jedisCluster == null) this.jedisCluster = new JedisCluster(hostAndPort,DEFAULT_TIMEOUT,DEFAULT_TIMEOUT,DEFAULT_REDIRECTIONS,this.password,DEFAULT_CONFIG);
        return jedisCluster;
    }

    private void setJedisCluster(JedisCluster jedisCluster) {
        this.jedisCluster = jedisCluster;
    }

    public void close() {
        try {
            this.jedisCluster.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
