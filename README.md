# 投資探究 — GitHub Pages 検討版

新しい公開リポジトリ（例 investment-tankyu）のルートに配置する案です。既存のサイトは変更していません。Settings → Pages → Build and deployment → Deploy from a branch → main / (root) を選択すると、GitHub Pages標準のJekyllでMarkdownをHTMLへ生成します。URLは https://<ユーザー名>.github.io/<リポジトリ名>/ の形式です。初回の実際のビルドを確認してください。

## 記事の追加

`_articles/` のMarkdownをコピーし、タイトル、company_id、period、published（引用符付きの YYYY-MM-DD）、summary、rating、review_status と本文を更新します。company_id は `_data/companies.json` のidと一致させてください。mainへ反映されると記事一覧と各企業の最新記事リンクが更新されます。同日の記事順は保証されません。企業一覧は `_data/companies.json` で管理します。

公開リポジトリの全ファイルや変更履歴は閲覧可能です。保有株数、取得単価、評価損益、非公開のメモや下書きは登録しないでください。投稿前に一次資料と個人情報を確認してください。
