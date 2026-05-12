const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.210 Mobile Safari/537.36');
  
  // Capture all requests to find the actual TV source API
  const allResponses = [];
  page.on('response', async resp => {
    try {
      const url = resp.url();
      const ct = resp.headers()['content-type'] || '';
      const status = resp.status();
      if (ct.includes('json') || status === 200 || status === 301 || status === 302) {
        const text = await resp.text().catch(() => '');
        allResponses.push({url: url.substring(0, 200), status, ct: ct.substring(0, 60), textPreview: text.substring(0, 300)});
      }
    } catch(e) {}
  });
  
  await page.goto('http://www.饭太硬.com/tv', {waitUntil: 'networkidle2', timeout: 15000});
  await new Promise(r => setTimeout(r, 3000));
  
  console.log('All responses:');
  allResponses.forEach(r => {
    console.log('URL: ' + r.url);
    console.log('Status: ' + r.status + ', CT: ' + r.ct);
    if (r.textPreview) console.log('Text: ' + r.textPreview);
    console.log('---');
  });
  
  await browser.close();
})().catch(e => console.log('Error:', e.message));