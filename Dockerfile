FROM debian:latest
LABEL authors="John Samarasinghe"

ENTRYPOINT ["top", "-b"]

RUN apt update
RUN apt install python3.11-venv -y
RUN apt install -y libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev llvm libncurses5-dev
RUN apt install -y libncursesw5-dev xz-utils tk-dev libgdbm-dev lzma lzma-dev tcl-dev libxml2-dev libxmlsec1-dev
RUN apt install -y libffi-dev liblzma-dev wget curl make build-essential openssl
RUN apt install -y python3-dev default-libmysqlclient-dev build-essential
RUN apt install python3-flask -y
RUN apt install libopenjp2-7-dev -y
RUN apt install libopenblas-dev -y
RUN apt install unixodbc-dev -y
RUN apt install git -y
