# OpenWallet_AIOps

OpenWallet AI 서비스의 자동 모니터링 및 운영 자동화를 담당하는 리포지토리입니다.

Kanana 기반 소비 트렌드 요약 및 Qwen 기반 챗봇 기능의
성능과 응답 상태를 주기적으로 진단하고,
변화가 감지되면 Discord로 자동 알림을 제공하여
서비스 안정성을 강화합니다.

## 초기 기능

### Kanana 소비 트렌드 모니터링
- 10분마다 Kanana 트렌드 요약 실행
- 응답 속도 및 품질(요약 필수 요소) 자동 점검
- Discord Webhook 알림 전송
- 성능 저하 감지 시 GitHub Actions 실패 처리

## 필수 Secrets 설정

GitHub Repository > Settings > Secrets > Actions

| Secret Name | Description |
|------------|-------------|
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL |

## 추후 계획

- Qwen 챗봇 라우팅 테스트 + 응답 품질 모니터링 추가
- 지표 누적 수집 및 대시보드화
- Alert 다채널화 (Slack, Email 등)

---

문의 및 기여는 Issues 또는 Pull Request로 남겨주세요.
