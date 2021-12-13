FROM openjdk:11-jdk-bullseye
RUN addgroup --system spring && adduser --system spring --ingroup spring
RUN apt update && apt install netcat -y
USER spring:spring
COPY WGMYWS-1.0.0-DIST.jar app.jar
COPY flag.txt /opt/flag.txt
ENTRYPOINT ["java","-jar","/app.jar"]
