# WBC 2026 データストア

**2026 ワールドベースボールクラシック（WBC）** の打席・投球レベルのデータセットです。[MLB Stats API](https://statsapi.mlb.com/api/v1) から収集し、**Tableau でのデータ分析・可視化**を目的として整備しています。

> ラウンド終了後に随時更新しています。
> 最終更新: 2026-03-20

## このデータセットの使い方（Tableau）

1. `csv/` フォルダ内の CSV ファイルをすべて Tableau に読み込む
2. `game_id` をキーにテーブルを結合する
3. 試合・イニング・打席・投球の各粒度で分析できる

```
wbc2026_games（試合マスタ）
  └─ game_id で結合
       ├── wbc2026_innings  → イニング別得点推移
       ├── wbc2026_atbats   → 打者・投手別成績
       ├── wbc2026_pitches  → 球種・球速分布
       └── wbc2026_events   → 盗塁・暴投などの走塁イベント
```

---

## データセット概要

| ファイル | 行数（目安） | 説明 |
|---|---|---|
| `csv/wbc2026_games.csv` | 約 50 | 試合マスタ（スコア・ラウンド・チーム） |
| `csv/wbc2026_innings.csv` | 約 500 | イニング別ラインスコア |
| `csv/wbc2026_atbats.csv` | 約 4,000 | 打席結果 |
| `csv/wbc2026_pitches.csv` | 約 16,000 | 投球ごとのデータ（球速・球種） |
| `csv/wbc2026_events.csv` | 約 500 | 打席外イベント（盗塁・暴投など） |

全ファイルは `game_id` をキーに結合できます。

```
wbc2026_games ──┬── wbc2026_innings
                ├── wbc2026_atbats
                ├── wbc2026_pitches
                └── wbc2026_events
```

---

## トーナメント構成

| Pool | 開催地 | 参加チーム |
|---|---|---|
| A | サンファン | Puerto Rico / Colombia / Cuba / Panama / Canada |
| B | ヒューストン | United States / Mexico / Italy / Great Britain / Brazil |
| C | 東京 | Japan / Korea / Australia / Chinese Taipei / Czechia |
| D | マイアミ | Dominican Republic / Venezuela / Kingdom of the Netherlands / Israel / Nicaragua |

ノックアウトラウンド: **準々決勝 → 準決勝 → 決勝**

---

## CSV スキーマ

### wbc2026_games.csv

| カラム | 型 | 説明 |
|---|---|---|
| game_id | 数値 | MLB Stats API の gamePk |
| date | 文字列 | 試合日（YYYY-MM-DD） |
| round | 文字列 | Pool A〜D / Quarterfinal / Semifinal / Final |
| pool | 文字列 | グループ（A/B/C/D）。ノックアウトは null |
| away_team | 文字列 | アウェイチーム名 |
| home_team | 文字列 | ホームチーム名 |
| away_score | 数値 | アウェイ得点 |
| home_score | 数値 | ホーム得点 |
| game_time | 数値 | 試合時間（分） |
| status | 文字列 | Final / Completed Early |

### wbc2026_innings.csv

| カラム | 型 | 説明 |
|---|---|---|
| game_id | 数値 | 試合ID |
| inning | 数値 | イニング番号 |
| batting_team | 文字列 | 攻撃チーム名 |
| runs | 数値 | 得点 |
| hits | 数値 | 安打 |
| errors | 数値 | 失策 |
| left_on_base | 数値 | 残塁 |

### wbc2026_atbats.csv

| カラム | 型 | 説明 |
|---|---|---|
| game_id | 数値 | 試合ID |
| inning | 数値 | イニング番号 |
| batting_team | 文字列 | 攻撃チーム名 |
| pitcher | 文字列 | 投手名 |
| batter | 文字列 | 打者名 |
| pitches | 数値 | 投球数 |
| result | 文字列 | 打席結果 |
| rbi | 数値 | 打点 |
| runner_1b | 文字列 | 一塁走者名（いない場合 null） |
| runner_2b | 文字列 | 二塁走者名（いない場合 null） |
| runner_3b | 文字列 | 三塁走者名（いない場合 null） |

### wbc2026_pitches.csv

| カラム | 型 | 説明 |
|---|---|---|
| game_id | 数値 | 試合ID |
| inning | 数値 | イニング番号 |
| batting_team | 文字列 | 攻撃チーム名 |
| pitcher | 文字列 | 投手名 |
| batter | 文字列 | 打者名 |
| pitch_num | 数値 | 打席内の投球番号 |
| pitch_type | 文字列 | 球種 |
| call | 文字列 | 判定 |
| strikes | 数値 | ストライクカウント（投球後） |
| balls | 数値 | ボールカウント（投球後） |
| speed_kmh | 数値 | 球速（km/h） |

### wbc2026_events.csv

| カラム | 型 | 説明 |
|---|---|---|
| game_id | 数値 | 試合ID |
| inning | 数値 | イニング番号 |
| batting_team | 文字列 | 攻撃チーム名 |
| pitcher | 文字列 | 投手名（イベント発生時） |
| batter | 文字列 | 打者名（イベント発生時） |
| event_type | 文字列 | イベント種別 |
| player | 文字列 | 対象選手名 |
| from_base | 文字列 | 移動前の塁（1B/2B/3B） |
| to_base | 文字列 | 移動後の塁（2B/3B/home/null） |
| runner_1b | 文字列 | 一塁走者名（いない場合 null） |
| runner_2b | 文字列 | 二塁走者名（いない場合 null） |
| runner_3b | 文字列 | 三塁走者名（いない場合 null） |

---

## データソース

- [MLB.com](https://www.mlb.com/) の Stats API からデータを収集しています。

---

## 備考

- 文字コード: UTF-8（BOM なし）
- 欠損値: 空欄
- チーム名は MLB Stats API の英語表記をそのまま使用（例: `Kingdom of the Netherlands`）
- 球種・打席結果・イベント種別は日本語に変換済み
