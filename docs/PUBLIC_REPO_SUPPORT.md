# Public 저장소 지원 가이드

## 개요

NightWatch는 이제 **Public 저장소를 PAT 없이도 구독**할 수 있습니다. Private 저장소는 여전히 PAT가 필요합니다.

## 사용 방법

### Public 저장소 구독

1. **프론트엔드에서:**

   - 레포지토리 이름 입력 (예: `owner/repo-name`)
   - PAT 필드는 **비워두세요**
   - "구독 추가" 클릭

2. **API로 직접:**
   ```bash
   curl -X POST http://localhost:5001/api/subscriptions \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "user123",
       "repo_full_name": "owner/public-repo",
       "auto_test": true,
       "slack_notify": true
     }'
   ```
   (PAT 필드를 생략하거나 `null`로 설정)

### Private 저장소 구독

Private 저장소는 여전히 PAT가 필요합니다:

```bash
curl -X POST http://localhost:5001/api/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "repo_full_name": "owner/private-repo",
    "pat": "ghp_your-token-here",
    "auto_test": true,
    "slack_notify": true
  }'
```

## 동작 방식

### Public 저장소

- PAT 없이 GitHub API에 접근
- Rate limit: 시간당 60회 (인증 없음)
- 저장소 정보, PR 목록, PR diff 등 모든 Public 데이터 접근 가능

### Private 저장소

- PAT 필수
- Rate limit: 시간당 5,000회 (인증됨)
- Private 저장소의 모든 데이터 접근 가능

## 자동 감지

시스템은 자동으로:

1. PAT가 제공되지 않으면 Public 저장소인지 확인
2. Public이 아니면 에러 메시지 반환
3. Public이면 PAT 없이 구독 생성

## Polling

Polling 서비스는:

- PAT가 있는 구독: PAT를 사용하여 GitHub API 호출
- PAT가 없는 구독: Public API로 접근 (rate limit 낮음)

## 주의사항

1. **Rate Limit**: Public API는 rate limit이 낮으므로, 많은 구독이 있는 경우 PAT 사용을 권장합니다.

2. **Private 저장소**: PAT 없이 Private 저장소를 구독하려고 하면 에러가 발생합니다.

3. **데이터베이스**: 기존 구독은 그대로 유지되며, 새로운 Public 저장소 구독은 `user_credential_id`가 `NULL`로 저장됩니다.

## 예제

### Public 저장소 예제

```python
# Public 저장소 구독 (PAT 없음)
subscription_service.create_subscription(
    user_id="user123",
    repo_full_name="facebook/react",  # Public 저장소
    pat=None,  # 또는 생략
    auto_test=True
)
```

### Private 저장소 예제

```python
# Private 저장소 구독 (PAT 필요)
subscription_service.create_subscription(
    user_id="user123",
    repo_full_name="company/private-repo",
    pat="ghp_xxxxxxxxxxxx",
    auto_test=True
)
```
