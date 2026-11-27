/* Build Plan: Confidential Document Copilot (Redline)
 * #BuildHybridAI 2026 - Devpost hackathon
 * English formal report, R4 Top Color Block cover, GO-1 palette.
 */
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, PageBreak, Header, Footer, PageNumber, NumberFormat,
  AlignmentType, HeadingLevel, WidthType, BorderStyle, ShadingType,
  TabStopType, TabStopPosition, LevelFormat, TableOfContents,
  SectionType, TableLayoutType,
} = require("docx");
const fs = require("fs");

/* ---------------- Palette: GO-1 Graphite Orange ---------------- */
const P = {
  bg: "1A2330",
  accent: "D4875A",
  ink: "1A2330",          // body headings
  body: "000000",
  secondary: "666666",
  cover: {
    titleColor: "FFFFFF",
    subtitleColor: "B0B8C0",
    metaColor: "707A86",   // readable on white lower area
    footerColor: "909090",
  },
  table: {
    headerBg: "D4875A",
    headerText: "FFFFFF",
    accentLine: "D4875A",
    innerLine: "DDD0C8",
    surface: "F8F0EB",
  },
  codeBg: "F6F7F9",
};

const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: NB, bottom: NB, left: NB, right: NB };
const allNoBorders = { top: NB, bottom: NB, left: NB, right: NB, insideHorizontal: NB, insideVertical: NB };

const EN_FONT = { ascii: "Times New Roman", eastAsia: "SimSun" };
const HEAD_FONT = { ascii: "Times New Roman", eastAsia: "SimHei" };
const CODE_FONT = { ascii: "Courier New", eastAsia: "SimSun" };

function safeText(v, ph) {
  if (v === undefined || v === null || v === "" || String(v) === "NaN" || String(v) === "undefined") {
    return ph || "";
  }
  return String(v);
}

/* ---------------- Cover title layout (English, width-aware) ---------------- */
function estimateTextWidth(text, pt) {
  let width = 0;
  for (const ch of text) {
    const code = ch.codePointAt(0);
    const isCJK = (code >= 0x4e00 && code <= 0x9fff) || (code >= 0x3400 && code <= 0x4dbf) ||
      (code >= 0x3000 && code <= 0x303f) || (code >= 0xff00 && code <= 0xffef);
    width += isCJK ? pt * 20 : pt * 11;
  }
  return width;
}

function splitTitleLinesByWidth(title, maxWidthTwips, pt) {
  const words = title.split(/\s+/);
  const lines = [];
  let current = "";
  for (const w of words) {
    const candidate = current ? current + " " + w : w;
    if (estimateTextWidth(candidate, pt) <= maxWidthTwips || !current) {
      current = candidate;
    } else {
      lines.push(current);
      current = w;
    }
  }
  if (current) lines.push(current);
  // no short orphan on the last line
  if (lines.length > 1 && lines[lines.length - 1].length <= 2) {
    const last = lines.pop();
    lines[lines.length - 1] += " " + last;
  }
  return lines;
}

function calcTitleLayout(title, maxWidthTwips, preferredPt = 40, minPt = 24) {
  let titlePt = preferredPt;
  let lines;
  while (titlePt >= minPt) {
    lines = splitTitleLinesByWidth(title, maxWidthTwips, titlePt);
    const fits = lines.every((l) => estimateTextWidth(l, titlePt) <= maxWidthTwips);
    if (lines.length <= 3 && fits) break;
    titlePt -= 2;
  }
  if (!lines || lines.length > 3) {
    lines = splitTitleLinesByWidth(title, maxWidthTwips, minPt);
    titlePt = minPt;
  }
  return { titlePt, titleLines: lines };
}

const emptyPara = () => new Paragraph({
  spacing: { before: 0, after: 0, line: 40, lineRule: "exact" },
  children: [],
});

/* ---------------- Recipe R4: Top Color Block ---------------- */
function buildCoverR4(config) {
  const C = config.palette;
  const padL = 1200, padR = 800;
  const availableWidth = 11906 - padL - padR;

  const { titlePt, titleLines } = calcTitleLayout(config.title, availableWidth, 40, 26);
  const titleSize = titlePt * 2;

  const titleBlockHeight = titleLines.length * (titlePt * 23 + 200);
  const englishLabelH = config.englishLabel ? (9 * 23 + 500) : 0;
  const subtitleH = config.subtitle ? (12 * 23 + 200) : 0;
  const upperContentH = englishLabelH + titleBlockHeight + subtitleH;
  const UPPER_MIN = 7500;
  const UPPER_H = Math.max(UPPER_MIN, upperContentH + 1500 + 800);
  const DIVIDER_H = 60;

  const contentEstimate = englishLabelH + titleBlockHeight + subtitleH;
  const spacerIntrinsic = 280;
  const topSpacing = Math.max(UPPER_H - contentEstimate - spacerIntrinsic - 800, 400);

  const upperBlock = new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows: [new TableRow({
      height: { value: UPPER_H, rule: "exact" },
      children: [new TableCell({
        shading: { fill: C.bg, type: ShadingType.CLEAR },
        borders: noBorders,
        verticalAlign: "top",
        margins: { left: padL, right: padR },
        children: [
          new Paragraph({ spacing: { before: topSpacing } }),
          config.englishLabel ? new Paragraph({
            spacing: { after: 500 },
            children: [new TextRun({
              text: config.englishLabel.split("").join(" "),
              size: 18, color: C.accent, font: { ascii: "Arial" }, characterSpacing: 60,
            })],
          }) : null,
          ...titleLines.map((line, i) => new Paragraph({
            spacing: {
              after: i < titleLines.length - 1 ? 100 : 200,
              line: Math.ceil(titlePt * 23), lineRule: "atLeast",
            },
            children: [new TextRun({
              text: line, size: titleSize, bold: true,
              color: C.cover.titleColor, font: { eastAsia: "SimHei", ascii: "Arial" },
            })],
          })),
          config.subtitle ? new Paragraph({
            spacing: { after: 100, line: Math.ceil(12 * 23), lineRule: "atLeast" },
            children: [new TextRun({
              text: config.subtitle, size: 24, color: C.cover.subtitleColor,
              font: { eastAsia: "Microsoft YaHei", ascii: "Arial" },
            })],
          }) : null,
        ].filter(Boolean),
      })],
    })],
  });

  const divider = new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: allNoBorders,
    rows: [new TableRow({
      height: { value: DIVIDER_H, rule: "exact" },
      children: [new TableCell({
        borders: noBorders,
        shading: { fill: C.accent, type: ShadingType.CLEAR },
        children: [emptyPara()],
      })],
    })],
  });

  const lowerContent = [
    new Paragraph({ spacing: { before: 800 } }),
    ...(config.metaLines || []).map((line) => new Paragraph({
      indent: { left: padL }, spacing: { after: 100 },
      children: [new TextRun({
        text: safeText(line), size: 26, color: C.cover.metaColor,
        font: { eastAsia: "Microsoft YaHei", ascii: "Arial" },
      })],
    })),
    new Paragraph({ spacing: { before: 2000 } }),
    new Paragraph({
      indent: { left: padL },
      children: [
        new TextRun({ text: safeText(config.footerLeft, ""), size: 22, color: C.cover.footerColor, font: { ascii: "Arial" } }),
        new TextRun({ text: "          " }),
        new TextRun({ text: safeText(config.footerRight, ""), size: 22, color: C.cover.footerColor, font: { ascii: "Arial" } }),
      ],
    }),
  ];

  return [new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows: [new TableRow({
      height: { value: 16838, rule: "exact" },
      children: [new TableCell({
        shading: { fill: "FFFFFF", type: ShadingType.CLEAR },
        borders: noBorders,
        verticalAlign: "top",
        children: [upperBlock, divider, ...lowerContent],
      })],
    })],
  })];
}

/* ---------------- Body building blocks ---------------- */
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 160, line: 380, lineRule: "atLeast" },
    children: [new TextRun({ text, bold: true, size: 32, color: P.ink, font: HEAD_FONT })],
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 260, after: 120, line: 340, lineRule: "atLeast" },
    children: [new TextRun({ text, bold: true, size: 28, color: P.ink, font: HEAD_FONT })],
  });
}

function body(runsOrText, opts = {}) {
  const runs = typeof runsOrText === "string"
    ? [new TextRun({ text: runsOrText, size: 24, color: P.body, font: EN_FONT })]
    : runsOrText;
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 312, after: 120 },
    ...opts,
    children: runs,
  });
}

function r(text, extra = {}) {
  return new TextRun({ text, size: 24, color: P.body, font: EN_FONT, ...extra });
}

function bullet(text, boldLead) {
  const runs = [];
  if (boldLead) {
    runs.push(new TextRun({ text: boldLead, bold: true, size: 24, color: P.body, font: EN_FONT }));
  }
  runs.push(new TextRun({ text, size: 24, color: P.body, font: EN_FONT }));
  return new Paragraph({
    bullet: { level: 0 },
    alignment: AlignmentType.LEFT,
    spacing: { line: 312, after: 80 },
    children: runs,
  });
}

function caption(text) {
  return new Paragraph({
    keepNext: true,
    alignment: AlignmentType.CENTER,
    spacing: { before: 160, after: 100, line: 280 },
    children: [new TextRun({ text, bold: true, size: 21, color: P.ink, font: EN_FONT })],
  });
}

function figCaption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 100, after: 160, line: 280 },
    children: [new TextRun({ text, bold: true, size: 21, color: P.ink, font: EN_FONT })],
  });
}

/* Generic table: headers [..], rows [[..]], widths [..] percentages */
function tbl(headers, rows, widths) {
  const headerRow = new TableRow({
    tableHeader: true,
    cantSplit: true,
    children: headers.map((text, i) => new TableCell({
      shading: { fill: P.table.headerBg, type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      width: { size: widths[i], type: WidthType.PERCENTAGE },
      children: [new Paragraph({
        spacing: { line: 280 },
        children: [new TextRun({ text, bold: true, size: 21, color: P.table.headerText, font: EN_FONT })],
      })],
    })),
  });
  const dataRows = rows.map((row, ri) => new TableRow({
    cantSplit: true,
    children: row.map((cellText, i) => new TableCell({
      shading: ri % 2 === 1 ? { fill: P.table.surface, type: ShadingType.CLEAR } : undefined,
      margins: { top: 70, bottom: 70, left: 120, right: 120 },
      width: { size: widths[i], type: WidthType.PERCENTAGE },
      children: (Array.isArray(cellText) ? cellText : [cellText]).map((t) => new Paragraph({
        spacing: { line: 280 },
        children: [new TextRun({ text: safeText(t), size: 21, color: P.body, font: EN_FONT })],
      })),
    })),
  }));
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: P.table.accentLine },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: P.table.accentLine },
      left: NB, right: NB,
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: P.table.innerLine },
      insideVertical: NB,
    },
    rows: [headerRow, ...dataRows],
  });
}

/* Code block: single-cell table, monospace */
function codeBlock(lines) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: P.table.innerLine },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: P.table.innerLine },
      left: { style: BorderStyle.SINGLE, size: 12, color: P.table.accentLine },
      right: { style: BorderStyle.SINGLE, size: 2, color: P.table.innerLine },
      insideHorizontal: NB, insideVertical: NB,
    },
    rows: [new TableRow({
      cantSplit: true,
      children: [new TableCell({
        shading: { fill: P.codeBg, type: ShadingType.CLEAR },
        margins: { top: 120, bottom: 120, left: 200, right: 160 },
        children: lines.map((line) => new Paragraph({
          alignment: AlignmentType.LEFT,
          spacing: { line: 260, lineRule: "atLeast", after: 20 },
          children: [new TextRun({ text: line.length ? line : " ", size: 18, color: "24313D", font: CODE_FONT })],
        })),
      })],
    })],
  });
}

function spacerAfterTable() {
  return new Paragraph({ spacing: { after: 60 }, children: [] });
}

/* ---------------- Body content ---------------- */
const imgBuffer = fs.readFileSync("/home/z/my-project/download/redline_architecture_diagram.png");
const IMG_W = 1800, IMG_H = 2054;
const dispW = 540;
const dispH = Math.round(dispW * (IMG_H / IMG_W));

const bodyChildren = [];

/* ============ 1. Executive Summary ============ */
bodyChildren.push(h1("1. Executive Summary"));
bodyChildren.push(body([
  r("Redline (working title) is a web application that lets solo legal professionals use powerful cloud AI on confidential contracts without ever exposing client data. It is built for the "),
  r("#BuildHybridAI 2026 hackathon", { bold: true }),
  r(" (Devpost, submissions close Monday, November 30, 2026 at 2:00 PM PT) and is designed around a single mechanism that only Firebase AI Logic hybrid inference can deliver: the on-device model acts as a privacy filter for the cloud model. Gemini Nano, running inside Chrome via the hybrid inference SDK, extracts every client-identifying value from a contract as structured JSON; the lawyer reviews and approves the redactions; and only then is the sanitized text sent to a cloud Gemini model for clause-level risk analysis. The original document never leaves the machine."),
]));
bodyChildren.push(body([
  r("This is a deliberate answer to how the hackathon will be judged. The published criteria reward projects that use Firebase AI Logic hybrid inference "),
  r("as part of the solution", { italics: true }),
  r(" rather than decoratively, that ship a complete product experience rather than a proof of concept, and that make a credible, specific case for solving a real problem for a real audience. In Redline, removing hybrid inference kills the product entirely: without the private on-device pass, the cloud step could not be used on client work at all. The privacy moment is also the best demo moment, and it is made visible with routing badges, a consent gate, and a \"what leaves your device\" panel."),
]));
bodyChildren.push(body([
  r("The build targets Web (Chrome) first, using Next.js with Tailwind CSS and Firebase AI Logic with App Check enforced. The plan schedules an 18-day path from Friday, November 13 to the submission deadline, organized into four phases: environment and SDK setup, the three-stage redaction pipeline, the trust and privacy user experience, and demo production with submission. The three material risks are Gemini Nano availability on the development machine (mitigated on Day 2 with direct model access configuration and a Google Quota Account request), the official rules still being unpublished at the time of writing (checked every two to three days, with dedicated buffer days), and scope creep (controlled by an explicit feature cut-list and a Day 14 feature freeze)."),
]));

/* ============ 2. Opportunity and Rationale ============ */
bodyChildren.push(h1("2. Opportunity and Rationale: Why This Project Wins"));

bodyChildren.push(h2("2.1 Hackathon Landscape"));
bodyChildren.push(body([
  r("#BuildHybridAI 2026 is Google's official hackathon for building AI apps that run on-device and in the cloud with Firebase AI Logic. It is an online, public hackathon managed on Devpost, with roughly 1,100 registered participants and a listed prize pool of $30,000 in cash (currently shown as a single Grand Prize). Categories are Machine Learning/AI, Mobile, and Web. Submissions formally opened on Wednesday, November 11 after a two-day slip from the originally announced November 9 date; the deadline remained Monday, November 30 at 2:00 PM PT, which is approximately 6:00 AM Philippine time (PHT) on Tuesday, December 1. The named judge is Ankita Saxena, and the organizer has scheduled a live Build Session (Thursday, November 12, 10:00 AM PT, presented by Cynthia Jiang of the Firebase team) with a recording to be shared afterward."),
]));
bodyChildren.push(body([
  r("One caution shapes this whole plan: at the time of writing, the Devpost rules page still states that the Official Rules will be posted prior to the submission period, and the requirements section has not been itemized in full. Registration already binds participants to review those rules. This plan therefore treats the rules page as a standing checkpoint, schedules a formal re-read on Day 15, and keeps submission buffer days free of feature work."),
]));

bodyChildren.push(h2("2.2 The Professional's Confidentiality Problem"));
bodyChildren.push(body([
  r("Cloud AI is genuinely useful for contract review: it flags risky clauses, spots missing terms, and produces first-pass summaries in minutes. Solo and small-firm lawyers know this, and most have tried a general-purpose chatbot at least once. The problem is structural. Client contracts contain names, fees, deadlines, and deal terms that the lawyer is professionally obligated to protect; pasting them into a hosted tool sends that data to a third party. A single illustrative persona anchors the design and the demo: "),
  r("Mara, a solo contract lawyer", { bold: true }),
  r(" who reviews ten to fifteen NDAs, loan agreements, and service contracts per week, works alone without an IT department, and will not route client documents through any cloud service she cannot fully audit. For her, today's options are unsatisfying: use no AI at all, or accept a confidentiality risk she cannot explain to a client. The gap between \"AI that is useful\" and \"AI that is permissible\" is exactly the gap this product closes."),
]));

bodyChildren.push(h2("2.3 Why the On-Device-as-Filter Pattern Wins"));
bodyChildren.push(body([
  r("Most hackathon entries will use hybrid inference in one of two decorative ways: as an offline fallback that few judges will ever see exercised, or as a cost-saving route that changes nothing about the product's promise. Redline uses the on-device model for something neither pure-cloud nor pure-on-device products can claim: it "),
  r("enables", { italics: true }),
  r(" the cloud step. The on-device pass is a compliance transformation, not a convenience. Three properties make the pattern strong in a judging room. First, it is non-obvious: the on-device model is not answering the user's question at all; it is editing the question so the cloud model may lawfully see it. Second, it is verifiable in the demo: airplane mode, a visible payload panel, and per-block routing badges let judges watch the privacy promise instead of being asked to believe it. Third, it generalizes: the same skeleton (on-device sanitize, consent, cloud analyze) applies to accountants, human resources reviewers, and clinicians, which makes the impact story specific but not narrow."),
]));

bodyChildren.push(h2("2.4 Judging-Criteria Mapping"));
bodyChildren.push(body([
  r("The hackathon publishes four criteria. The table below states each criterion as it appears on Devpost and shows where Redline earns its score. Every section that follows is traceable to one of these rows."),
]));
bodyChildren.push(caption("Table 1: Judging criteria mapped to project answers"));
bodyChildren.push(tbl(
  ["Criterion (as published)", "How Redline answers it"],
  [
    ["Technological Implementation: How well is the project built, and how effectively does it use Firebase AI Logic hybrid inference as part of the solution?",
     "Hybrid inference is the product's core mechanism: Stage 1 runs with prefer_on_device and structured output, Stage 3 with only_in_cloud; the SDK's automatic fallback is surfaced honestly in the UI. App Check is enforced end to end."],
    ["Design: Does the project deliver a complete, coherent product experience, not just a technical proof of concept?",
     "Five purposeful screens, one calm professional visual language, routing badges on every AI block, empty and error states, and an exportable audit trail. One killer flow, polished, instead of ten half-features."],
    ["Potential Impact: Does the project make a credible, specific case for solving a real problem for a real audience, and does the solution address it based on what is demonstrated?",
     "A named persona (solo contract lawyer), a named obstacle (client confidentiality), and a demo that resolves the obstacle on screen: from raw NDA to redacted risk report in under three minutes."],
    ["Quality of the Idea: Is this a creative, non-obvious use of Firebase AI Logic, and does the team show genuine understanding of the problem space?",
     "The on-device model is used as a privacy filter for the cloud model. The demo shows understanding of why professionals refuse cloud AI today, not just how to call an SDK."],
  ],
  [42, 58]
));
bodyChildren.push(spacerAfterTable());

/* ============ 3. Product Definition and UX ============ */
bodyChildren.push(h1("3. Product Definition and User Experience"));

bodyChildren.push(h2("3.1 Persona and Product Promise"));
bodyChildren.push(body([
  r("The product promise, in one sentence: "),
  r("\"Analyze any contract with a frontier cloud model, and be able to show your client exactly what left your machine.\"", { italics: true }),
  r(" The persona (illustrative, not a real individual) is a solo lawyer with modest technical skill: she can paste text and click buttons, and nothing in the product may require her to configure anything. Every default must be the privacy-preserving one. The promise implies hard rules for the build: the original document is never uploaded; consent precedes every network call; and the interface always discloses where inference is running."),
]));

bodyChildren.push(h2("3.2 Core User Flow"));
bodyChildren.push(body([
  r("The end-to-end flow has eight steps, matching the architecture in Section 4. (1) The lawyer pastes or uploads the contract text. (2) The on-device model extracts sensitive entities and returns them as structured JSON: persons, organizations, financial values, dates, addresses, and identifiers. (3) The redaction preview screen lists every proposed redaction for review; the lawyer accepts, edits, or rejects each one. (4) The consent gate shows the exact outbound payload, with redacted values replaced by opaque tokens such as [PERSON_1] and [FINANCIAL_VALUE_2]. (5) Explicit approval starts the cloud stage; refusal keeps everything local and still yields an on-device-only summary. (6) An audit log entry records what was sent, when, and by which model. (7) The cloud model returns clause-level findings against the tokenized text. (8) Findings are merged back onto the original document held on-device, producing an exportable report and audit trail."),
]));

bodyChildren.push(h2("3.3 Screen Inventory"));
bodyChildren.push(body([
  r("Five screens cover the entire product. Anything that does not fit one of them is out of scope by default (see Section 6)."),
]));
bodyChildren.push(caption("Table 2: Screen inventory"));
bodyChildren.push(tbl(
  ["Screen", "Purpose", "Key elements"],
  [
    ["1. Intake", "Bring a document into the app", "Paste box; .txt/.md upload; sample-document chips; character count; privacy statement line"],
    ["2. Redaction review", "Approve the on-device extraction", "Entity list with type chips; accept/edit/reject per item; live redacted preview; on-device badge; airplane-mode indicator"],
    ["3. Consent gate", "Make the cloud step explicit", "\"What leaves your device\" payload panel; token map; Approve / Keep-it-local buttons; fallback notice if Nano is unavailable"],
    ["4. Findings report", "Deliver the cloud analysis", "Findings by severity; clause references via tokens; merged preview (original + findings); export report button"],
    ["5. Audit log", "Prove the promise over time", "Chronological entries: timestamp, stage, model, bytes sent; export JSON"],
  ],
  [18, 30, 52]
));
bodyChildren.push(spacerAfterTable());

bodyChildren.push(h2("3.4 Privacy UX Principles"));
bodyChildren.push(body([
  r("The trust experience is the design work in this project, and it is governed by four principles. Visibility: every AI-generated block carries a routing badge (On-device, Cloud, or Cloud fallback), and the consent gate shows the exact outbound bytes. Consent: no network call ever happens without a prior explicit approval in the current session; defaulting to approval is forbidden. Reversibility: redactions are stored as a local, reversible mapping so the report can show the original and the sanitized version side by side without the original ever having been transmitted. Fall-back honesty: if the device cannot run Gemini Nano, the app says so before extraction and asks permission to run the redaction pass in the cloud instead; silently switching is treated as a bug, not a fallback."),
]));

bodyChildren.push(h2("3.5 Sample Document Strategy"));
bodyChildren.push(body([
  r("Three synthetic sample contracts are authored as fixtures inside the repository: a mutual non-disclosure agreement, a small-business loan agreement, and a software services agreement. They are written to be realistic (dense clause numbering, defined terms, schedules) while containing only invented names, amounts, and addresses, so the demo never depends on real client data and no confidentiality line is crossed during judging. The same fixtures drive development, the automated smoke test, and the demo video, which keeps every stage of the project honest about what the pipeline actually handles."),
]));

/* ============ 4. System Architecture ============ */
bodyChildren.push(h1("4. System Architecture and Data Flow"));

bodyChildren.push(h2("4.1 Pipeline Overview"));
bodyChildren.push(body([
  r("Figure 1 shows the full pipeline. Stage 1 and Stage 2 are entirely local; Stage 3 is the only network-using stage, and it sees exclusively tokenized text. The fallback rule in the final note is part of the architecture, not an afterthought: when Gemini Nano is unavailable, Stage 1 reroutes to the cloud with explicit user consent and a visible notice, preserving the product promise (\"you always know where inference ran\") on any device."),
]));
bodyChildren.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 120 },
  children: [new ImageRun({
    data: imgBuffer,
    transformation: { width: dispW, height: dispH },
    type: "png",
  })],
}));
bodyChildren.push(figCaption("Figure 1: Redline hybrid document analysis pipeline (three stages, two inference modes)"));

bodyChildren.push(h2("4.2 Inference Routing"));
bodyChildren.push(caption("Table 3: Inference routing per stage"));
bodyChildren.push(tbl(
  ["Stage", "Mode / model", "Network", "Output"],
  [
    ["1. Entity extraction", "prefer_on_device: Gemini Nano in Chrome; automatic cloud fallback if unavailable", "None when on-device; cloud only with prior consent when falling back", "Structured JSON entity list (Table 4 schema)"],
    ["2. Consent gate", "No inference", "None", "Approved tokenized payload; local audit entry"],
    ["3. Risk analysis", "only_in_cloud: current-generation Gemini Flash model", "Required", "Structured findings JSON keyed by placeholder tokens"],
  ],
  [20, 38, 20, 22]
));
bodyChildren.push(spacerAfterTable());
bodyChildren.push(body([
  r("Two versioning notes keep the build out of known deprecation traps. First, Google has announced that requests to Gemini 2.5 models will be automatically routed to newer models starting December 1, 2026; the plan therefore pins current-generation Flash model names at build time and verifies them against the documentation rather than hard-coding a 2.5 identifier. Second, Firebase App Check enforcement became a requirement for Firebase AI Logic on November 2, 2026, so App Check is wired on Day 1 with the debug provider during development and a real provider before submission."),
]));

bodyChildren.push(h2("4.3 Firebase Setup and Model Initialization"));
bodyChildren.push(body([
  r("The client initializes Firebase, gets the AI Logic instance with the Gemini Developer API backend, and creates two model instances with different inference modes. Package names and method signatures evolve; the snippet below reflects the published hybrid inference pattern, and Day 1 includes verifying the exact import paths against the current Firebase AI Logic documentation."),
]));
bodyChildren.push(codeBlock([
  "import { initializeApp } from \"firebase/app\";",
  "import { getAI, getGenerativeModel, GoogleAIBackend } from \"firebase/ai\";",
  "",
  "const app = initializeApp(firebaseConfig);",
  "const ai = getAI(app, { backend: new GoogleAIBackend() });",
  "",
  "// Stage 1: on-device first; SDK falls back to cloud if Nano is unavailable",
  "const redactor = getGenerativeModel(ai, { mode: \"prefer_on_device\" });",
  "",
  "// Stage 3: cloud only, by design",
  "const analyst  = getGenerativeModel(ai, { mode: \"only_in_cloud\" });",
]));
bodyChildren.push(spacerAfterTable());

bodyChildren.push(h2("4.4 Structured Output Schema for Redaction"));
bodyChildren.push(body([
  r("Stage 1 uses Firebase AI Logic structured output (a JSON response schema on the generation config) so the extraction step returns machine-checkable data rather than prose. The schema is deliberately small: type, value, suggested replacement token, and a short reason the lawyer can read while reviewing. Structured output support differs slightly between the on-device and cloud paths, so the client validates and repairs defensively (Day 3 task)."),
]));
bodyChildren.push(codeBlock([
  "const redactionSchema = {",
  "  type: \"ARRAY\",",
  "  items: {",
  "    type: \"OBJECT\",",
  "    properties: {",
  "      type:        { type: \"STRING\", enum: [\"PERSON\", \"ORGANIZATION\",",
  "                       \"FINANCIAL_VALUE\", \"DATE\", \"ADDRESS\", \"IDENTIFIER\", \"OTHER\"] },",
  "      value:       { type: \"STRING\" },   // exact substring from the document",
  "      replacement: { type: \"STRING\" },   // e.g. [PERSON_1], [FINANCIAL_VALUE_2]",
  "      reason:      { type: \"STRING\" }    // one short human-readable line",
  "    },",
  "    required: [\"type\", \"value\", \"replacement\", \"reason\"]",
  "  }",
  "};",
]));
bodyChildren.push(spacerAfterTable());

bodyChildren.push(h2("4.5 Prompt Templates"));
bodyChildren.push(body([
  r("Stage 1 system prompt (on-device): "),
  r("\"You are a legal-document privacy filter. From the text, extract every string that could identify a party, a price, a deadline, or a location, or that acts as a personal or account identifier. Return JSON only, matching the provided schema. Never summarize; never omit a match; assign replacement tokens in order of first appearance.\"", { italics: true }),
]));
bodyChildren.push(body([
  r("Stage 3 system prompt (cloud): "),
  r("\"You are a senior contract reviewer. You will receive a contract in which sensitive values were replaced with placeholders such as [PERSON_1] and [FINANCIAL_VALUE_2]. You cannot know the real values, and you must not speculate about them. Identify clause risks, missing protective terms, ambiguous language, and one-sided obligations. For each finding return: severity (HIGH, MEDIUM, LOW), clause_reference (the token-bearing clause), issue, and recommendation. Return JSON only.\"", { italics: true }),
]));
bodyChildren.push(body([
  r("The placeholder trick is what makes the two stages compose: the cloud model reasons about structure and obligations using tokens as stable references, while the reversible local mapping lets the report display \"Clause 4.2 references [PERSON_1]\" next to the real name on the lawyer's machine."),
]));

bodyChildren.push(h2("4.6 Data-Handling Rules"));
bodyChildren.push(bullet(" is client-side only; there is no server endpoint that receives document content, so the original document physically cannot be uploaded.", "Architecture: the Next.js app"));
bodyChildren.push(bullet(" redaction mappings and audit entries live in browser-local storage (IndexedDB); export is an explicit user action.", "Local state:"));
bodyChildren.push(bullet(" the tokenized payload shown in the consent gate is byte-for-byte what Stage 3 receives; a hash of it is written to the audit log.", "Single source of truth:"));
bodyChildren.push(bullet(" no document content is ever logged to analytics; App Check attests the app, not the user's text.", "Telemetry hygiene:"));

/* ============ 5. Implementation Roadmap ============ */
bodyChildren.push(h1("5. Implementation Roadmap: 18-Day Build Schedule"));
bodyChildren.push(body([
  r("The schedule runs Friday, November 13 (Manila time) to the submission deadline, Monday, November 30 at 2:00 PM PT (approximately 6:00 AM PHT, Tuesday, December 1). Working into December 1 Manila-morning is deliberately not part of the plan: the internal freeze is Day 17 (November 29) with a draft submission uploaded, so that the final Devpost submit happens in daylight hours with buffer. Each phase ends at a gate; a gate that slips consumes the buffer day rather than the demo days."),
]));
bodyChildren.push(caption("Table 4: Day-by-day schedule (dates in PHT)"));
bodyChildren.push(tbl(
  ["Day / date", "Phase", "Work items", "Gate"],
  [
    ["1 - Fri Nov 13", "Setup", "Firebase project; App Check (debug provider); Next.js + Tailwind scaffold; SDK init; watch Build Session recording", "Hello-world hybrid call runs in Chrome"],
    ["2 - Sat Nov 14", "Setup", "Chrome on-device dev configuration (direct model access to Gemini Nano); verify prefer_on_device vs fallback; routing logger", "Mode switching observed and logged"],
    ["3 - Sun Nov 15", "Pipeline", "Stage 1 structured-output extraction against the NDA fixture; JSON validation/repair", "Accurate entities JSON on fixture 1"],
    ["4 - Mon Nov 16", "Pipeline", "Redaction engine: apply replacement tokens; reversible local mapping", "Tokenized text generated losslessly"],
    ["5 - Tue Nov 17", "Pipeline", "Redaction review screen: accept / edit / reject per entity", "Review loop complete"],
    ["6 - Wed Nov 18", "Pipeline", "Stage 3 cloud analysis with findings schema; merge findings via tokens", "End-to-end run on one document"],
    ["7 - Thu Nov 19", "Pipeline", "Intake screen; document state handling; error and edge cases (empty, huge, non-English text)", "All five screens stubbed or live"],
    ["8 - Fri Nov 20", "Trust UX", "Consent gate + \"what leaves your device\" payload panel", "Privacy flow complete"],
    ["9 - Sat Nov 21", "Trust UX", "Audit log; routing badges everywhere; fallback consent pre-flight", "Badges verified on both model paths"],
    ["10 - Sun Nov 22", "Polish", "Tailwind theme pass: spacing, type scale, empty states, microcopy", "No lorem, no dead ends"],
    ["11 - Mon Nov 23", "Polish", "Airplane-mode test; weak-machine fallback test; fix gaps", "Offline demo works end to end"],
    ["12 - Tue Nov 24", "Polish", "Exportable report + audit trail download", "Exports open cleanly"],
    ["13 - Wed Nov 25", "Demo", "Video: script read-through, screen recording, edit to 3 minutes", "Picture-locked cut"],
    ["14 - Thu Nov 26", "Demo", "Bug-fix buffer only; feature freeze", "No new code after today"],
    ["15 - Fri Nov 27", "Submit", "Re-read official rules + requirements; write-up, README, license; record any constraint changes", "Compliance confirmed"],
    ["16 - Sat Nov 28", "Submit", "Clean-machine dry run; Devpost form dry run", "Zero surprises"],
    ["17 - Sun Nov 29", "Submit", "Internal freeze; upload draft submission", "Draft submitted"],
    ["18 - Mon Nov 30", "Submit", "Final review; SUBMIT well before 2:00 PM PT", "Submitted"],
  ],
  [16, 12, 46, 26]
));
bodyChildren.push(spacerAfterTable());
bodyChildren.push(body([
  r("If team size allows two builders, the natural split is pipeline (Days 3-6) versus interface (Days 5, 7-10); the gates are unchanged. For a solo builder, the schedule already assumes single-threaded work, and the cut-list in Section 6 is the pressure valve: items move from MVP to strong-to-have only if their gate passed early."),
]));

/* ============ 6. Feature Cut-List ============ */
bodyChildren.push(h1("6. Feature Cut-List and Scope Guardrails"));
bodyChildren.push(body([
  r("With roughly 1,100 participants, the differentiator is not feature count; it is a single flow that works flawlessly and demonstrates the mechanism. The cut-list below is a contract with yourself: MVP rows are commitments, strong-to-have rows are taken only when their enabling gate has already passed, and out-of-scope rows are refused even when tempting. Anything not listed here requires displacing an equal-effort MVP item before it enters the schedule."),
]));
bodyChildren.push(caption("Table 5: Feature tiers"));
bodyChildren.push(tbl(
  ["Tier", "Features", "Rationale"],
  [
    ["MVP (committed)",
     "On-device entity extraction with structured output; redaction review UI; consent gate with payload panel; cloud risk analysis on tokenized text; findings merged into a report; routing badges; airplane-mode operation for Stages 1-2; local audit log; three sample fixtures",
     "These are the minimum set that lets every judging criterion be demonstrated on screen"],
    ["Strong-to-have (only if gates passed)",
     "Client-side .docx text extraction; editable replacement tokens; audit-trail export; fallback consent pre-flight banner; keyboard-first review UX; light/dark theme",
     "Each deepens Design or Implementation without touching the pipeline's risk profile"],
    ["Out of scope (v2 ideas)",
     "Server-side storage or sync; multi-user teams; PDF/image OCR intake; e-signature integrations; clause template library; non-English contracts; mobile builds; template marketplace",
     "None of these affect the judged demo; each adds days of risk to an 18-day window"],
  ],
  [20, 46, 34]
));
bodyChildren.push(spacerAfterTable());
bodyChildren.push(body([
  r("One guardrail deserves emphasis because it is a scoring issue, not an engineering one: the product must never claim to provide legal advice or compliance certification. The interface copy positions Redline as an assistive review tool; the demo narration says \"first-pass analysis\" rather than \"legal opinion.\" Overclaiming invites exactly the scrutiny a privacy product cannot afford."),
]));

/* ============ 7. Risk Analysis ============ */
bodyChildren.push(h1("7. Risk Analysis and Contingency Plans"));
bodyChildren.push(body([
  r("The risk register below is reviewed at every gate. Likelihood and impact are qualitative (Low / Medium / High); mitigations name the day the mitigation happens, so a risk that slips is visible in the schedule rather than in the final week."),
]));
bodyChildren.push(caption("Table 6: Risk register"));
bodyChildren.push(tbl(
  ["Risk", "L", "I", "Mitigation"],
  [
    ["Gemini Nano unavailable on the development machine (Chrome build, hardware, or flag gating)", "M", "H",
     "Day 2 is reserved for direct model access configuration and verification; if still blocked, request a Google Quota Account through the hackathon process (identity verification required, allow lead time); the cloud-fallback path is itself demoable"],
    ["Official rules and full submission requirements still unpublished", "H", "M",
     "Check the Devpost rules and Updates tabs every 2-3 days; formal re-read on Day 15; buffer days 14-17 absorb constraint changes (video length, platform, license)"],
    ["Structured output behaves differently on-device vs cloud", "M", "M",
     "Defensive JSON validation and repair on both paths (Day 3); smoke test runs both paths on all fixtures (Day 11)"],
    ["Gemini 2.5 model sunset (auto-routing from Dec 1, 2026)", "L", "L",
     "Pin current-generation Flash model names at build time; verify against documentation during Day 1 setup"],
    ["App Check enforcement friction (attestation provider setup)", "M", "M",
     "Wired Day 1 with debug provider; real provider swapped in during Day 15-16; never deferred to submission day"],
    ["Cloud quota or rate limits during judging", "L", "H",
     "Demo video recorded on Day 13, so evaluation does not depend on live calls; quota account process available; graceful rate-limit error states in UI"],
    ["Scope creep", "H", "M",
     "Section 6 cut-list governance; Day 14 feature freeze; new ideas must displace equal-effort MVP items"],
    ["Privacy claim overreach invites scrutiny", "L", "H",
     "Wording review on Day 15; assistive-tool positioning; \"what leaves your device\" panel keeps claims verifiable"],
  ],
  [40, 6, 6, 48]
));
bodyChildren.push(spacerAfterTable());

/* ============ 8. Demo Video Script ============ */
bodyChildren.push(h1("8. Demo Video Script and Judging-Criteria Mapping"));
bodyChildren.push(h2("8.1 Three-Minute Script"));
bodyChildren.push(body([
  r("The video is recorded on Day 13 from the NDA fixture, in one continuous flow with two cutaways (the airplane-mode indicator and the audit log). Final length constraints come from the official requirements and are confirmed on Day 15; if a shorter cut is required, the script compresses from the middle, never from the consent gate."),
]));
bodyChildren.push(caption("Table 7: Demo video script"));
bodyChildren.push(tbl(
  ["Time", "Scene", "Narration essence"],
  [
    ["0:00-0:20", "Problem hook", "Solo lawyers cannot use cloud AI on client contracts; confidentiality blocks it. Today that trade-off is false."],
    ["0:20-0:50", "Intake + on-device stage", "Paste the NDA; point at the On-device badge and the airplane-mode indicator while extraction runs locally."],
    ["0:50-1:30", "Redaction review", "Structured entities appear (persons, amounts, dates); accept one, edit one; the preview updates live."],
    ["1:30-2:00", "Consent gate", "Open the \"what leaves your device\" panel; read a tokenized line aloud; approve. This is the product."],
    ["2:00-2:40", "Cloud findings + merge", "Findings return keyed to clauses via tokens; merged view shows the report next to the original; audit log entry shown."],
    ["2:40-3:00", "Close", "Restate the promise; name the stack (Firebase AI Logic hybrid inference, Next.js); show the fallback notice; invite questions."],
  ],
  [14, 24, 62]
));
bodyChildren.push(spacerAfterTable());

bodyChildren.push(h2("8.2 Scene-to-Criteria Mapping"));
bodyChildren.push(caption("Table 8: Which scene proves which criterion"));
bodyChildren.push(tbl(
  ["Criterion", "Proven by"],
  [
    ["Technological Implementation", "Scenes at 0:20 (mode badges, airplane mode), 0:50 (structured output), 2:40 (two-mode architecture)"],
    ["Design", "The uninterrupted 3-minute flow itself; review and consent interactions; report presentation at 2:00"],
    ["Potential Impact", "The 0:00 persona framing and the 1:30 consent gate that resolves it"],
    ["Quality of the Idea", "The 1:30-2:00 payload panel: the on-device model shown functioning as a filter for the cloud model"],
  ],
  [34, 66]
));
bodyChildren.push(spacerAfterTable());

/* ============ 9. Submission Checklist and Resources ============ */
bodyChildren.push(h1("9. Submission Checklist and Resources"));
bodyChildren.push(h2("9.1 Pre-Submission Checklist"));
bodyChildren.push(caption("Table 9: Submission checklist"));
bodyChildren.push(tbl(
  ["#", "Item", "When"],
  [
    ["1", "Re-read the Official Rules on Devpost once published; note eligibility, team, IP, and submission constraints", "Day 15 (hard gate)"],
    ["2", "Confirm submission form fields and demo video constraints against the requirements section", "Day 15"],
    ["3", "App Check active with a production provider; verified on a clean Chrome profile", "Days 15-16"],
    ["4", "Demo video final cut, captions included, within stated limits", "Day 13 (recut if rules demand)"],
    ["5", "Public repository with README (setup, architecture, sample fixtures) and an open-source license, if required by rules", "Day 15"],
    ["6", "Devpost project description, images, and team details completed", "Day 17"],
    ["7", "Draft submission uploaded on Devpost; final submit confirmed in daylight hours", "Day 17-18"],
    ["8", "Timezone check: deadline is 2:00 PM PT on Mon Nov 30 (about 6:00 AM PHT Tue Dec 1); never plan a Dec 1 PHT morning submit", "Standing"],
  ],
  [6, 68, 26]
));
bodyChildren.push(spacerAfterTable());

bodyChildren.push(h2("9.2 Official Resources"));
bodyChildren.push(caption("Table 10: Resource index"));
bodyChildren.push(tbl(
  ["Resource", "Where"],
  [
    ["Hackathon page (overview, prizes, judging, participants)", "firebasehybridaihackathon.devpost.com"],
    ["Official rules and updates tabs (check for publication)", "firebasehybridaihackathon.devpost.com/rules and the Updates tab"],
    ["Firebase AI Logic hybrid inference overview", "firebase.google.com/docs/ai-logic/hybrid"],
    ["Web get-started guide (Chrome hybrid experiences)", "firebase.google.com/docs/ai-logic/hybrid/web/get-started"],
    ["Android get-started guide (if a stretch build is attempted)", "firebase.google.com/docs/ai-logic/hybrid/android/get-started"],
    ["Hybrid inference announcement and code pattern", "firebase.blog/posts/2025/06/hybrid-inference-firebase-ai-logic"],
    ["Android hybrid developer guide", "developer.android.com/ai/hybrid"],
    ["Build Session recording (Cynthia Jiang, Firebase team)", "Linked from the hackathon Resources tab (recorded Nov 12)"],
    ["Teammate and support channels", "Devpost Discord: #buildhybridai-chat; #hackathon-help with the BuildHybridAI tag"],
    ["Google Quota Account request", "Form linked from the hackathon Resources tab; identity verification required; accounts issued weekly"],
    ["General Firebase developer support", "firebase.google.com/community and the firebase-talk Google group"],
  ],
  [46, 54]
));
bodyChildren.push(spacerAfterTable());

bodyChildren.push(h2("9.3 Standing Cadence"));
bodyChildren.push(body([
  r("Three habits keep the plan safe until submission. Check the Devpost rules and Updates tabs every two to three days, since the Official Rules were still pending at the time this plan was written and bonus-challenge details may also surface there. Re-run the two smoke tests (airplane mode and clean-machine) after any dependency change, not just at Day 11 and Day 16. And treat Day 14's feature freeze as the moment the project switches from building to proving: from that day forward, every change must trace to a bug, a rule, or a judging criterion."),
]));

/* ============ 10. Cross-Platform Delivery (Addendum) ============ */
bodyChildren.push(h1("10. Addendum A: Cross-Platform Delivery on Firebase"));
bodyChildren.push(body([
  r("This addendum answers two delivery questions raised after the main plan was written: where the product is hosted on Firebase, and what changes when an Android build joins the web build inside the same Firebase project. The platform facts below were verified against the Firebase AI Logic documentation on November 12, 2026; they confirm that the architecture in Section 4 needs no structural change to ship on both platforms."),
]));

bodyChildren.push(h2("10.1 Hosting and Distribution Matrix"));
bodyChildren.push(body([
  r("The web build is the primary judged artifact and deploys with "),
  r("Firebase App Hosting", { bold: true }),
  r(" (generally available since April 2025 and built for Next.js). App Hosting requires the Blaze pay-as-you-go plan; at demo traffic levels the cost is effectively zero, and a budget alert should be set on Day 1. Because Redline is client-only by architecture (Section 4.6: no server endpoint ever receives document text), a static export on the free Spark plan is a viable fallback if SSR is not needed. The Android build reuses the same Firebase project; its judged distribution path is "),
  r("Firebase App Distribution", { bold: true }),
  r(", which delivers an APK to judges through a tester invite link without a Play Store review cycle."),
]));
bodyChildren.push(caption("Table 11: Hosting and distribution matrix"));
bodyChildren.push(tbl(
  ["Platform", "Build and hosting", "Distribution to judges", "Notes"],
  [
    ["Web (primary build)",
     "Next.js on Firebase App Hosting (Blaze plan, budget alert); static-export fallback on Spark",
     "Public URL entered on the Devpost submission form; App Hosting preview channels for iteration",
     "One Firebase project with the Web app registered; App Check enforced with a web attestation provider"],
    ["Android (secondary build)",
     "Same Firebase project with an Android app registered (package name + SHA-256); Gradle: firebase-ai on BoM 34.10+ plus firebase-ai-ondevice 16.0.0-beta07",
     "Firebase App Distribution tester invite link with the APK; a Play Store listing is optional and can wait until after judging",
     "On-device inference needs an AICore device (Pixel 8 class); the on-device SDK is experimental and not yet in the BoM"],
    ["Shared backend",
     "Firebase Auth (anonymous sign-in), App Check, and optionally Firestore for audit-metadata sync",
     "Both apps attest through App Check; judges never configure anything",
     "Document text is never stored server-side, keeping the Section 4.6 data-handling rules intact"],
  ],
  [16, 32, 28, 24]
));
bodyChildren.push(spacerAfterTable());

bodyChildren.push(h2("10.2 Hybrid Inference Support by Platform"));
bodyChildren.push(body([
  r("On the web, on-device inference is real and demoable today: the Firebase JS SDK drives "),
  r("Gemini Nano inside Chrome Desktop v139 or later", { bold: true }),
  r(" through Chrome's Prompt API, and - importantly for Stage 1 - structured output (JSON) is supported on the on-device path. The on-device model is single-turn and caps at 9,216 tokens, accepts text or inline JPEG/PNG images, and cannot read PDFs, which is exactly why the intake design in Section 3.3 is text-first. On Android, hybrid inference is labeled experimental: the on-device artifact ships outside the BoM, and supported hardware is the ML Kit/AICore device list (Pixel 8 class and newer). The four inference modes are identical across platforms, so the Section 4.2 routing table holds for both builds."),
]));
bodyChildren.push(caption("Table 12: Hybrid inference platform capabilities (verified November 12, 2026)"));
bodyChildren.push(tbl(
  ["Capability", "Web (Chrome Desktop)", "Android"],
  [
    ["On-device model", "Gemini Nano in Chrome via the Prompt API", "Gemini Nano via AICore / ML Kit Prompt API (beta)"],
    ["SDK baseline", "Firebase JS SDK (hybrid extension); Chrome v139+", "firebase-ai 17.10.0+ (BoM 34.10.0+) plus firebase-ai-ondevice 16.0.0-beta07"],
    ["Structured output on-device", "Supported - Stage 1 works fully on-device", "Experimental; verify per device during Day 2 gate"],
    ["On-device limits", "Single-turn; 9,216-token cap; text or inline JPEG/PNG; no PDF input", "Single-turn; text or a single Bitmap input; no PDF input"],
    ["Availability check", "LanguageModel.availability() returns available / downloading / downloadable; LanguageModel.create() triggers the download", "ML Kit supported-device list; AICore manages model download and updates"],
    ["Inference modes", "prefer_on_device, only_on_device, prefer_in_cloud, only_in_cloud", "Same four modes"],
  ],
  [24, 40, 36]
));
bodyChildren.push(spacerAfterTable());

bodyChildren.push(h2("10.3 One Project, Two Apps - and Demo Readiness"));
bodyChildren.push(body([
  r("A single Firebase project registers both applications; Auth, App Check, and any future Firestore rules are configured once and inherited by both clients. The recommended build order does not change: the web build ships first because judges open a URL, and the Android build follows as the proof that hybrid inference is a real, cross-platform mechanism rather than a browser trick. Three rehearsal items turn this matrix into demo insurance:"),
]));
bodyChildren.push(bullet(" the demo laptop runs Chrome 139+ with the Nano model pre-downloaded, so LanguageModel.availability() reports \"available\" on stage; every Stage 1 chunk is kept under the 9,216-token cap.", "Demo machine:"));
bodyChildren.push(bullet(" a Pixel 8-class device with the App Distribution build installed before the video is recorded on Day 13.", "Android device:"));
bodyChildren.push(bullet(" a judge who opens the URL on a non-Chrome or older browser simply gets the cloud path with the honest fallback notice from Section 3.4 - treat that as a rehearsed feature demonstration, not a failure.", "Fallback rehearsal:"));

/* ============ 11. Competitive Differentiation (Addendum) ============ */
bodyChildren.push(h1("11. Addendum B: Competitive Differentiation Strategy"));
bodyChildren.push(body([
  r("With the submission gallery not yet published and participation grown past 1,500, Redline must assume that other entries will also combine the words \"private\" and \"AI.\" This addendum defines what Redline competes against and the six structural properties that keep it ahead of same-idea copycats. It is written as a check on the plan, not an addition to the scope: every moat below is already embodied in the Section 6 MVP list."),
]));

bodyChildren.push(h2("11.1 The Field Redline Runs Against"));
bodyChildren.push(body([
  r("The most useful benchmark is not other hackathon entries but the tools professionals can already buy. Every serious alternative to Redline is server-side or manual, which means the professional still hands client data to someone else's machine - the exact act the Section 2.2 persona refuses. That gap is the positioning statement, and it is defensible in one sentence during judging."),
]));
bodyChildren.push(caption("Table 13: Existing alternatives and why they do not close the gap"));
bodyChildren.push(tbl(
  ["Alternative", "What it does", "Why it is not Redline"],
  [
    ["Microsoft Presidio", "Open-source PII detection and redaction library", "A server-side pipeline the user must build and host; no contract analysis; a developer tool, not a product"],
    ["Private AI", "Hosted PII-redaction API", "Data still leaves the machine to a third party; per-call pricing; no legal findings"],
    ["Nightfall DLP", "Cloud data-loss-prevention scanning", "Enterprise cloud scanning; neither on-device nor lawyer-facing"],
    ["Adobe Acrobat redaction", "Manual, permanent redaction of files", "Hand-driven marking with no AI extraction, no analysis, and no reversibility"],
    ["General-purpose cloud chatbots", "Strong clause analysis and summarization", "Requires pasting the client's actual contract into a third-party service - precisely what the persona cannot do"],
  ],
  [20, 34, 46]
));
bodyChildren.push(spacerAfterTable());

bodyChildren.push(h2("11.2 Six Structural Moats"));
bodyChildren.push(body([
  r("A copycat that reads the Devpost brief and builds \"redact on-device, then send to cloud\" still loses to Redline on six structural points. Each is difficult to bolt on in the final week of a hackathon, and each maps to a published judging criterion, which is what turns differentiation into points."),
]));
bodyChildren.push(caption("Table 14: Differentiation moats mapped to judging criteria"));
bodyChildren.push(tbl(
  ["Moat", "What it looks like in Redline", "Why copycats miss it", "Criterion"],
  [
    ["Pipeline, not chatbot",
     "Three auditable stages with a schema-enforced contract between them; all inference modes exercised and visible",
     "Wrappers demo a single prompt; a consent-gated pipeline is product architecture that takes days to stabilize",
     "Technological Implementation"],
    ["Reversible re-hydration",
     "Cloud answers arrive as [PERSON_1] and are re-substituted locally; the report shows original and findings side by side",
     "Redact-then-cloud demos lose the token map, so their answers come back de-anchored from the real document",
     "Implementation / Design"],
    ["Trust receipts",
     "\"What leaves your device\" shows the exact outbound payload; SHA-256 hashes land in an exportable audit log",
     "Others display privacy as a screenshot; Redline lets judges verify the claim byte by byte",
     "Design / Impact"],
    ["Judge-tip pre-emption",
     "Routing badges on every AI block, an airplane-mode flow, and a rehearsed low-memory fallback path",
     "The Firebase team's published tips go unimplemented by most entries, which is free scoring left on the table",
     "Technological Implementation"],
    ["Professional depth",
     "A named persona, clause-severity findings, obligations and deadlines - not just redaction",
     "Redaction-only utilities have no \"so what\" moment for a judge scoring Potential Impact",
     "Impact / Quality of the Idea"],
    ["Judged-demo mechanics",
     "A live hosted URL, a three-minute video with the network inspector visible, and a clean public repository",
     "Repo-only submissions raise judge friction, and friction is a silent criterion across all four scores",
     "All four"],
  ],
  [16, 32, 34, 18]
));
bodyChildren.push(spacerAfterTable());

bodyChildren.push(h2("11.3 Positioning and Claims Discipline"));
bodyChildren.push(body([
  r("The one-line positioning, usable on the Devpost page and in the video close: "),
  r("\"Every other entry asks you to trust the AI. Redline shows you the receipts.\"", { bold: true }),
  r(" Positioning only works if the claims stay disciplined, so the Section 6 guardrail is restated here as law: Redline is an assistive first-pass review tool, never a source of legal advice or compliance certification; every privacy claim must be verifiable on screen; and every fallback must announce itself. The strategy's practical conclusion is conservative and deliberate - the six moats confirm the existing cut-list rather than expand it, and the differentiation work from Day 8 onward is polish, not new features."),
]));

/* ---------------- Assembly ---------------- */
const coverConfig = {
  title: "Confidential Document Copilot",
  subtitle: "Build Plan - #BuildHybridAI 2026 Hackathon (Firebase AI Logic)",
  englishLabel: "PROJECT BUILD PLAN",
  metaLines: [
    "Working title: Redline",
    "Platform: Web (Chrome) + Firebase AI Logic hybrid inference",
    "Stack: Next.js + Tailwind CSS",
    "Deadline: Monday, November 30, 2026, 2:00 PM PT",
    "Prepared: November 12, 2026",
    "Team: Solo or two-person build",
  ],
  footerLeft: "#BuildHybridAI 2026 - Devpost",
  footerRight: "On-device redaction. Cloud intelligence.",
  palette: P,
};

const pageHeader = new Header({
  children: [new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 0 },
    children: [new TextRun({
      text: "Confidential Document Copilot - Build Plan (#BuildHybridAI 2026)",
      size: 18, color: "808080", font: EN_FONT,
    })],
  })],
});

const pageFooter = new Footer({
  children: [new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "808080", font: EN_FONT })],
  })],
});

const doc = new Document({
  creator: "Build Plan",
  title: "Confidential Document Copilot - Build Plan",
  styles: {
    default: {
      document: {
        run: { font: EN_FONT, size: 24, color: P.body },
        paragraph: { spacing: { line: 312 } },
      },
      heading1: {
        run: { font: HEAD_FONT, size: 32, bold: true, color: P.ink },
        paragraph: { spacing: { before: 360, after: 160, line: 380 }, outlineLevel: 0 },
      },
      heading2: {
        run: { font: HEAD_FONT, size: 28, bold: true, color: P.ink },
        paragraph: { spacing: { before: 260, after: 120, line: 340 }, outlineLevel: 1 },
      },
      heading3: {
        run: { font: HEAD_FONT, size: 24, bold: true, color: P.ink },
        paragraph: { spacing: { before: 200, after: 100, line: 312 }, outlineLevel: 2 },
      },
    },
  },
  sections: [
    /* Section 1: Cover - margin 0, no header/footer, no page number */
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 0, bottom: 0, left: 0, right: 0 },
        },
      },
      children: buildCoverR4(coverConfig),
    },
    /* Section 2: Front matter (TOC) - Roman numerals, no visible footer needed */
    {
      properties: {
        type: SectionType.NEXT_PAGE,
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, bottom: 1440, left: 1701, right: 1417 },
          pageNumbers: { start: 1, formatType: NumberFormat.UPPER_ROMAN },
        },
      },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 200, after: 200, line: 400, lineRule: "atLeast" },
          children: [new TextRun({
            text: "Table of Contents",
            bold: true, size: 32, color: P.ink, font: HEAD_FONT,
          })],
        }),
        new TableOfContents("Table of Contents", {
          hyperlink: true,
          headingStyleRange: "1-3",
        }),
        new Paragraph({
          spacing: { before: 80 },
          children: [new TextRun({
            text: "Note: This Table of Contents is generated via field codes. To ensure page number accuracy after editing, please right-click the TOC and select \"Update Field.\"",
            italics: true, size: 18, color: "888888", font: EN_FONT,
          })],
        }),
        /* No PageBreak here: the body starts in its own NEXT_PAGE section,
           and PageBreak + section break would create a blank page. */
      ],
    },
    /* Section 3: Body - Arabic numerals starting at 1 */
    {
      properties: {
        type: SectionType.NEXT_PAGE,
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, bottom: 1440, left: 1701, right: 1417 },
          pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL },
        },
      },
      headers: { default: pageHeader },
      footers: { default: pageFooter },
      children: bodyChildren,
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const out = "/home/z/my-project/download/Confidential_Document_Copilot_Build_Plan.docx";
  fs.writeFileSync(out, buf);
  console.log("Wrote", out, buf.length, "bytes");
});
