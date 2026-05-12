const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  
  await page.goto('http://www.饭太硬.com/tv', {waitUntil: 'networkidle2', timeout: 15000});
  await new Promise(r => setTimeout(r, 2000));
  
  // Extract all data from page
  const pageData = await page.evaluate(() => {
    // Find all script contents
    const scripts = Array.from(document.querySelectorAll('script'));
    const scriptContent = scripts.map(s => {
      if (s.src) return {type: 'ext', src: s.src};
      if (s.textContent && s.textContent.trim()) return {type: 'inline', content: s.textContent.substring(0, 5000)};
      return null;
    }).filter(x => x);
    
    // Get all HTML content as string
    const html = document.documentElement.outerHTML;
    
    // Find JSON-like data in window variables
    const windowVars = [];
    for (let key in window) {
      try {
        if (typeof window[key] === 'object' && window[key] !== null) {
          const val = JSON.stringify(window[key]);
          if (val && val.length > 50 && val.length < 100000 && val.startsWith('{')) {
            windowVars.push({key, preview: val.substring(0, 300)});
          }
        }
      } catch(e) {}
    }
    
    // Find any JSON data in page source
    const jsonPatterns = [];
    const scriptMatches = html.match(/\"sites\"\s*:\s*\[/g);
    if (scriptMatches) scriptMatches.forEach(m => {
      const idx = html.indexOf(m);
      jsonPatterns.push(html.substring(idx, idx+200));
    });
    
    // Get text content
    const text = document.body.innerText;
    
    return {scriptContent, windowVars, jsonPatterns, textPreview: text.substring(0, 1000), htmlLength: html.length};
  });
  
  console.log('HTML length:', pageData.htmlLength);
  console.log('\nWindow vars found:', pageData.windowVars.length);
  pageData.windowVars.forEach((v, i) => console.log(i + ':', v.key, '->', v.preview));
  
  console.log('\nJSON patterns found:');
  pageData.jsonPatterns.forEach(p => console.log(p));
  
  console.log('\nText preview:');
  console.log(pageData.textPreview);
  
  await browser.close();
})().catch(e => console.log('Error:', e.message));