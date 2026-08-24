# persona-lightsim

[English](README.md) | [한국어](README.ko.md) | **日本語** | [中文](README.zh.md)

[Claude Code](https://claude.com/claude-code)向けの軽量ペルソナ市場調査・シミュレーションハーネス。任意のプロダクトを**10か国の合成人口**(NVIDIA [Nemotron-Personas](https://huggingface.co/nvidia))に写像し、ユースケース分析・支払い意思の判定・バッチ判定による反応シミュレーション・再利用可能なペルソナカードを生成する — **ウェブアプリもシミュレーションサーバーも不要、データはわずか63MB。**

## AIに任せるセットアップ

Claude Code(または任意のコーディングエージェント)にそのまま貼り付ける:

```
https://github.com/Dongkyu-ES/persona-lightsim をセットアップして:
1. git clone https://github.com/Dongkyu-ES/persona-lightsim && cd persona-lightsim
2. python3 scripts/setup_data.py        # HuggingFaceから63MBのライトデータをダウンロード + pyarrow venv作成
3. セットアップが出力するスモークテストを実行して結果を見せて。
スキル文書の言語切替: python3 scripts/set_language.py ko (デフォルトは英語)。
```

以上。レポジトリをClaude Codeで開き、こう依頼するだけ:

- *「プロダクトXを10か国のペルソナに当ててユースケースと支払い意思を分析して」* → `persona-research`スキル(国別アナリストの並列ファンアウト)
- *「このブリーフで韓国100人の軽量シミュレーションを回してパックを作って」* → `persona-lightsim`スキル(バッチ判定 → mean-field 2次パス → カード蒸留 → sqliteパック)

## 構成

| 要素 | 役割 |
|---|---|
| `.claude/skills/persona-research` | オーケストレーター: ブリーフ監査 → サンプリング → 国別分析ファンアウト → 統合 → QA |
| `.claude/skills/persona-country-analysis` | 単位方法論: 実カウントスクリーニング → 精読 → 7セクションレポート |
| `.claude/skills/persona-lightsim` | 対話なしシミュレーション: バッチ判定(1呼び出し=25人) → 決定的集計 → 世論再注入2次パス → セグメントカード → ローカルパック |
| `.claude/agents/persona-*` (5種) | brief-auditor / country-analyst / synthesis-critic / batch-judge / distiller |
| `scripts/setup_data.py` | ライトデータのダウンロード(sha256固定マニフェスト) + venv構成 |
| `scripts/set_language.py` | アクティブなスキル・エージェント文書を`en`/`ko`で切替 |

元ハーネスでのパイプライン全体の実測値: バッチ判定スキーマ有効99/99、2次パスの意見変化率24.2%(0%でも100%でもない — mean-field再注入が実際に機能することを実証)、カードの根拠引用39/39をサンプル原文と照合検証。

## データ

`scripts/setup_data.py`が取得するのは**ライトパック** — [`dominicDK94/nemotron-personas-lite`](https://huggingface.co/datasets/dominicDK94/nemotron-personas-lite) — NVIDIA Nemotron-Personas(CC-BY-4.0)の派生再配布版:

- 10か国: ベルギー・ブラジル・エルサルバドル・フランス・インド・日本・韓国・シンガポール・米国・ベトナム
- 国あたり10,000人、原本0.1M~1.2Mからシード42固定抽出
- 26カラム中ハーネスが読む15カラムのみ保持、長い叙述フィールドは300~400字にトリム
- 原本のシャード構造を保存(ベルギーの言語クォータ、インドの英語のみ) — サンプラーはライト/フルデータで無修正で動作
- **合計~63MB**(原本は~24GB)

トリムなしのフルデータが必要な場合はNVIDIAの原本をHuggingFaceから取得し、環境変数で指定する:

```bash
export NEMOTRON_PERSONAS_BASE=/path/to/full-data   # nemotron-personas-*/ の親ディレクトリ
```

## 注意と限界

- ペルソナは合成された人口構成であり行動ログではない。すべてのスキルが結論を**「方向性の仮説」**として書き、実験での検証を強制する。
- 軽量シミュレーションは**mean-field近似**: 同調・硬化といった1次の社会効果は捉えるが、エコーチェンバー・伝播力学といった構造効果は範囲外。
- エージェント定義のデフォルトは`model: opus` — `.claude/agents/*.md`で変更可能。

## ライセンス

コード: [MIT](LICENSE)。ライトデータセット: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)、NVIDIA Nemotron-Personas(© NVIDIA, CC-BY-4.0)の派生 — 帰属表示の詳細はデータセットカードを参照。
