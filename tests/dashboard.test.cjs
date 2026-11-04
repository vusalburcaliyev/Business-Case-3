const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const test = require('node:test');
const source = fs.readFileSync(path.join(__dirname,'../Sales_Dashboard.html'),'utf8')
  .match(/<script>([\s\S]*?)<\/script>/)[1];

function report() {
  const ids = Object.fromEntries(['year','metric','context','cards','channel-title','month-title',
    'channel-bars','month-bars','category','discount','findings'].map(id=>[id,{handlers:{},
    addEventListener(k,fn){this.handlers[k]=fn;}}]));
  ids.year.value='2013';
  ids.metric.value='sales_usd';
  vm.runInNewContext(source,{document:{getElementById:id=>ids[id]}});
  return ids;
}

test('2013 KPI and sensitivity outputs match the SQL results',()=>{
  const d=report();
  assert.match(d.cards.innerHTML,/24,661,612/);
  assert.match(d.cards.innerHTML,/8\.70%/);
  assert.match(d.findings.innerHTML,/40\.87%/);
  assert.match(d.category.innerHTML,/Accessories/);
});

test('the profit chart shows the reseller loss and changes when the year changes',()=>{
  const d=report();
  d.metric.value='profit_usd'; d.metric.handlers.change();
  assert.equal(d['channel-title'].textContent,'Gross profit by channel');
  assert.match(d['channel-bars'].innerHTML,/fill neg/);
  assert.match(d['channel-bars'].innerHTML,/153,306/);
  d.year.value='2012'; d.year.handlers.change();
  assert.doesNotMatch(d['channel-bars'].innerHTML,/fill neg/);
  assert.match(d['channel-bars'].innerHTML,/631,370/);
  assert.match(d.cards.innerHTML,/21,058,436/);
});
