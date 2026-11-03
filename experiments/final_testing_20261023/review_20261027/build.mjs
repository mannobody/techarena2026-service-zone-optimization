import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const dir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(dir, '../../..');
const outputDir = path.join(root, 'outputs/results-table');
const data = JSON.parse(await fs.readFile(path.join(dir, 'verified_data.json'), 'utf8'));
const wb = Workbook.create();
const main = wb.worksheets.add('Сравнение');
const source = wb.worksheets.add('Источники');
const records = data.source_records;
const colors = {navy:'#18344B', blue:'#335F8A', ink:'#243746', muted:'#607180', pale:'#F1F5F8', white:'#FFFFFF'};
const cell = (sheet, address, value) => {sheet.getRange(address).values = [[value]];};
const formula = (sheet, address, value) => {sheet.getRange(address).formulas = [[value]];};
const near = (a,b,tolerance=1e-9) => {
  if (typeof a !== 'number' || Math.abs(a-b)>tolerance) throw new Error(`Mismatch: ${a} versus ${b}`);
};
for (const s of [main,source]) {
  s.showGridLines = false;
  s.getRange(s===main?'A1:G34':'A1:H31').format.font = {name:'Arial',size:11,color:colors.ink};
  s.getRange(s===main?'A1:G34':'A1:H31').format.rowHeight = 24;
  s.getRange(s===main?'A1:G34':'A1:H31').format.verticalAlignment = 'center';
}
main.tabColor = colors.navy;
source.tabColor = colors.blue;
// One row per test; missing values in the cropped screenshot remain blank.
source.getRange('A4:H4').values = [['Тест',...records.map(r=>r.label)]];
source.getRange('A5:H16').values = Array.from({length:12},(_,i)=>[i+1,...records.map(r=>i<r.values.length?Number(r.values[i]):null)]);
source.getRange('B5:H16').setNumberFormat('#,##0.00');
source.getRange('A1:A31').format.columnWidth = 8;
source.getRange('B1:H31').format.columnWidth = 23;
source.getRange('A2').values = [['Исходные результаты со скриншотов']];
source.getRange('A2').format.font = {name:'Arial',size:16,bold:true,color:colors.navy};
cell(source,'A3','6 полных строк по 12 тестов и один читаемый фрагмент №1–3.');
source.getRange('A3').format.font = {name:'Arial',size:11,italic:true,color:colors.muted};
source.getRange('A20:C20').values = [['Колонка','Результат','Файл скриншота']];
source.getRange('A21:C27').values = records.map((r,i)=>[String.fromCharCode(66+i),r.label,r.screenshot]);
cell(source,'A29','Фрагмент: №1 = 0,00 (T); №2 и №3 — A. Не видимые №4–12 оставлены пустыми.');
cell(source,'A30','Нижние строки с 33 прогонами исключены: другой набор тестов.');
cell(source,'A31','Даты обозначают присланные скриншоты. Названия команд для неназванных посылок неизвестны.');
source.getRange('A29:H31').format.font = {name:'Arial',size:11,color:colors.muted};
source.freezePanes.freezeColumns(1);

main.getRange('A1:A34').format.columnWidth = 8;
main.getRange('B1:C34').format.columnWidth = 23;
main.getRange('D1:D34').format.columnWidth = 17;
main.getRange('E1:E34').format.columnWidth = 23;
main.getRange('F1:F34').format.columnWidth = 18;
main.getRange('G1:G34').format.columnWidth = 25;
cell(main,'A2','Итоговые результаты и известные максимумы');
main.getRange('A2').format.font = {name:'Arial',size:16,bold:true,color:colors.navy};
cell(main,'A3','Сверено 27.10.2026. Максимумы только среди предоставленных результатов; остальные участники неизвестны.');
main.getRange('A3').format.font = {name:'Arial',size:11,italic:true,color:colors.muted};
cell(main,'A4','Наш скор');
formula(main,'B4','=C25');
cell(main,'C4','С отставанием');
formula(main,'D4','=COUNTIFS(E8:E19,">0")');
cell(main,'E4','На максимуме');
formula(main,'F4','=COUNTIFS(E8:E19,"=0")');
main.getRange('B4').setNumberFormat('0.000000');
for (const address of ['B4','D4','F4']) main.getRange(address).format.font = {name:'Arial',size:14,bold:true,color:colors.navy};
for (const address of ['C4','E4']) main.getRange(address).format.horizontalAlignment = 'center';
cell(main,'A5','Отставание, % = (максимум − наш результат) / максимум.');
main.getRange('A5').format.font = {name:'Arial',size:11,color:colors.muted};
main.getRange('A7:G7').values = [['Тест','Наш результат','Известный максимум','Наш / максимум','Отставание, ед.','Отставание, %','Источник максимума']];
for (let i=0;i<12;i++) {
  const r=8+i,sr=5+i;
  main.getRange(`A${r}:G${r}`).formulas = [[
    `='Источники'!A${sr}`,`='Источники'!B${sr}`,
    `=MAX('Источники'!B${sr}:H${sr})`,`=B${r}/C${r}`,
    `=C${r}-B${r}`,`=E${r}/C${r}`,
    `=INDEX('Источники'!$B$4:$H$4,1,MATCH(C${r},'Источники'!B${sr}:H${sr},0))`
  ]];
}
main.getRange('B8:C19').setNumberFormat('#,##0.00');
main.getRange('D8:D19').setNumberFormat('0.000000');
main.getRange('E8:E19').setNumberFormat('#,##0.00');
main.getRange('F8:F19').setNumberFormat('0.00%');
main.getRange('F8:F19').conditionalFormats.add('cellIs',{operator:'greaterThan',formula:0,format:{fill:'#FFF0D9',font:{color:'#8A4B08',bold:true}}});
cell(main,'A21','При равном максимуме указан первый источник в таблице. Все равенства сохранены в исходных данных.');
main.getRange('A21').format.font = {name:'Arial',size:11,color:colors.muted};
cell(main,'A22','Скоры полных результатов');
main.getRange('A22').format.font = {name:'Arial',size:14,bold:true,color:colors.navy};
main.getRange('A24:C24').values = [['Место','Результат','Скор из 12']];
data.ranking.forEach((key,index)=>{
  const r=25+index,recordIndex=records.findIndex(x=>x.key===key),col=String.fromCharCode(66+recordIndex);
  formula(main,`A${r}`,`=1+COUNTIFS($C$25:$C$30,">"&C${r})`);
  formula(main,`B${r}`,`='Источники'!${col}4`);
  const terms=Array.from({length:12},(_,i)=>`'Источники'!${col}${5+i}/$C$${8+i}`);
  formula(main,`C${r}`,key==='ours'?'=SUM(D8:D19)':`=SUM(${terms.join(',')})`);
});
main.getRange('C25:C30').setNumberFormat('0.000000');
main.getRange('A25:C25').format.font = {name:'Arial',size:11,bold:true,color:colors.navy};
cell(main,'A32','Неполный скриншот учитывается в максимумах, но не получает скор.');
cell(main,'A33','Изменения на листе «Источники» пересчитывают максимумы, скоры и места. Порядок строк сохраняется.');
main.getRange('A32:A33').format.font = {name:'Arial',size:11,color:colors.muted};

for (const [s,areas] of [[main,['A7:G7','A24:C24']],[source,['A4:H4','A20:C20']]]) {
  for(const address of areas) {
    const h=s.getRange(address);
    h.format.fill=colors.navy;
    h.format.font={name:'Arial',size:11,bold:true,color:colors.white};
    h.format.horizontalAlignment='center';
    h.format.verticalAlignment='center';
    h.format.rowHeight=34;
    h.format.wrapText=true;
  }
}
for (const [s,range] of [[main,'A8:G19'],[main,'A25:C30'],[source,'A5:H16']]) {
  s.getRange(range).format.borders={bottom:{style:'thin',color:'#D7E1E8'}};
}
main.getRange('A8:A19').format.horizontalAlignment='center';
main.getRange('A25:A30').format.horizontalAlignment='center';
main.getRange('B8:F19').format.horizontalAlignment='right';
main.getRange('G8:G19').format.horizontalAlignment='left';
source.getRange('B5:H16').format.horizontalAlignment='right';
source.getRange('A5:A16').format.horizontalAlignment='center';
source.getRange('A20:H27').format.rowHeight=25;

// Input-change checks are restored before final calculation and export.
wb.recalculate();
const saved = source.getRange('C5').values[0][0];
const ourScore = Number(data.scores.ours);
cell(source,'C5',Number(data.source_records[0].values[0])*2);
wb.recalculate();
near(main.getRange('D8').values[0][0],.5);
near(main.getRange('C25').values[0][0],ourScore-.5);
if(main.getRange('A25').values[0][0]===1)throw new Error('Rank did not react to new leader');
cell(source,'C5',saved);
cell(source,'H8',0);
wb.recalculate();
near(main.getRange('C11').values[0][0],Number(data.comparison[3].maximum),1e-6);
cell(source,'H8',null);
wb.recalculate();

for(let i=0;i<12;i++) {
  const r=8+i,x=data.comparison[i];
  near(main.getRange(`B${r}`).values[0][0],Number(x.ours),1e-6);
  near(main.getRange(`C${r}`).values[0][0],Number(x.maximum),1e-6);
  near(main.getRange(`D${r}`).values[0][0],Number(x.normalized));
  near(main.getRange(`E${r}`).values[0][0],Number(x.absolute_gap),1e-6);
  near(main.getRange(`F${r}`).values[0][0],Number(x.gap_fraction));
}
data.ranking.forEach((k,i)=>near(main.getRange(`C${25+i}`).values[0][0],Number(data.scores[k])));
near(main.getRange('D4').values[0][0],8);
near(main.getRange('F4').values[0][0],4);
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:100},maxChars:2500});
const inspection=await wb.inspect({kind:'table',range:'Сравнение!A7:G19',include:'values,formulas',tableMaxRows:13,tableMaxCols:7,maxChars:4500});
await fs.writeFile(path.join(dir,'workbook_inspection.json'),JSON.stringify({errors:errors.ndjson,table:inspection.ndjson},null,2));
for(const [sheetName,range,file]of [['Сравнение','A1:G34','comparison_preview.png'],['Источники','A1:H32','sources_preview.png']]){
  const preview=await wb.render({sheetName,range,scale:1,format:'png'});
  await fs.writeFile(path.join(dir,file),new Uint8Array(await preview.arrayBuffer()));
}
await fs.mkdir(outputDir,{recursive:true});
const target=path.join(outputDir,'Результаты_и_максимумы.xlsx');
const xlsx=await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(target);
await fs.writeFile(path.join(dir,'WORKBOOK_CHECK.json'),JSON.stringify({output:target,sourceScreenshots:7,readableValues:75,sourceDiscrepancies:data.source_differences.length,maximaDiscrepancies:data.maxima_differences.length,scoreDiscrepancies:data.score_differences.length,all12RowsMatchIndependentDecimal:true,all6ScoresMatchIndependentDecimal:true,rankAndMaxReactToChangedInput:true,blankAndZeroChecked:true,missingValuesRestored:true,engine:'Artifact Tool; native Excel not launched'},null,2));
console.log(JSON.stringify({output:target,scores:data.scores,errorScan:errors.ndjson}));
