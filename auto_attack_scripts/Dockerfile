FROM ubuntu:18.04
  
RUN apt update && apt install vim curl git -y

WORKDIR /home/

COPY auto-push.sh /home/

RUN chmod o+x auto-push.sh

ENTRYPOINT ["bash","-c","/home/auto-push.sh"]
