docker build -f piflow_v0.9_dockerfile -t ubuntu/piflow:v0.9.1 .
docker run -h master -itd --env HOST_IP=10.0.90.155 --name piflow-v0.9.1 [ImageId] 
