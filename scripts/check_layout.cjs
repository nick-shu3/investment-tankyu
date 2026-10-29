const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');
(async () => {
  const root = path.resolve('_site');
  const server = http.createServer((req,res) => {
    const url = new URL(req.url, 'http://localhost');
    let pathname = decodeURIComponent(url.pathname).replace(/^\/investment-tankyu(?=\/)/,'');
    let file = path.join(root, pathname);
    if (!file.startsWith(root + path.sep) && file !== root) {res.writeHead(403).end();return;}
    if (pathname.endsWith('/')) file = path.join(file, 'index.html');
    if (!fs.existsSync(file)) {res.writeHead(404).end();return;}
    res.setHeader('Content-Type',file.endsWith('.css')?'text/css':'text/html; charset=utf-8');
    res.end(fs.readFileSync(file));
  }).listen(8765, '127.0.0.1');
  const browser = await chromium.launch();
  try {
    fs.mkdirSync('qa-screenshots',{recursive:true});
    const articles = fs.readdirSync('_articles').filter(f=>f.endsWith('.md'));
    for (const width of [390,1280]) {
      const page = await browser.newPage({viewport:{width,height:900}});
      const failed=[];
      page.on('response', r=>{if(r.status()>=400) failed.push(`${r.status()} ${r.url()}`)});
      for (const slug of ['index','companies',...articles.map(f=>f.slice(0,-3))]) {
        await page.goto('http://127.0.0.1:8765/investment-tankyu/'+(slug==='index'?'':slug==='companies'?'companies.html':'articles/'+slug+'.html'));
        await page.evaluate(()=>document.fonts.ready);
        const overflow = await page.evaluate(()=>document.documentElement.scrollWidth > innerWidth+1);
        if (overflow) throw Error(`Page overflow: ${width} ${slug}`);
        const tables = page.locator('.article-body table');
        for(let i=0;i<await tables.count();i++) {
          if(!await tables.nth(i).locator('th').count()) throw Error(`No table headers: ${slug}`);
        }
        await page.screenshot({path:`qa-screenshots/${slug}-${width}.png`,fullPage:true});
        await page.keyboard.press('Tab');
        if (!await page.locator('a:focus').count()) throw Error(`Keyboard focus missing: ${slug}`);
      }
      if(failed.length) throw Error(failed.join('\n'));
      await page.close();
    }
    console.log(`PASS: ${articles.length + 2} pages at 390px and 1280px; no page overflow, no HTTP errors, table headers and keyboard focus`);
  } finally { await browser.close(); server.close(); }
})().catch(e=>{console.error(e);process.exit(1)});
