import re
import requests
import csv
import time
from collections import defaultdict

BASE_URL = "https://statsapi.mlb.com/api/v1"
DATA_DIR = "../csv"

TEAM_POOL = {
    # Pool A - San Juan
    "Puerto Rico": "A",
    "Colombia": "A",
    "Cuba": "A",
    "Panama": "A",
    "Canada": "A",
    # Pool B - Houston
    "United States": "B",
    "Mexico": "B",
    "Italy": "B",
    "Great Britain": "B",
    "Brazil": "B",
    # Pool C - Tokyo
    "Japan": "C",
    "Korea": "C",
    "Australia": "C",
    "Chinese Taipei": "C",
    "Czechia": "C",
    # Pool D - Miami
    "Dominican Republic": "D",
    "Venezuela": "D",
    "Kingdom of the Netherlands": "D",
    "Israel": "D",
    "Nicaragua": "D",
}

PITCH_TYPE_JA = {
    "FF": "直球",
    "SI": "ツーシーム",
    "SL": "スライダー",
    "CU": "カーブ",
    "CH": "チェンジアップ",
    "SP": "フォーク",
    "FS": "フォーク",
    "FC": "カットボール",
    "KC": "ナックルカーブ",
    "KN": "ナックル",
    "EP": "エフェス",
    "FO": "フォーク",
    "CS": "スローカーブ",
    "SC": "スクリューボール",
    "PO": "ピッチアウト",
    "IN": "申告敬遠",
    "UN": "不明",
    "FT": "ツーシーム",   # 旧コード
    "ST": "スイーパー",
    "SV": "スラーブ",
}

RESULT_JA = {
    "single": "安打",
    "double": "二塁打",
    "triple": "三塁打",
    "home_run": "本塁打",
    "strikeout": "三振",
    "strikeout_double_play": "三振併殺",
    "walk": "四球",
    "intent_walk": "申告敬遠",
    "hit_by_pitch": "死球",
    "sac_bunt": "犠打",
    "sac_fly": "犠飛",
    "sac_bunt_double_play": "犠打併殺",
    "double_play": "併殺",
    "triple_play": "三重殺",
    "grounded_into_double_play": "ゴロ併殺",
    "field_out": "アウト",
    "force_out": "フォースアウト",
    "fielders_choice": "フィールダースチョイス",
    "fielders_choice_out": "フィールダースチョイスアウト",
    "field_error": "エラー",
    "catcher_interf": "捕手妨害",
    "fan_interference": "観客妨害",
    "other_out": "その他アウト",
    "caught_stealing_2b": "盗塁死（二塁）",
    "caught_stealing_3b": "盗塁死（三塁）",
    "caught_stealing_home": "盗塁死（本塁）",
    "pickoff_1b": "牽制（一塁）",
    "pickoff_2b": "牽制（二塁）",
    "pickoff_3b": "牽制（三塁）",
    "pickoff_caught_stealing_2b": "牽制盗塁死（二塁）",
    "pickoff_caught_stealing_3b": "牽制盗塁死（三塁）",
    "pickoff_caught_stealing_home": "牽制盗塁死（本塁）",
    "runner_double_play": "ランダウン",
    "runner_out": "走者アウト",
}

CALL_JA = {
    "B": "ボール",
    "C": "ストライク（見逃し）",
    "S": "ストライク（空振り）",
    "F": "ファール",
    "X": "インプレー",
    "T": "ファールチップ",
    "L": "ファールバント",
    "O": "空振り（バント）",
    "P": "ピッチアウト",
    "Q": "スイング（ピッチアウト）",
    "R": "ファール（ピッチアウト）",
    "M": "見逃し（バント）",
    "N": "申告敬遠",
    "I": "申告敬遠",
    "K": "ストライク",
    "D": "死球",
    "E": "エラー（投球）",
    "H": "ヒットバイピッチ",
    "V": "申告敬遠",
    "*B": "ボール（自動）",
}

EVENT_TYPE_JA = {
    "stolen_base_2b": "盗塁（二塁）",
    "stolen_base_3b": "盗塁（三塁）",
    "stolen_base_home": "盗塁（本塁）",
    "caught_stealing_2b": "盗塁死（二塁）",
    "caught_stealing_3b": "盗塁死（三塁）",
    "caught_stealing_home": "盗塁死（本塁）",
    "wild_pitch": "暴投",
    "passed_ball": "捕逸",
    "balk": "ボーク",
    "defensive_indiff": "守備妨害",
    "pickoff_1b": "牽制（一塁）",
    "pickoff_2b": "牽制（二塁）",
    "pickoff_3b": "牽制（三塁）",
    "pickoff_caught_stealing_2b": "牽制盗塁死（二塁）",
    "pickoff_caught_stealing_3b": "牽制盗塁死（三塁）",
    "pickoff_caught_stealing_home": "牽制盗塁死（本塁）",
    "runner_double_play": "ランダウン",
    "runner_out": "走者アウト",
    "error": "エラー",
}

# 打席フラグ用定数
HIT_TYPES = {"single", "double", "triple", "home_run"}
WALK_TYPES = {"walk", "intent_walk"}
NOT_AT_BAT = {"walk", "intent_walk", "hit_by_pitch", "sac_bunt", "sac_fly",
              "sac_bunt_double_play", "catcher_interf", "fan_interference"}
SAC_TYPES = {"sac_bunt", "sac_fly", "sac_bunt_double_play"}
STRIKEOUT_TYPES = {"strikeout", "strikeout_double_play", "strikeout_triple_play"}
TOTAL_BASES_MAP = {"single": 1, "double": 2, "triple": 3, "home_run": 4}

# 投球フラグ用定数
STRIKE_CALLS = {"S", "C", "F", "T", "X", "L", "O", "K"}
SWING_CALLS = {"S", "F", "T", "X", "L", "O"}
CONTACT_CALLS = {"F", "T", "X", "L"}


def calc_atbat_flags(event_type):
    return {
        "is_plate_appearance": 1,
        "is_at_bat": 0 if event_type in NOT_AT_BAT else 1,
        "is_hit": 1 if event_type in HIT_TYPES else 0,
        "is_single": 1 if event_type == "single" else 0,
        "is_double": 1 if event_type == "double" else 0,
        "is_triple": 1 if event_type == "triple" else 0,
        "is_home_run": 1 if event_type == "home_run" else 0,
        "is_strikeout": 1 if event_type in STRIKEOUT_TYPES else 0,
        "is_walk": 1 if event_type in WALK_TYPES else 0,
        "is_hbp": 1 if event_type == "hit_by_pitch" else 0,
        "is_sac": 1 if event_type in SAC_TYPES else 0,
        "total_bases": TOTAL_BASES_MAP.get(event_type, 0),
    }


def calc_pitch_flags(call_code):
    if call_code in ("C", "K", "S", "O", "M"):
        group = "ストライク"
    elif call_code in ("F", "T", "L", "R", "Q"):
        group = "ファール"
    elif call_code == "X":
        group = "インプレー"
    elif call_code in ("B", "*B", "P", "D", "H", "N", "I", "V", "E"):
        group = "ボール"
    else:
        group = None
    return {
        "is_strike": 1 if call_code in STRIKE_CALLS else 0,
        "is_swing": 1 if call_code in SWING_CALLS else 0,
        "is_contact": 1 if call_code in CONTACT_CALLS else 0,
        "pitch_result_group": group,
    }


def fetch_schedule():
    url = f"{BASE_URL}/schedule"
    params = {
        "sportId": 51,
        "season": 2026,
        "gameType": "S,R,P,F,D,L,W",
        "startDate": "2026-03-01",
        "endDate": "2026-03-20",
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()

    games = []
    for date in data.get("dates", []):
        for g in date.get("games", []):
            games.append({
                "game_pk": g["gamePk"],
                "date": date["date"],
                "away_team": g["teams"]["away"]["team"]["name"],
                "home_team": g["teams"]["home"]["team"]["name"],
                "status": g["status"]["detailedState"],
                "series_description": g.get("seriesDescription", ""),
            })
    return games


def fetch_play_by_play(game_pk):
    url = f"{BASE_URL}/game/{game_pk}/playByPlay"
    res = requests.get(url)
    res.raise_for_status()
    return res.json()


def fetch_linescore(game_pk):
    url = f"{BASE_URL}/game/{game_pk}/linescore"
    res = requests.get(url)
    res.raise_for_status()
    return res.json()


def fetch_boxscore(game_pk):
    url = f"{BASE_URL}/game/{game_pk}/boxscore"
    res = requests.get(url)
    res.raise_for_status()
    return res.json()


def fetch_player_profile(person_id):
    url = f"{BASE_URL}/people/{person_id}?hydrate=currentTeam"
    res = requests.get(url)
    res.raise_for_status()
    data = res.json()
    return data["people"][0] if data.get("people") else None


def parse_height_cm(height_str):
    if not height_str:
        return None
    m = re.match(r"(\d+)'\s*(\d+)\"", height_str)
    if m:
        return round(int(m.group(1)) * 30.48 + int(m.group(2)) * 2.54)
    return None


def parse_weight_kg(weight_lbs):
    if not weight_lbs:
        return None
    return round(weight_lbs * 0.453592)


def fetch_players(player_ids):
    players_rows = []
    total = len(player_ids)
    for i, (pid, team_info) in enumerate(player_ids.items(), 1):
        print(f"  選手プロフィール取得 ({i}/{total}): {pid}")
        try:
            profile = fetch_player_profile(pid)
            if not profile:
                continue
            debut = profile.get("mlbDebutDate", "")
            debut_year = int(debut[:4]) if debut else None
            players_rows.append({
                "player_id": pid,
                "player_name": profile.get("fullName"),
                "wbc_team": team_info["wbc_team"],
                "position": team_info["position"],
                "jersey_number": team_info["jersey_number"],
                "birth_date": profile.get("birthDate"),
                "age": profile.get("currentAge"),
                "height_cm": parse_height_cm(profile.get("height")),
                "weight_kg": parse_weight_kg(profile.get("weight")),
                "bat_side": profile.get("batSide", {}).get("code"),
                "pitch_hand": profile.get("pitchHand", {}).get("code"),
                "birth_country": profile.get("birthCountry"),
                "mlb_team": profile.get("currentTeam", {}).get("name"),
                "mlb_debut_year": debut_year,
                "mlb_experience_years": 2026 - debut_year if debut_year else None,
            })
            time.sleep(0.3)
        except Exception as e:
            print(f"  エラー: {pid} - {e}")
    return players_rows


def parse_runners(runners):
    r1, r2, r3 = False, False, False
    for r in runners:
        base = r.get("movement", {}).get("originBase") or r.get("movement", {}).get("start")
        if base == "1B":
            r1 = True
        elif base == "2B":
            r2 = True
        elif base == "3B":
            r3 = True
    return int(r1), int(r2), int(r3)


def add_cumulative_scores(innings_rows, games_rows):
    game_teams = {g["game_id"]: (g["away_team"], g["home_team"]) for g in games_rows}
    game_innings = defaultdict(list)
    for row in innings_rows:
        game_innings[row["game_id"]].append(row)

    result = []
    for game_id, rows in game_innings.items():
        away_team, home_team = game_teams.get(game_id, (None, None))
        rows_sorted = sorted(rows, key=lambda r: (r["inning"], 0 if r["batting_team"] == away_team else 1))
        away_cum = 0
        home_cum = 0
        for row in rows_sorted:
            if row["batting_team"] == away_team:
                away_cum += row["runs"]
                row["cumulative_runs"] = away_cum
                row["score_diff"] = away_cum - home_cum
            else:
                home_cum += row["runs"]
                row["cumulative_runs"] = home_cum
                row["score_diff"] = home_cum - away_cum
        result.extend(rows_sorted)
    return result


def process_game(game_pk, game_info, games_rows, innings_rows, atbats_rows, pitches_rows, events_rows, pitching_rows, player_ids):
    print(f"  取得中: {game_info['away_team']} vs {game_info['home_team']}")
    pbp = fetch_play_by_play(game_pk)
    box = fetch_boxscore(game_pk)
    linescore = fetch_linescore(game_pk)

    away_name = box["teams"]["away"]["team"]["name"]
    home_name = box["teams"]["home"]["team"]["name"]
    away_score = box["teams"]["away"].get("teamStats", {}).get("batting", {}).get("runs", 0)
    home_score = box["teams"]["home"].get("teamStats", {}).get("batting", {}).get("runs", 0)

    # round / pool 判定
    away_pool = TEAM_POOL.get(away_name)
    home_pool = TEAM_POOL.get(home_name)
    if away_pool and home_pool and away_pool == home_pool:
        round_name = f"Pool {away_pool}"
        pool = away_pool
    else:
        pool = None
        series_desc = game_info.get("series_description", "").lower()
        if "semifinal" in series_desc:
            round_name = "Semifinal"
        elif "quarterfinal" in series_desc:
            round_name = "Quarterfinal"
        elif series_desc:
            # "World Baseball Classic" など Final 相当
            round_name = "Final"
        else:
            # seriesDescription が取れない場合は日付で判定
            game_date = game_info.get("date", "")
            if game_date in ("2026-03-15", "2026-03-16"):
                round_name = "Semifinal"
            elif game_date == "2026-03-17":
                round_name = "Final"
            else:
                round_name = "Quarterfinal"

    # winner / loser / score_diff
    if away_score > home_score:
        winner, loser = away_name, home_name
    elif home_score > away_score:
        winner, loser = home_name, away_name
    else:
        winner, loser = None, None
    score_diff = abs(away_score - home_score)

    info = box.get("gameInfo", {})
    games_rows.append({
        "game_id": game_pk,
        "date": game_info["date"],
        "round": round_name,
        "pool": pool,
        "away_team": away_name,
        "home_team": home_name,
        "away_score": away_score,
        "home_score": home_score,
        "winner": winner,
        "loser": loser,
        "score_diff": score_diff,
        "game_time": info.get("gameDurationMinutes", None),
        "status": game_info["status"],
    })

    # boxscore から選手IDを収集
    for side in ("away", "home"):
        team_name = away_name if side == "away" else home_name
        players = box["teams"][side].get("players", {})
        for player_key, player_data in players.items():
            pid = player_data.get("person", {}).get("id")
            if pid and pid not in player_ids:
                position = player_data.get("position", {}).get("abbreviation")
                jersey = player_data.get("jerseyNumber")
                player_ids[pid] = {
                    "wbc_team": team_name,
                    "position": position,
                    "jersey_number": jersey,
                }

    # boxscore から投手成績を収集
    for side in ("away", "home"):
        pitching_team = away_name if side == "away" else home_name
        pitcher_ids = box["teams"][side].get("pitchers", [])
        players = box["teams"][side].get("players", {})
        for pid in pitcher_ids:
            player_data = players.get(f"ID{pid}", {})
            p_stats = player_data.get("stats", {}).get("pitching", {})
            if not p_stats:
                continue
            pitcher_name = player_data.get("person", {}).get("fullName", "")
            innings_pitched_str = p_stats.get("inningsPitched", "0.0")
            try:
                ip_parts = str(innings_pitched_str).split(".")
                ip_decimal = int(ip_parts[0]) + int(ip_parts[1]) / 3 if len(ip_parts) > 1 else float(ip_parts[0])
            except Exception:
                ip_decimal = None
            pitching_rows.append({
                "game_id": game_pk,
                "date": game_info["date"],
                "round": round_name,
                "pool": pool,
                "pitching_team": pitching_team,
                "pitcher_id": pid,
                "pitcher": pitcher_name,
                "innings_pitched": innings_pitched_str,
                "innings_pitched_dec": ip_decimal,
                "earned_runs": p_stats.get("earnedRuns", 0),
                "runs": p_stats.get("runs", 0),
                "hits": p_stats.get("hits", 0),
                "strikeouts": p_stats.get("strikeOuts", 0),
                "walks": p_stats.get("baseOnBalls", 0),
                "home_runs": p_stats.get("homeRuns", 0),
                "batters_faced": p_stats.get("battersFaced", 0),
                "num_pitches": p_stats.get("numberOfPitches", 0),
            })

    # innings
    for inning in linescore.get("innings", []):
        inning_num = inning["num"]
        for half, team in [("away", away_name), ("home", home_name)]:
            half_data = inning.get(half, {})
            innings_rows.append({
                "game_id": game_pk,
                "inning": inning_num,
                "batting_team": team,
                "runs": half_data.get("runs", 0),
                "hits": half_data.get("hits", 0),
                "errors": half_data.get("errors", 0),
                "left_on_base": half_data.get("leftOnBase", 0),
            })

    # atbats / pitches / events
    for play in pbp.get("allPlays", []):
        about = play.get("about", {})
        inning = about.get("inning")
        half = about.get("halfInning", "")
        batting_team = away_name if half == "top" else home_name
        pitching_team = home_name if half == "top" else away_name
        matchup = play.get("matchup", {})
        pitcher = matchup.get("pitcher", {}).get("fullName")
        pitcher_id = matchup.get("pitcher", {}).get("id")
        batter = matchup.get("batter", {}).get("fullName")
        batter_id = matchup.get("batter", {}).get("id")
        result = play.get("result", {})
        event_type = result.get("eventType", "")
        rbi = result.get("rbi", 0)

        runners_before = [r for r in play.get("runners", [])
                          if r.get("movement", {}).get("originBase") is not None]
        r1, r2, r3 = parse_runners(runners_before)
        pitch_count = sum(1 for pe in play.get("playEvents", []) if pe.get("type") == "pitch")

        atbat_row = {
            "game_id": game_pk,
            "date": game_info["date"],
            "round": round_name,
            "pool": pool,
            "inning": inning,
            "batting_team": batting_team,
            "pitching_team": pitching_team,
            "pitcher_id": pitcher_id,
            "pitcher": pitcher,
            "batter_id": batter_id,
            "batter": batter,
            "pitches": pitch_count,
            "result": RESULT_JA.get(event_type, event_type),
            "rbi": rbi,
            "runner_on_1b": r1,
            "runner_on_2b": r2,
            "runner_on_3b": r3,
        }
        atbat_row.update(calc_atbat_flags(event_type))
        atbats_rows.append(atbat_row)

        pitch_num = 0
        for pe in play.get("playEvents", []):
            if pe.get("type") == "pitch":
                pitch_num += 1
                details = pe.get("details", {})
                pitch_data = pe.get("pitchData", {})
                call_code = details.get("call", {}).get("code", "")
                pitch_type_code = details.get("type", {}).get("code", "")
                pitch_row = {
                    "game_id": game_pk,
                    "date": game_info["date"],
                    "round": round_name,
                    "pool": pool,
                    "inning": inning,
                    "batting_team": batting_team,
                    "pitching_team": pitching_team,
                    "pitcher_id": pitcher_id,
                    "pitcher": pitcher,
                    "batter_id": batter_id,
                    "batter": batter,
                    "pitch_num": pitch_num,
                    "pitch_type": PITCH_TYPE_JA.get(pitch_type_code, pitch_type_code),
                    "call": CALL_JA.get(call_code, call_code),
                    "strikes": pe.get("count", {}).get("strikes"),
                    "balls": pe.get("count", {}).get("balls"),
                    "speed_kmh": round(pitch_data.get("startSpeed") * 1.60934, 1) if pitch_data.get("startSpeed") else None,
                }
                pitch_row.update(calc_pitch_flags(call_code))
                pitches_rows.append(pitch_row)

            elif pe.get("type") == "action":
                details = pe.get("details", {})
                ev = details.get("eventType", "")
                if ev in EVENT_TYPE_JA:
                    for runner in play.get("runners", []):
                        if runner.get("details", {}).get("eventType", "") == ev:
                            events_rows.append({
                                "game_id": game_pk,
                                "date": game_info["date"],
                                "round": round_name,
                                "pool": pool,
                                "inning": inning,
                                "batting_team": batting_team,
                                "pitching_team": pitching_team,
                                "pitcher_id": pitcher_id,
                                "pitcher": pitcher,
                                "batter_id": batter_id,
                                "batter": batter,
                                "event_type": EVENT_TYPE_JA.get(ev, ev),
                                "player_id": runner.get("details", {}).get("runner", {}).get("id"),
                                "player": runner.get("details", {}).get("runner", {}).get("fullName"),
                                "from_base": runner.get("movement", {}).get("originBase"),
                                "to_base": runner.get("movement", {}).get("end"),
                            })


COLUMN_MAP = {
    "game_id":              "試合ID",
    "date":                 "日付",
    "round":                "ラウンド",
    "pool":                 "プール",
    "away_team":            "アウェイチーム",
    "home_team":            "ホームチーム",
    "away_score":           "アウェイ得点",
    "home_score":           "ホーム得点",
    "winner":               "勝利チーム",
    "loser":                "敗戦チーム",
    "score_diff":           "得点差",
    "game_time":            "試合時間（分）",
    "status":               "ステータス",
    "inning":               "イニング",
    "batting_team":         "攻撃チーム",
    "pitching_team":        "守備チーム",
    "runs":                 "得点",
    "hits":                 "安打数",
    "errors":               "失策",
    "left_on_base":         "残塁",
    "cumulative_runs":      "累積得点",
    "pitcher_id":           "投手ID",
    "pitcher":              "投手",
    "batter_id":            "打者ID",
    "batter":               "打者",
    "pitches":              "投球数",
    "result":               "打席結果",
    "rbi":                  "打点",
    "runner_on_1b":         "一塁走者あり",
    "runner_on_2b":         "二塁走者あり",
    "runner_on_3b":         "三塁走者あり",
    "is_plate_appearance":  "打席",
    "is_at_bat":            "打数",
    "is_hit":               "安打",
    "is_single":            "一塁打",
    "is_double":            "二塁打",
    "is_triple":            "三塁打",
    "is_home_run":          "本塁打",
    "is_strikeout":         "三振",
    "is_walk":              "四球",
    "is_hbp":               "死球",
    "is_sac":               "犠打犠飛",
    "total_bases":          "塁打数",
    "pitch_num":            "投球番号",
    "pitch_type":           "球種",
    "call":                 "判定",
    "strikes":              "ストライク",
    "balls":                "ボール",
    "speed_kmh":            "球速（km/h）",
    "is_strike":            "ストライク判定",
    "is_swing":             "スイング",
    "is_contact":           "コンタクト",
    "pitch_result_group":   "結果グループ",
    "event_type":           "イベント種別",
    "player_id":            "選手ID",
    "player":               "選手",
    "from_base":            "移動前の塁",
    "to_base":              "移動後の塁",
    "player_name":          "選手名",
    "wbc_team":             "WBCチーム",
    "position":             "ポジション",
    "jersey_number":        "背番号",
    "birth_date":           "生年月日",
    "age":                  "年齢",
    "height_cm":            "身長（cm）",
    "weight_kg":            "体重（kg）",
    "bat_side":             "打席",
    "pitch_hand":           "投球腕",
    "birth_country":        "出身国",
    "mlb_team":             "MLBチーム",
    "mlb_debut_year":       "MLB初出場年",
    "mlb_experience_years": "MLB経験年数",
    "pitching_team":        "守備チーム",
    "innings_pitched":      "投球回",
    "innings_pitched_dec":  "投球回（小数）",
    "earned_runs":          "自責点",
    "runs":                 "失点",
    "hits":                 "被安打",
    "strikeouts":           "奪三振",
    "walks":                "与四球",
    "home_runs":            "被本塁打",
    "batters_faced":        "対戦打者数",
    "num_pitches":          "投球数",
}


def write_csv(filename, rows, fieldnames):
    filepath = f"{DATA_DIR}/{filename}"
    renamed_rows = [{COLUMN_MAP.get(k, k): v for k, v in row.items()} for row in rows]
    renamed_fields = [COLUMN_MAP.get(f, f) for f in fieldnames]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=renamed_fields)
        writer.writeheader()
        writer.writerows(renamed_rows)
    print(f"保存: {filepath} ({len(rows)}行)")


def run(skip_players=False):
    print("=== WBC 2026 データ取得 ===")
    if skip_players:
        print("※ 選手プロフィール取得をスキップします（wbc2026_players.csv は更新しません）")
    games = fetch_schedule()
    print(f"試合数: {len(games)}")

    games_rows, innings_rows, atbats_rows, pitches_rows, events_rows, pitching_rows = [], [], [], [], [], []
    player_ids = {}

    for game in games:
        if game["status"] not in ("Final", "Completed Early"):
            print(f"  スキップ: {game['away_team']} vs {game['home_team']} ({game['status']})")
            continue
        try:
            process_game(game["game_pk"], game, games_rows, innings_rows, atbats_rows, pitches_rows, events_rows, pitching_rows, player_ids)
            time.sleep(0.5)
        except Exception as e:
            print(f"  エラー: {game['game_pk']} - {e}")

    innings_rows = add_cumulative_scores(innings_rows, games_rows)
    if not skip_players:
        players_rows = fetch_players(player_ids)

    write_csv("wbc2026_games.csv", games_rows,
              ["game_id", "date", "round", "pool", "away_team", "home_team",
               "away_score", "home_score", "winner", "loser", "score_diff", "game_time", "status"])

    write_csv("wbc2026_innings.csv", innings_rows,
              ["game_id", "inning", "batting_team", "runs", "hits", "errors", "left_on_base",
               "cumulative_runs", "score_diff"])

    write_csv("wbc2026_atbats.csv", atbats_rows,
              ["game_id", "date", "round", "pool", "inning", "batting_team", "pitching_team",
               "pitcher_id", "pitcher", "batter_id", "batter", "pitches", "result", "rbi",
               "runner_on_1b", "runner_on_2b", "runner_on_3b",
               "is_plate_appearance", "is_at_bat", "is_hit", "is_single", "is_double",
               "is_triple", "is_home_run", "is_strikeout", "is_walk", "is_hbp", "is_sac", "total_bases"])

    write_csv("wbc2026_pitches.csv", pitches_rows,
              ["game_id", "date", "round", "pool", "inning", "batting_team", "pitching_team",
               "pitcher_id", "pitcher", "batter_id", "batter", "pitch_num", "pitch_type", "call", "strikes", "balls", "speed_kmh",
               "is_strike", "is_swing", "is_contact", "pitch_result_group"])

    write_csv("wbc2026_events.csv", events_rows,
              ["game_id", "date", "round", "pool", "inning", "batting_team", "pitching_team",
               "pitcher_id", "pitcher", "batter_id", "batter", "event_type", "player_id", "player", "from_base", "to_base"])

    if not skip_players:
        write_csv("wbc2026_players.csv", players_rows,
                  ["player_id", "player_name", "wbc_team", "position", "jersey_number",
                   "birth_date", "age", "height_cm", "weight_kg",
                   "bat_side", "pitch_hand", "birth_country",
                   "mlb_team", "mlb_debut_year", "mlb_experience_years"])

    write_csv("wbc2026_pitching.csv", pitching_rows,
              ["game_id", "date", "round", "pool", "pitching_team", "pitcher_id", "pitcher",
               "innings_pitched", "innings_pitched_dec",
               "earned_runs", "runs", "hits", "strikeouts", "walks",
               "home_runs", "batters_faced", "num_pitches"])
