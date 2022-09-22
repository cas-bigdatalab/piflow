FROM maven:3-jdk-8 AS build
WORKDIR /app
COPY . /app
RUN mvn clean install -Dmaven.test.skip=true

FROM  openjdk:8-jre-alpine
WORKDIR /tmp
COPY --from=build /app/target/*.jar /tmp/h5.jar
EXPOSE 7786
ENTRYPOINT ["java","-jar","-Xms64m","-Xmx128m","h5.jar"]

