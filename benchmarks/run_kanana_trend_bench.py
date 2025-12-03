import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any

import requests

from trend_summary import run as run_trend_summary, TrendSummary

# 벤치마크 설정값
MAX_LATENCY_MS = 2000          # 2초 이하면 OK
MIN_BULLETS = 1                # bullets 최소 1개 이상
MIN_KEY_STATS = 1              # key_stats 최소 1개 이상
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

# 테스트 케이스 정의
TEST_CASES: List[Dict[str, Any]] = [
    {
        "id": "general_consumption",
        "keywords": ["소비 트렌드", "가계부", "생활비"],
        "days": 3,
        "max_articles": 10,
    },
    {
        "id": "subscription_focus",
        "keywords": ["구독 서비스", "구독경제", "멤버십"],
        "days": 7,
        "max_articles": 10,
    },
    {
        "id": "small_pleasure",
        "keywords": ["카페 소비", "소확행", "간편식"],
        "days": 7,
        "max_articles": 10,
    },
]


def run_single_case(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    단일 케이스에 대해 trend_summary.run()을 호출하고,
    응답 시간 / bullets / key_stats 등을 검증한다.
    """
    start = time.perf_counter()
    summary: TrendSummary = run_trend_summary(
        db="./openwallet_trends.db",
        keywords=case["keywords"],
        days=case["days"],
        max_articles=case["max_articles"],
        model="kakaocorp/kanana-1.5-2.1b-instruct-2505",
    )
    end = time.perf_counter()
    latency_ms = (end - start) * 1000

    bullets = summary.bullets or []
    key_stats = summary.key_stats or []

    status = "ok"
    reasons: List[str] = []

    if latency_ms > MAX_LATENCY_MS:
        status = "warn"
        reasons.append(f"latency {latency_ms:.0f}ms > {MAX_LATENCY_MS}ms")

    if len(bullets) < MIN_BULLETS:
        status = "warn"
        reasons.append(f"bullets count {len(bullets)} < {MIN_BULLETS}")

    if len(key_stats) < MIN_KEY_STATS:
        status = "warn"
        reasons.append(f"key_stats count {len(key_stats)} < {MIN_KEY_STATS}")

    return {
        "id": case["id"],
        "keywords": case["keywords"],
        "days": case["days"],
        "max_articles": case["max_articles"],
        "latency_ms": latency_ms,
        "bullets_count": len(bullets),
        "key_stats_count": len(key_stats),
        "status": status,
        "reasons": reasons,
        "period_start": summary.period_start,
        "period_end": summary.period_end,
        "model": summary.model,
    }


def send_discord_message(results: List[Dict[str, Any]]) -> None:
    """
    벤치마크 결과를 Discord Webhook으로 전송.
    DISCORD_WEBHOOK_URL 이 설정되지 않은 경우는 조용히 패스.
    """
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("[bench] DISCORD_WEBHOOK_URL not set. Skip Discord notification.")
        return

    total = len(results)
    ok = sum(1 for r in results if r["status"] == "ok")
    warn = total - ok

    avg_latency = sum(r["latency_ms"] for r in results) / total if total > 0 else 0.0

    lines = []
    lines.append("[Kanana Trend Benchmark]")
    lines.append(f"총 케이스: {total}, 정상: {ok}, 경고: {warn}")
    lines.append(f"평균 응답 시간: {avg_latency:.0f} ms (기준 {MAX_LATENCY_MS} ms)")

    for r in results:
        line = (
            f"- {r['id']} | 상태: {r['status']} | "
            f"latency: {r['latency_ms']:.0f} ms | "
            f"bullets: {r['bullets_count']} | key_stats: {r['key_stats_count']}"
        )
        if r["reasons"]:
            line += " | 이유: " + "; ".join(r["reasons"])
        lines.append(line)

    content = "\n".join(lines)

    try:
        resp = requests.post(
            webhook_url,
            json={"content": content},
            timeout=10,
        )
        if resp.status_code >= 400:
            print(f"[bench] Discord webhook failed: {resp.status_code} {resp.text}")
        else:
            print("[bench] Discord notification sent.")
    except Exception as e:
        print(f"[bench] Discord webhook error: {e}")


def main() -> None:
    all_results: List[Dict[str, Any]] = []

    for case in TEST_CASES:
        print(f"[bench] run case: {case['id']}")
        res = run_single_case(case)
        all_results.append(res)
        print(
            f"  -> status={res['status']}, "
            f"latency={res['latency_ms']:.0f}ms, "
            f"bullets={res['bullets_count']}, key_stats={res['key_stats_count']}"
        )

    # 결과 JSON 저장
    out_path = RESULTS_DIR / "kanana_trend_bench.json"
    out_path.write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[bench] results saved -> {out_path}")

    # 디스코드 알림
    send_discord_message(all_results)

    # 하나라도 warn이면 CI 실패 처리
    has_warn = any(r["status"] != "ok" for r in all_results)
    if has_warn:
        print("[bench] some cases are in WARN status. Failing CI.")
        raise SystemExit(1)
    else:
        print("[bench] all cases are OK.")
        raise SystemExit(0)


if __name__ == "__main__":
    main()
