pipeline {
    agent { label 'onpremise' }  // 'onpremise' 라벨을 가진 에이전트에서만 실행

    environment {
        DOCKER_IMAGE_FLASK = 'Harbor/project/flaskapp'  // Harbor 프로젝트 및 이미지 이름 flaskapp
        DOCKER_IMAGE_NGINX = 'Harbor/project/nginx'  // Harbor 이미지 변수 nginx
        IMAGE_TAG = "${env.BUILD_ID}"  // Jenkins 빌드 ID를 이미지 태그로 사용
        REGISTRY_CREDENTIALS = 'harbor'
        GIT_CREDENTIALS_ID = 'github'  // Jenkins에 저장된 자격 증명 ID
    }

    stages {
        stage('Checkout Source Code') {
            steps {
                git branch: 'main', url: 'https://github.com/mincheol07/onpremisecicd.git'
            }
        }

        stage('Build Docker Image FLASKAPP') {
            steps {
                script {
                    dockerImageFlask = docker.build("${DOCKER_IMAGE_FLASK}:${IMAGE_TAG}")
                }
            }
        }

        stage('Build Docker Image NGINX') {
            steps {
                script {
                    dockerImageNginx = docker.build("${DOCKER_IMAGE_NGINX}:${IMAGE_TAG}", "nginx")
                }
            }
        }

        stage('Push Docker Image to Harbor') {
            steps {
                script {
                    docker.withRegistry('https://Harbor', REGISTRY_CREDENTIALS) {
                        dockerImageFlask.push() // flask 이미지 push
                        dockerImageNginx.push() // nginx 이미지 push
                    }
                }
            }
        }

         stage('Update Kubernetes Manifests') {
            steps {
               withCredentials([usernamePassword(credentialsId: "${GIT_CREDENTIALS_ID}", passwordVariable: 'GIT_PASSWORD', usernameVariable: 'GIT_USERNAME')]) {
                    sh '''
                    #!/bin/bash
                    cd /home/admin/team3k8s/onpremise
                    git pull origin main --rebase
                    sed -i "s|image: Harbor/project/nginx:.*$|image: ${DOCKER_IMAGE_NGINX}:${IMAGE_TAG}|" deployment.yaml # nginx 이미지 업데이트
                    sed -i "s|image: Harbor/project/flaskapp:.*$|image: ${DOCKER_IMAGE_FLASK}:${IMAGE_TAG}|" deployment.yaml # flaskapp 이미지 업데이트
                    git add .
                    git config user.email "chojo480912@gmail.com"
                    git config user.name "mincheol07"
                    git commit -m "Update image tag to ${IMAGE_TAG}"
                    git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/mincheol07/team3k8s.git HEAD:main
                    '''
                }
            }
        }



        
    }

    post {
        always {
            cleanWs()
        }
    }
}
