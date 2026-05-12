const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  
  // Capture all network requests
  page.on('request', req => {
    const url = req.url();
    if (!url.includes('google-analytics') && !url.includes('gtag')) {
      console.log('REQ:', req.method(), url.substring(0, 150));
    }
  });
  page.on('response', async resp => {
    try {
      const url = resp.url();
      if (!url.includes('google-analytics') && !url.includes('xn--sss604efuw.com/z/css')) {
        const ct = resp.headers()['content-type'] || '';
        console.log('RESP:', resp.status(), url.substring(0, 150), ct.substring(0, 40));
      }
    } catch(e) {}
  });
  
  await page.goto('http://www.饭太硬.com/tv', {waitUntil: 'networkidle2', timeout: 15000});
  await new Promise(r => setTimeout(r, 2000));
  
  // Find all copy buttons
  const copyBtns = await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('.copy-btn'));
    return btns.map(b => ({text: b.innerText, id: b.id}));
  });
  console.log('Copy buttons found:', JSON.stringify(copyBtns));
  
  // Try clicking the first one to see what happens
  const firstBtn = await page.$('.copy-btn');
  if (firstBtn) {
    await firstBtn.click();
    await new Promise(r => setTimeout(r, 2000));
  }
  
  // Check what's in the page HTML - look for data
  const html = await page.content();
  
  // Look for site data
  const siteMatch = html.match(/\"sites\"\s*:\s*\[/);
  if (siteMatch) {
    const idx = siteMatch.index;
    console.log('Found sites at:', idx);
    console.log(html.substring(idx, idx+500));
  }
  
  // Look for api calls in any inline JS
  const apiMatch = html.match(/api[Uu]rl\s*[:=]\s*[\"\']([^\"\']+)[\"\']/);
  if (apiMatch) console.log('API URL found:', apiMatch[1]);
  
  console.log('\\nDone');
  await browser.close();
})().catch(e => console.log('Error:', e.message));