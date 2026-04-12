import argparse
import scraping_wbc2026

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WBC 2026 データ取得")
    parser.add_argument(
        "--skip-players",
        action="store_true",
        help="選手プロフィール取得をスキップする（wbc2026_players.csv は更新しない）",
    )
    args = parser.parse_args()
    scraping_wbc2026.run(skip_players=args.skip_players)
