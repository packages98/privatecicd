# Nginx의 기본 이미지를 사용
FROM nginx:latest

# nginx.conf 파일을 복사해서 Nginx 기본 설정을 덮어씀
COPY nginx.conf /etc/nginx/nginx.conf

# default.conf 파일을 복사해서 conf.d 디렉토리에 설정 추가
COPY default.conf /etc/nginx/conf.d/default.conf

# Nginx 기본 포트 80 노출
EXPOSE 80

# Nginx를 포그라운드에서 실행
CMD ["nginx", "-g", "daemon off;"]
