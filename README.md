# 投資探究

企業決算を公式資料から読み、分析の変化を蓄積する閲覧専用サイト。GitHub Pages標準のJekyllを使用します。

## 更新手順

1. `_articles/` のMarkdownで記事を作成・改訂します。`company_id` は `_data/companies.json` のidと一致させます。
2. `published`（公開日）を維持し、改訂時は `updated` と本文の更新履歴を変更します。日付は引用符付きの YYYY-MM-DD。`announcement` は決算発表日です。
3. `conclusions` はトップと本文の要約、`segments` は図表と当期数値の管理元です。単位は億ドル。図の表示上限を超える場合は `_includes/segment-chart.html` の目盛り・説明・倍率を揃えて改訂します。
4. 出典の表・注記、数値、対象期間、独自計算式を照合し、変更を作業ブランチへ登録します。
5. 差分確認後mainに反映し、Pagesのビルド・公開・表示を確認します。

新しい決算は別記事にします。事実、会社の見通し、AI分析、本人の考察を区別し、本人の言葉を創作しません。未確認事項と未実施の株価評価は明記します。

記事一覧と公開済み・更新予定の銘柄数はMarkdownと企業データから自動生成します。企業データのtypeは日本株・米国株・ETF・J-REITを使用します。

## 公開と検証

Settings → Pages → Deploy from a branch → main / (root)。baseurlは `/investment-tankyu`。

ローカルでJekyllが利用できる場合は `jekyll build --baseurl /investment-tankyu`。公開後はトップ・記事・CSS・目次・出典を確認し、スマートフォンで表以外に横はみ出しがないこと、キーボードでリンクへ移動できることを確認します。

公開リポジトリでは全ファイルと変更履歴を閲覧できます。個人の保有数量、取得単価、損益、資産額、取引履歴、非公開メモを登録しないでください。

## 公開対象ポリシー（必須）

IDホールディングス（4709、id-holdings）は公開対象外です。再追加は本人による明示的な方針変更がない限り禁止します。保有リストの受領や全銘柄の一括更新依頼だけでは、この除外を解除しません。銘柄一覧、記事、更新予定、決算カレンダー、図表の全てが対象です。機械可読の除外指定は `_data/publication_policy.json` で管理します。

更新・公開前に `python3 scripts/validate_publication.py` を必ず実行してください。

## 決算カレンダー

`_data/earnings_calendar.json` のeventsで管理します。company_idは公開銘柄データに存在する必要があります。statusはscheduled（公式の日付付き予定）、month_only（公式の月のみ）、unknown（次回日程未確認）、fund（ETF別扱い）。scheduledにはdate（YYYY-MM-DD）、period、source、checkedが必須です。時刻は確認できた場合のみタイムゾーンを明記します。説明会、配当、決算期末を決算発表と混同しません。

as_ofは日程の確認基準日です。表示はその日時点のスナップショットで、自動収集・自動実績判定は行いません。更新時は過ぎた予定を発表済みと推定せず、公式実績を確認して整理し、as_ofとcheckedを更新してください。確認前の過去日を新しい予定表へ持ち越すことは検証スクリプトが拒否します。
