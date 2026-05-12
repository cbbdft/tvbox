const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  
  // Intercept all XHR and fetch requests
  const xhrRequests = [];
  page.on('request', req => {
    const url = req.url();
    if (req.resourceType() === 'xhr' || req.resourceType() === 'fetch' || req.resourceType() === 'script') {
      xhrRequests.push({url, method: req.method()});
    }
  });
  page.on('response', async resp => {
    try {
      const url = resp.url();
      if (resp.headers()['content-type'] && resp.headers()['content-type'].includes('json')) {
        const body = await resp.text();
        console.log('JSON RESP from:', url.substring(0, 150));
        console.log('Body preview:', body.substring(0, 500));
        console.log('---');
      }
    } catch(e) {}
  });
  
  await page.goto('http://www.饭太硬.com/tv', {waitUntil: 'networkidle2', timeout: 15000});
  await new Promise(r => setTimeout(r, 3000));
  
  // Look for data in page DOM
  const domData = await page.evaluate(() => {
    // Find elements with copy-btn class
    const btns = Array.from(document.querySelectorAll('.copy-btn'));
    return btns.map(btn => {
      const rect = btn.getBoundingClientRect();
      // Get preceding text node sibling or nearby text
      let prevText = '';
      if (btn.previousSibling) prevText = btn.previousSibling.textContent || '';
      return {
        id: btn.id,
        text: btn.innerText,
        dataUrl: btn.getAttribute('data-url') || btn.getAttribute('data-api') || '',
        href: btn.getAttribute('href') || '',
        prevText: prevText.trim()
      };
    });
  });
  
  console.log('DOM data:', JSON.stringify(domData, null, 2));
  
  // Also check for hidden elements
  const hiddenData = await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('[data-url], [data-api], [data-key], [data-src]'));
    return all.map(el => ({
      tag: el.tagName,
      cls: el.className,
      id: el.id,
      attrs: {
        dataUrl: el.getAttribute('data-url'),
        dataApi: el.getAttribute('data-api'),
        dataKey: el.getAttribute('data-key'),
        dataSrc: el.getAttribute('data-src')
      },
      text: el.innerText ? el.innerText.substring(0, 100) : ''
    }));
  });
  
  console.log('Hidden data elements:', JSON.stringify(hiddenData, null, 2));
  
  await browser.close();
})().catch(e => console.log('Error:', e.message));