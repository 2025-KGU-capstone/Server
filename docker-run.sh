#!/bin/bash

# 1. 빌드
docker-compose build

# 2. 실행 (자동 재시작 포함)
docker-compose up -d

# 3. 로그 확인
docker-compose logs -f


