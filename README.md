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
