import puppeteer from 'puppeteer';

(async () => {
    const browser = await puppeteer.launch({ headless: 'new' });
    const page = await browser.newPage();
    const client = await page.target().createCDPSession();
    await client.send('Page.setDownloadBehavior', {
        behavior: 'allow',
        downloadPath: './downloads',
    });

    // We need to login first
    await page.goto('http://localhost:5173/login');
    await page.type('input[type="email"]', 'kavita.ramdhave@paccar.com');
    await page.type('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');
    await page.waitForNavigation();
    
    // Go to the attempt result
    await page.goto('http://localhost:5173/attempts/b71e59ae-62d4-4014-975b-8caecda173da/result', { waitUntil: 'networkidle2' });
    
    console.log('Page loaded. Clicking download...');
    
    // capture console logs
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    
    // Click download
    await page.evaluate(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const dlBtn = btns.find(b => b.textContent.includes('Download PDF'));
        if (dlBtn) dlBtn.click();
        else console.log('Download button not found!');
    });
    
    await new Promise(r => setTimeout(r, 5000));
    console.log('Check complete.');
    await browser.close();
})();
