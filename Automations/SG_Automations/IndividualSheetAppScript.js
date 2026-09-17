// ==============================================================================
// CONFIGURATION & MAPPING
// All column letters and cell targets are centralized here for easy maintenance.
// ==============================================================================
const CONFIG = {
  MASTER_SHEET_ID: "1lrJ6LuspTxZPHyxowQsZ-fWfgeUIkRSrvEvqNh8mOUU",
  TOKEN_CELL_INDIVIDUAL: "G3",
  DEFAULT_TOKEN_COL_MASTER: "C", // Default token column for most tabs

  PERSONAL_INFO: {
    SHEET_NAME: "Master Roster Contact Info",
    TOKEN_COL: "I", // Column I specifically for this tab
    TARGETS: {
      NAME_CELL: "B3",  // First (Col B) + Last (Col A)
      ID_CELL: "E3",    // Col D
      EMAIL_CELL: "B4", // Col E
      GRADE_CELL: "E4"  // Col C
    }
  },

  TOTAL_POINTS: {
    SHEET_NAME: "Overall Total Points",
    TOKEN_COL: "C",
    MASTER_COL: "E",
    TARGET_CELL: "B5"
  },

  FUNDRAISING: {
    SHEET_NAME: "Fundraising/Deposits",
    ROW: 9,
    COLS: {
      CARRY_OVER:     { masterCol: "E", targetCol: "A" },
      VERTICAL_RAISE: { masterCol: "F", targetCol: "B" },
      SEES:           { masterCol: "G", targetCol: "C" },
      FIRST_AID:      { masterCol: "H", targetCol: "D" },
      EMERGENCY_KITS: { masterCol: "I", targetCol: "E" },
      REMAINING:      { masterCol: "J", targetCol: "F" },
      USED:           { masterCol: "K", targetCol: "G" }
    }
  },

  CONFERENCE_PAYMENTS: {
    SHEET_NAME: "Fundraising/Deposits",
    CONFERENCES: {
      GMUNC:  { row: 13, p1: "O",  p2: "P",  appliedFR: "Q" },
      SMUNC:  { row: 14, p1: "S",  p2: "T",  appliedFR: "U" },
      PACMUN: { row: 15, p1: "W",  p2: "X",  appliedFR: "Y" },
      SCVMUN: { row: 16, p1: "AA",  p2: null, appliedFR: "AB" },
      NHSMUN: { row: 17, p1: "AC",  p2: "AD",  appliedFR: "AE" },
      RIMUN:  { row: 18, p1: "AG", p2: "AH", appliedFR: "AI" },
      BMUN:   { row: 19, p1: "AK", p2: "AL", appliedFR: "AM" },
      DMUNC:  { row: 20, p1: "AO", p2: "AP", appliedFR: "AQ" }
    }
  },

  AWARDS_ATTENDANCE: {
    SHEET_NAME: "Conference Attd/Award",
    CONFERENCES: {
      GMUNC:  { row: 24, attd: "F", award: "G", points: "H" },
      SMUNC:  { row: 25, attd: "I", award: "J", points: "K" },
      PACMUN: { row: 26, attd: "L", award: "M", points: "N" },
      SCVMUN: { row: 27, attd: "Q", award: "R", points: "S" },
      BMUN:   { row: 28, attd: "T", award: "U", points: "V" },
      NHSMUN: { row: 29, attd: "W", award: "X", points: "Y" },
      RIMUN:  { row: 30, attd: "Z", award: "AA", points: "AB" },
      DMUNC:  { row: 31, attd: "AC", award: "AD", points: "AE" }
    }
  },

  MEETINGS: {
    THURSDAY: {
      SHEET_NAME: "Thursday Meeting Attd",
      START_COL: "F",
      END_COL: "AR",
      TARGET_COL: "J",
      START_ROW: 2
    },
    WEDNESDAY: {
      SHEET_NAME: "Mock/Training Attd",
      START_COL: "F",
      END_COL: "AO",
      TARGET_COL: "M",
      START_ROW: 2
    }
  }
};

// ==============================================================================
// MAIN EXECUTION FUNCTION
// ==============================================================================
function updateMemberDashboard() {
  const indSheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const token = indSheet.getRange(CONFIG.TOKEN_CELL_INDIVIDUAL).getValue();

  if (!token) {
    SpreadsheetApp.getUi().alert("Error: No token found in cell " + CONFIG.TOKEN_CELL_INDIVIDUAL);
    return;
  }

  let masterSpreadsheet;
  try {
    masterSpreadsheet = SpreadsheetApp.openById(CONFIG.MASTER_SHEET_ID);
  } catch (e) {
    SpreadsheetApp.getUi().alert("Error opening Master Sheet. Verify Sheet ID and view permissions.");
    return;
  }

  // Execute Section Updates
  updatePersonalInfo(indSheet, masterSpreadsheet, token);
  updateTotalPoints(indSheet, masterSpreadsheet, token);
  updateFundraising(indSheet, masterSpreadsheet, token);
  updateConferencePayments(indSheet, masterSpreadsheet, token);
  updateAwardsAttendance(indSheet, masterSpreadsheet, token);
  updateDynamicAttendance(indSheet, masterSpreadsheet, token, CONFIG.MEETINGS.THURSDAY);
  updateDynamicAttendance(indSheet, masterSpreadsheet, token, CONFIG.MEETINGS.WEDNESDAY);

  SpreadsheetApp.getUi().alert("Dashboard updated successfully!");
}

// ==============================================================================
// HELPER FUNCTIONS FOR EACH SECTION
// ==============================================================================

function updatePersonalInfo(indSheet, masterSpreadsheet, token) {
  const masterSheet = masterSpreadsheet.getSheetByName(CONFIG.PERSONAL_INFO.SHEET_NAME);
  const rowData = getRowByToken(masterSheet, token, CONFIG.PERSONAL_INFO.SHEET_NAME, CONFIG.PERSONAL_INFO.TOKEN_COL);
  if (!rowData) return;

  const targets = CONFIG.PERSONAL_INFO.TARGETS;
  
  const firstName = rowData[colToIdx("B")] || "";
  const lastName = rowData[colToIdx("A")] || "";
  const fullName = (firstName + " " + lastName).trim();

  indSheet.getRange(targets.NAME_CELL).setValue(fullName);
  indSheet.getRange(targets.ID_CELL).setValue(rowData[colToIdx("D")]);
  indSheet.getRange(targets.EMAIL_CELL).setValue(rowData[colToIdx("E")]);
  indSheet.getRange(targets.GRADE_CELL).setValue(rowData[colToIdx("C")]);
}

function updateTotalPoints(indSheet, masterSpreadsheet, token) {
  const masterSheet = masterSpreadsheet.getSheetByName(CONFIG.TOTAL_POINTS.SHEET_NAME);
  const rowData = getRowByToken(masterSheet, token, CONFIG.TOTAL_POINTS.SHEET_NAME, CONFIG.TOTAL_POINTS.TOKEN_COL);
  if (!rowData) return;

  const totalPoints = rowData[colToIdx(CONFIG.TOTAL_POINTS.MASTER_COL)];
  indSheet.getRange(CONFIG.TOTAL_POINTS.TARGET_CELL).setValue(totalPoints);
}

function updateFundraising(indSheet, masterSpreadsheet, token) {
  const masterSheet = masterSpreadsheet.getSheetByName(CONFIG.FUNDRAISING.SHEET_NAME);
  const rowData = getRowByToken(masterSheet, token, CONFIG.FUNDRAISING.SHEET_NAME);
  if (!rowData) return;

  const cols = CONFIG.FUNDRAISING.COLS;
  const targetRow = CONFIG.FUNDRAISING.ROW;

  for (let key in cols) {
    const val = rowData[colToIdx(cols[key].masterCol)];
    indSheet.getRange(cols[key].targetCol + targetRow).setValue(val);
  }
}

function updateConferencePayments(indSheet, masterSpreadsheet, token) {
  const masterSheet = masterSpreadsheet.getSheetByName(CONFIG.CONFERENCE_PAYMENTS.SHEET_NAME);
  const rowData = getRowByToken(masterSheet, token, CONFIG.CONFERENCE_PAYMENTS.SHEET_NAME);
  if (!rowData) return;

  const confs = CONFIG.CONFERENCE_PAYMENTS.CONFERENCES;
  for (let conf in confs) {
    const c = confs[conf];
    const p1Val = c.p1 ? rowData[colToIdx(c.p1)] : "";
    const p2Val = c.p2 ? rowData[colToIdx(c.p2)] : "";
    const frval = c.appliedFR ? rowData[colToIdx(c.appliedFR)] : "";

    indSheet.getRange("B" + c.row).setValue(p1Val);
    indSheet.getRange("C" + c.row).setValue(p2Val);
    indSheet.getRange("D" + c.row).setValue(frval);
  }
}

function updateAwardsAttendance(indSheet, masterSpreadsheet, token) {
  const masterSheet = masterSpreadsheet.getSheetByName(CONFIG.AWARDS_ATTENDANCE.SHEET_NAME);
  const rowData = getRowByToken(masterSheet, token, CONFIG.AWARDS_ATTENDANCE.SHEET_NAME);
  if (!rowData) return;

  const confs = CONFIG.AWARDS_ATTENDANCE.CONFERENCES;
  for (let conf in confs) {
    const c = confs[conf];
    const attdVal = isP(rowData[colToIdx(c.attd)]);
    const awardVal = rowData[colToIdx(c.award)];
    const pointsVal = rowData[colToIdx(c.points)];

    indSheet.getRange("B" + c.row).setValue(attdVal);   // Column B: Attendance Checkbox (TRUE/FALSE)
    indSheet.getRange("C" + c.row).setValue(awardVal);  // Column C: Award
    indSheet.getRange("D" + c.row).setValue(pointsVal); // Column D: Points Earned
  }
}

function updateDynamicAttendance(indSheet, masterSpreadsheet, token, meetingConfig) {
  const masterSheet = masterSpreadsheet.getSheetByName(meetingConfig.SHEET_NAME);
  const rowData = getRowByToken(masterSheet, token, meetingConfig.SHEET_NAME);
  if (!rowData) return;

  const startIdx = colToIdx(meetingConfig.START_COL);
  const endIdx = colToIdx(meetingConfig.END_COL);

  const rawAttendance = rowData.slice(startIdx, endIdx + 1);
  const checkboxValues = rawAttendance.map(val => [isP(val)]);

  const targetRange = indSheet.getRange(
    meetingConfig.START_ROW,
    colToIdx(meetingConfig.TARGET_COL) + 1,
    checkboxValues.length,
    1
  );

  targetRange.setValues(checkboxValues);
}

// ==============================================================================
// UTILITY FUNCTIONS
// ==============================================================================

function getRowByToken(sheet, token, sheetName, overrideTokenCol) {
  if (!sheet) {
    Logger.log("Error: Tab '" + sheetName + "' not found on Master Sheet.");
    return null;
  }
  
  const tokenColStr = overrideTokenCol || CONFIG.DEFAULT_TOKEN_COL_MASTER;
  const tokenColIdx = colToIdx(tokenColStr);
  const data = sheet.getDataRange().getValues();

  for (let i = 0; i < data.length; i++) {
    if (String(data[i][tokenColIdx]).trim() === String(token).trim()) {
      return data[i];
    }
  }
  Logger.log("Token '" + token + "' was not found in tab: " + sheetName + " (Searching Col " + tokenColStr + ")");
  return null;
}

function isP(val) {
  if (typeof val === "boolean") return val;
  if (!val) return false;
  const str = String(val).trim().toUpperCase();
  return str === "P" || str === "TRUE";
}

function colToIdx(colStr) {
  if (!colStr) return -1;
  let col = 0;
  let str = String(colStr).toUpperCase().trim();
  for (let i = 0; i < str.length; i++) {
    col = col * 26 + (str.charCodeAt(i) - 64);
  }
  return col - 1;
}

function onOpen(e) {
  try {
    const ui = SpreadsheetApp.getUi();
    ui.createMenu("Club Tools")
      .addItem("Sync / Update Dashboard", "updateMemberDashboard")
      .addToUi();
  } catch (err) {
    // Prevents silent fails on restricted auth modes
    Logger.log("Menu creation failed: " + err);
  }
}