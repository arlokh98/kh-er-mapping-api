const ENABLE_LOGGING = true;
const API_URLS = {
  extractAllCategories: "https://color-extraction-api.onrender.com/extract_all_categories",
  arrowCheckBulk: "https://color-extraction-api.onrender.com/arrow_check_bulk",
  cropAllDecisionIcons: "https://color-extraction-api.onrender.com/crop_all_decision_icons"
};

const pathRanges = [
  "AA3:AB3", "U8:V8", "AG8:AH8", "O13:P13", "AA13:AB13", "AM13:AN13",
  "I18:J18", "U18:V18", "AG18:AH18", "AS18:AT18", "C23:D23", "O23:P23",
  "AA23:AB23", "AM23:AN23", "AY23:AZ23", "I28:J28", "U28:V28", "AG28:AH28",
  "AS28:AT28", "O33:P33", "AA33:AB33", "AM33:AN33", "U38:V38", "AG38:AH38",
  "AA43:AB43"
];
const lostMapRanges = [
  "AE8:AF8", "Y13:Z13", "AK13:AL13", "S18:T18", "AE18:AF18", "AQ18:AR18",
  "M23:N23", "Y23:Z23", "AK23:AL23", "AW23:AX23", "G28:H28", "S28:T28",
  "AE28:AF28", "AQ28:AR28", "BC28:BD28", "M33:N33", "Y33:Z33", "AK33:AL33",
  "AW33:AX33", "S38:T38", "AE38:AF38", "AQ38:AR38", "Y43:Z43", "AK43:AL43",
  "AE48:AF48"
];
const pathCheckboxes = [
    "AA5:AA6","U10:U11","AG10:AG11","O15:O16","AA15:AA16","AM15:AM16",
    "I20:I21","U20:U21","AG20:AG21","AS20:AS21","C25:C26","O25:O26",
    "AA25:AA26","AM25:AM26","AY25:AY26","I30:I31","U30:U31","AG30:AG31",
    "AS30:AS31","O35:O36","AA35:AA36","AM35:AM36","U40:U41","AG40:AG41",
    "AA45:AA46","AF5:AF6","Z10:Z11","T15:T16","AF15:AF16","AR15:AR16",
    "N20:N21","Z20:Z21","AL20:AL21","AX20:AX21","H25:H26","T25:T26",
    "AF25:AF26","AR25:AR26","BD25:BD26","N30:N31","Z30:Z31","AL30:AL31",
    "AX30:AX31","T35:T36","AF35:AF36","AR35:AR36","Z40:Z41","AL40:AL41",
    "AF45:AF46","AL10:AL11"
];
const layout = {
  leftIconCells: [
    "AB5:AC6", "V10:W11", "AH10:AI11", "P15:Q16", "AB15:AC16", "AN15:AO16",
    "J20:K21", "V20:W21", "AH20:AI21", "AT20:AU21", "D25:E26", "P25:Q26",
    "AB25:AC26", "AN25:AO26", "AZ25:BA26", "J30:K31", "V30:W31", "AH30:AI31",
    "AT30:AU31", "P35:Q36", "AB35:AC36", "AN35:AO36", "V40:W41", "AH40:AI41",
    "AB45:AC46"
  ],
  rightIconCells: [
    "AD5:AE6", "X10:Y11", "AJ10:AK11", "R15:S16", "AD15:AE16", "AP15:AQ16",
    "L20:M21", "X20:Y21", "AJ20:AK21", "AV20:AW21", "F25:G26", "R25:S26",
    "AD25:AE26", "AP25:AQ26", "BB25:BC26", "L30:M31", "X30:Y31", "AJ30:AK31",
    "AV30:AW31", "R35:S36", "AD35:AE36", "AP35:AQ36", "X40:Y41", "AJ40:AK41",
    "AD45:AE46"
  ]
};
const realmMapping = {
    "Realm 1": { backend: "R1 backend", urlCell: "F7" },
    "Realm 2": { backend: "R2 backend", urlCell: "K9" },
    "Realm 3": { backend: "R3 backend", urlCell: "F11" },
    "Realm 4": { backend: "R4 backend", urlCell: "K13" },
    "Realm 5": { backend: "R5 backend", urlCell: "F15" },
    "Realm 6": { backend: "R6 backend", urlCell: "K17" },
    "Realm 7": { backend: "R7 backend", urlCell: "F19" }
};

function log(message) {
  if (ENABLE_LOGGING) Logger.log(message);
}
function getBackendSheet(sheetName) {
  return SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName.replace("Realm ", "R") + " backend");
}
function clearRanges(sheet, ranges) {
  ranges.forEach(range => sheet.getRange(range).clearContent());
}
function insertImage(sheet, rangeA1, base64, id) {
  const tag = `ICON_${id}`;
  const blob = Utilities.newBlob(Utilities.base64Decode(base64), 'image/png', 'icon.png');
  const cell = sheet.getRange(rangeA1);
  const merged = cell.getMergedRanges()[0] || cell;
  const image = sheet.insertImage(blob, merged.getColumn(), merged.getRow());
  image.setWidth(30).setHeight(30);
  image.setAltTextTitle(tag);

  const props = PropertiesService.getScriptProperties();
  const ids = JSON.parse(props.getProperty("ICON_IDS") || "[]");
  ids.push(tag);
  props.setProperty("ICON_IDS", JSON.stringify(ids));
}
function getImageUrlForSheet(sheetName) {
  const realmMapping = {
    "Realm 1": "F7", "Realm 2": "K9", "Realm 3": "F11", "Realm 4": "K13",
    "Realm 5": "F15", "Realm 6": "K17", "Realm 7": "F19"
  };
  const range = realmMapping[sheetName];
  return range ? SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Landing").getRange(range).getValue() : "";
}

function clearMapAndImages(sheetName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);
  const backendSheet = getBackendSheet(sheetName);
  const props = PropertiesService.getScriptProperties();
  const tracked = JSON.parse(props.getProperty("ICON_IDS") || "[]");

  if (backendSheet) {
    clearRanges(backendSheet, ["C2:C26", "E2:F26", "H2:I26", "Z2:AB26"]);
  }
  clearRanges(sheet, ["I1", "C2"]);

  const images = sheet.getImages();
  let removed = 0;
  images.forEach(img => {
    const alt = img.getAltTextTitle();
    if (tracked.includes(alt)) {
      img.remove();
      removed++;
    }
  });
  props.deleteProperty("ICON_IDS");
  log(`✅ Removed ${removed} tracked images from ${sheetName}`);

  pathRanges.forEach(range => sheet.getRange(range).clearContent());
  lostMapRanges.forEach(range => sheet.getRange(range).clearContent());
  pathCheckboxes.forEach(range => sheet.getRange(range).setValue(false));
}
function pathClear(sheetName) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  if (!sheet) return;

  pathRanges.forEach(range => sheet.getRange(range).clearContent());
  lostMapRanges.forEach(range => sheet.getRange(range).clearContent());
  pathCheckboxes.forEach(range => sheet.getRange(range).setValue(false));
}
function resetAllRealms() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const realmSheets = ss.getSheets().filter(s => s.getName().startsWith("Realm "));
  realmSheets.forEach(sheet => clearMapAndImages(sheet.getName()));
}

function checkAndFormatLandingSheet() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Landing");
  if (!sheet) return;

  const targetCells = ["F7","K9","F11","K13","F15","K17","F19"];
  targetCells.forEach(cell => {
    const range = sheet.getRange(cell);
    const mergedRange = range.getMergedRanges()[0] || range;
    let value = mergedRange.getValue().toString().trim();

    if (value === "") {
      mergedRange.setValue("Coming soon...");
      value = "Coming soon...";
    }

    // Check if it's a link
    const isLink = value.includes("http");

    if (isLink) {
      mergedRange.setFontLine("underline");
      mergedRange.setHorizontalAlignment("left");  // Links are always left-aligned
    } else {
      mergedRange.setFontLine("none");
      mergedRange.setHorizontalAlignment(cell.startsWith("F") ? "left" : "right");
    }
  });
}
function onEdit(e) {
  const sheet = e.source.getActiveSheet();
  const range = e.range;
  const sheetName = sheet.getName();

  // B42 triggers clearMapAndImages
  if (range.getA1Notation() === "B51" && range.getValue() === true) {
    clearMapAndImages(sheetName);
    range.setValue(false);
  }

  // B43 triggers pathClear
  if (range.getA1Notation() === "B52" && range.getValue() === true) {
    pathClear(sheetName);
    range.setValue(false);
  }

  if (sheetName === "Landing") {
    checkAndFormatLandingSheet();
  }
  if (sheet.getName() === "Landing" && range.getA1Notation() === "B23" && range.getValue() === true) {
    resetAllRealms();
    range.setValue(false);
  }
}

function insertBase64ImageToMergedCell(sheet, mergedRangeA1, base64String, imageId = "", ids = []) {
  if (!base64String || base64String.length < 50) {
    Logger.log(`⚠️ Skipping empty/invalid base64 image: ${imageId}`);
    return;
  }

  const range = sheet.getRange(mergedRangeA1);
  const mergedRanges = range.getMergedRanges();
  const targetRange = mergedRanges.length > 0 ? mergedRanges[0] : range;

  const startRow = targetRange.getRow();
  const startCol = targetRange.getColumn();

  try {
    const decoded = Utilities.base64Decode(base64String);
    const blob = Utilities.newBlob(decoded, 'image/png', 'icon.png');
    const image = sheet.insertImage(blob, startCol, startRow);
    image.setWidth(30).setHeight(30);

    const tag = `ICON_${imageId}`;
    image.setAltTextTitle(tag);

    // Track per sheet name
    const props = PropertiesService.getScriptProperties();
    const sheetKey = `ICON_IDS_${sheet.getName()}`;
    const tracked = JSON.parse(props.getProperty(sheetKey) || "[]");
    tracked.push(tag);
    props.setProperty(sheetKey, JSON.stringify(tracked));
    ids.push(tag); // optional: track in session for use elsewhere

  } catch (e) {
    Logger.log(`❌ Failed to insert image ${imageId}: ${e}`);
  }
}

function processIslandCategoriesToBackend(sheetName, imageUrl) {
  const backendSheet = getBackendSheet(sheetName);
  if (!backendSheet || !imageUrl) return;

  const response = UrlFetchApp.fetch(API_URLS.extractAllCategories, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({ image_url: imageUrl }),
    muteHttpExceptions: true
  });

  const result = JSON.parse(response.getContentText());
  if (!result.island_data || result.island_data.length !== 25) return;

  const types = result.island_data.map(d => [d.island_type || ""]);
  const cats = result.island_data.map(d => [d.category || ""]);

  backendSheet.getRange(2, 26, 25, 1).setValues(types); // Col Z
  backendSheet.getRange(2, 3, 25, 1).setValues(cats);   // Col C
}
function arrowCheckBulk(sheet, imageUrl) {
  const response = UrlFetchApp.fetch(API_URLS.arrowCheckBulk, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({ image_url: imageUrl }),
    muteHttpExceptions: true
  });
  const result = JSON.parse(response.getContentText());
  if (!result.A || !result.D) return;

  result.A.forEach((row, i) => {
    sheet.getRange(i + 2, 5).setValue(row[0] === "skip" ? "" : row[0]);
    sheet.getRange(i + 2, 6).setValue(row[1] === "skip" ? "" : row[1]);
  });
  result.D.forEach((row, i) => {
    sheet.getRange(i + 2, 8).setValue(row[0] === "skip" ? "" : row[0]);
    sheet.getRange(i + 2, 9).setValue(row[1] === "skip" ? "" : row[1]);
  });
}
function populateDecisionIcons(imageUrl, realmSheet) {
  const backendSheet = getBackendSheet(realmSheet.getName());
  const categories = backendSheet.getRange("C2:C26").getValues().flat();
  const ids = [];
  const response = UrlFetchApp.fetch(API_URLS.cropAllDecisionIcons, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({ image_url: imageUrl, categories }),
    muteHttpExceptions: true
  });
  const result = JSON.parse(response.getContentText());
  if (!result.icons || result.icons.length !== 25) return;

  const labels = result.icons.map(i => [i.left.label, i.right.label]);
  backendSheet.getRange("AA2:AB26").setValues(labels);

  result.icons.forEach((i, idx) => {
    if (i.left.base64) insertImage(realmSheet, layout.leftIconCells[idx], i.left.base64, i.left.id);
    if (i.right.base64) insertImage(realmSheet, layout.rightIconCells[idx], i.right.base64, i.right.id);
  });
}

function getMapAndProcessAll() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  const sheetName = sheet.getName();
  const backend = getBackendSheet(sheetName);
  const url = getImageUrlForSheet(sheetName);

  if (!backend || !url) return;

  processIslandCategoriesToBackend(sheetName, url);
  arrowCheckBulk(backend, url);
  populateDecisionIcons(url, sheet);
}