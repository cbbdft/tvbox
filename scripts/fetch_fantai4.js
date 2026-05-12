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
  
  // Check what element has id="yunxing"
  const yunxingEl = await page.evaluate(() => {
    const el = document.getElementById('yunxing');
    if (!el) return null;
    // Check if it's inside some other element with the URL
    const outerHTML = el.outerHTML;
    const parent = el.parentElement;
    const grandParent = parent ? parent.parentElement : null;
    return {
      outerHTML,
      parentTag: parent ? parent.tagName : null,
      parentHTML: parent ? parent.outerHTML.substring(0, 500) : null,
      grandParentHTML: grandParent ? grandParent.outerHTML.substring(0, 500) : null
    };
  });
  
  console.log('yunxing element:', JSON.stringify(yunxingEl, null, 2));
  
  // Get full page source
  const fullHTML = await page.evaluate(() => document.documentElement.outerHTML);
  
  // Find the surrounding context of yunxing in the HTML
  const yunxingIdx = fullHTML.indexOf('id="yunxing"');
  if (yunxingIdx >= 0) {
    console.log('\n=== HTML around yunxing ===');
    console.log(fullHTML.substring(Math.max(0, yunxingIdx - 500), yunxingIdx + 300));
  }
  
  // Search for any URL patterns near yunxing
  const urlPatternNearYunxing = fullHTML.match(/https?:\/\/[^\s"'<>]+/g);
  console.log('\nAll URLs in HTML:');
  if (urlPatternNearYunxing) {
    urlPatternNearYunxing.forEach(u => console.log(u.substring(0, 200)));
  }
  
  // Also check - maybe there's an adjacent element with the URL
  const adjacentURL = await page.evaluate(() => {
    const yunxingEl = document.getElementById('yunxing');
    if (!yunxingEl) return null;
    // Check for a sibling or nearby element
    let sibling = yunxingEl.nextElementSibling;
    if (sibling) console.log('Next sibling:', sibling.tagName, sibling.className, sibling.innerText);
    let parent = yunxingEl.parentElement;
    if (parent) {
      console.log('Parent:', parent.tagName, parent.className);
      // Get all children of parent
      const children = Array.from(parent.children).map(c => c.tagName + '.' + c.className + ':' + c.innerText.substring(0, 50));
      console.log('Parent children:', children);
    }
    return null;
  });
  
  await browser.close();
})().catch(e => console.log('Error:', e.message));