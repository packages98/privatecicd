# 베이스 이미지로 Ubuntu 사용
FROM ubuntu:latest

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치 (Python, 필요한 도구들 설치)
RUN apt-get update && \
    apt-get install -y gcc python3-dev python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/*

# 모든 파일 복사
COPY . .

# 가상 환경 생성 및 활성화
RUN python3 -m venv venv && \
    . ./venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt


# Gunicorn 실행 스크립트 생성
RUN echo ". /app/venv/bin/activate && gunicorn --workers 3 --threads 2 --bind 0.0.0.0:8000 app:app" > /start.sh && \
    chmod +x /start.sh

# 기본 포트 노출
EXPOSE 8000

# 컨테이너 시작 시 실행할 명령
CMD ["/bin/sh", "/start.sh"]
