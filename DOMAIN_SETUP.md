# 울산유흥.shop 도메인 연결

표시 주소: https://울산유흥.shop
DNS/서버 내부 표기(Punycode): xn--zf4b93i7ik96c.shop

1. Docker 및 Docker Compose가 설치된 공개 서버(VPS)를 준비합니다. 외부 TCP 80, 443 포트를 열어야 합니다.
2. 도메인 구매처의 DNS 관리에서 A 레코드 호스트 @ 를 **실제 서버 공인 IPv4**로 설정합니다. 서버 IP를 모르는 상태에서 임의 IP를 넣지 마세요. www도 사용하려면 별도 DNS/서버 설정이 필요합니다.
3. 이 폴더의 `.env.example`을 `.env`로 복사하고 YAHWA_ADMIN_PASSWORD를 고유하고 긴 비밀번호로 변경합니다. `.env`를 공개 저장소에 업로드하지 마세요.
4. 서버에서 `docker compose up -d --build`를 실행합니다.
5. DNS 전파 후 https://울산유흥.shop 에서 HTTPS 및 사이트 표시를 확인합니다.
6. Google Search Console에서 도메인 속성 `울산유흥.shop` (또는 `xn--zf4b93i7ik96c.shop`)을 추가하고 Google이 발급한 TXT 인증 레코드를 DNS에 등록합니다.
7. https://울산유흥.shop/sitemap.xml 을 Search Console에 제출합니다.

주의: 실제 배포, DNS 변경, 구글 소유권 인증은 아직 실행되지 않았습니다. 동영상은 외부 링크이므로 만료 시 재생되지 않을 수 있습니다. 공개 전 관리자 보안, 게시판 개인정보, 법적 광고 문구를 점검하세요.
