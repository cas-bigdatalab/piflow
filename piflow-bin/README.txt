1.build piflow-server-0.9.jar, copy it to folder lib
  cp /yourPiflowPath/piflow-server/target/piflow-server-0.9.jar ./lib

2.start piflow server
  ./start.sh

3.please install piflow-web to configure flow in website.
    https://github.com/cas-bigdatalab/piflow-web

4.another way to use piflow: command line

  1)set PIFLOW_HOME
  vim /etc/profile
  	export PIFLOW_HOME=/yourPiflowPath/piflow-bin
	export PATH=$PATH:$PIFLOW_HOME/bin

  2)command example
    piflow flow start *.json
    piflow flow stop appID
    piflow flow info appID
    piflow flow log appID

    piflow flowGroup start *.json
    piflow flowGroup stop groupId
    piflow flowGroup info groupId

