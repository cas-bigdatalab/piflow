1.build piflow-server-0.9.jar, copy it to folder --- lib

2.set PIFLOW_HOME
  vim /etc/profile
  	export PIFLOW_HOME=/**/.../piflow-bin
	export PATH=$PATH:$PIFLOW_HOME/bin

3.command example
  piflow flow start *.json
  piflow flow stop appID
  piflow flow info appID
  piflow flow log appID

  piflow flowGroup start *.json
  piflow flowGroup stop groupId 
  piflow flowGroup info groupId 

  piflow project start *.json
  piflow project stop projectId
  piflow project info projectId
