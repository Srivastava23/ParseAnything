const fs = require('fs');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;
const html = fs.readFileSync('ui/index.html', 'utf8');
const dom = new JSDOM(html, { runScripts: "dangerously" });
if (dom.window.document.errors) {
    console.log(dom.window.document.errors);
}
console.log("No syntax errors found.");
