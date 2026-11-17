# 울산 야화 Google 공개 배포 + 검색 등록

## 1. 준비
- 본인 소유 도메인, 공인 IP가 있는 Ubuntu 서버(VPS), Docker Engine + Docker Compose 설치
- 서버 80/443 포트 개방, 도메인 A 레코드를 서버 IP로 연결
- 이 패키지는 Google Search 등록과 별도로 **서버 배포**가 필요합니다. Google Search Console 자체는 호스팅이 아닙니다.

## 2. 설정
```bash
cp .env.example .env
nano .env
```
`SITE_DOMAIN`은 본인 소유 도메인으로 바꾸고 `YAHWA_ADMIN_PASSWORD`는 20자 이상 무작위 문자열로 바꾸세요. `.env`는 공개 업로드 금지.

## 3. 서버 시작
```bash
docker compose up -d --build
```
- `https://도메인/` 방문자 사이트
- `https://도메인/admin.html` 관리자
- `https://도메인/robots.txt` 로봇 정책
- `https://도메인/sitemap.xml` 사이트맵
- Caddy가 DNS 연결 후 HTTPS 인증서를 자동 발급합니다.

## 4. Google 검색 등록
1. https://search.google.com/search-console 에서 도메인 속성 추가
2. DNS TXT 소유권 인증
3. 사이트맵 `https://도메인/sitemap.xml` 제출
4. URL 검사에서 홈페이지 주소 입력 → 색인 생성 요청
5. 구글 색인 및 순위는 보장되지 않습니다.

## 5. 운영 주의
- 서버 SQLite는 Docker `yahwa_data` 볼륨에 저장됩니다. 주기적으로 백업하세요.
- `admin.html`은 검색에서 제외하지만 공개 URL입니다. 강한 비밀번호 및 추가 보안(로그인 제한/WAF/모니터링)이 필요합니다.
- 공개 후기 게시판은 스팸 방지, 개인정보 안내, 신고/삭제 운영 정책이 필요합니다.
- 외부 HeyGen 영상 주소는 만료될 수 있어 자체 호스팅 MP4로 교체하는 것이 안전합니다.
- 업소/영업 정보는 실제 확인 후 공개하고 허위 출근·후기 정보는 넣지 마세요.
- 본 패키지는 운영 시제품이며 보안 침투 테스트나 실기기 전수 검증은 하지 않았습니다.
