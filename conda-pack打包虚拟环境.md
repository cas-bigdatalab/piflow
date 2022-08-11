我使用的是conda这个包管理工具来对anaconda所安装的python虚拟环境进行打包，需要注意的是打包的是anaconda安装的虚拟环境而不是本地环境。

优势：可以打包虚拟环境中包括二进制文件等整个环境包括pip安装的python库

劣势：conda打包的虚拟环境只能使用于同一个操作系统下，测试了ubuntu和centos可以通用

（操作系统ubuntu20.04）

1.安装Anaconda（使用脚本安装）安装教程链接：https://www.myfreax.com/how-to-install-anaconda-on-ubuntu-20-04/ ,或者自行搜索安装方法。

大致过程如下，下载脚本，执行脚本。

```bash
wget -P /tmp https://repo.anaconda.com/archive/Anaconda3-2020.02-Linux-x86_64.sh
```

安装anconda后建议更新下版本

2.安装conda pack工具，这里推荐使用pip安装。

```bash
pip install conda-pack
```

3.创建python虚拟环境

```
conda create -n vir-name python=x.x.  #vir-name换成你的虚拟环境名字
```

4.激活虚拟环境

```
conda activate vir-name
```

5.使用pip安装对应的包

6.使用conda pack打包环境

```
conda pack -n my_env_name -o out_name.tar.gz
```

此处打包只能打包成tar.gz模式，打包成zip会有报错，想打包成zip模式解决办法就是先打包成tar.gz之后解压再重新打包成zip

7.激活虚拟环境

将zip包从本地环境上传到服务器或者其他操作系统相同的环境后解压并进入其中的bin目录

使用`source activate`激活环境

8.退出虚拟环境

使用`source deactivate`退出虚拟环境