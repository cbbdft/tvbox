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
  
  // Get ALL copy-btn data attributes
  const allBtns = await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('.copy-btn'));
    return btns.map((btn, i) => {
      const parent = btn.parentElement;
      const grandParent = parent ? parent.parentElement : null;
      return {
        index: i,
        id: btn.id,
        text: btn.innerText.trim(),
        dataClipboardText: btn.getAttribute('data-clipboard-text'),
        parentClass: parent ? parent.className : null,
        grandParentClass: grandParent ? grandParent.className : null,
        // Get all data attributes on the parent items
        parentDataAttrs: parent ? JSON.stringify(Array.from(parent.attributes).map(a => ({name: a.name, value: a.value}))) : null
      };
    });
  });
  
  console.log('All copy buttons:');
  allBtns.forEach(b => {
    console.log('[' + b.index + '] text=' + b.text + ' id=' + b.id + ' clipboard=' + b.dataClipboardText + ' parentClass=' + b.parentClass);
  });
  
  // Also get the full list of all unique copy URLs
  const allUrls = await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('.copy-btn'));
    const urls = {};
    btns.forEach(btn => {
      const txt = btn.getAttribute('data-clipboard-text');
      if (txt && txt.startsWith('http')) {
        urls[txt] = (urls[txt] || 0) + 1;
      }
    });
    return urls;
  });
  
  console.log('\nAll copy URLs:');
  Object.keys(allUrls).forEach(u => console.log(u + ' (x' + allUrls[u] + ')'));
  
  await browser.close();
})().catch(e => console.log('Error:', e.message));