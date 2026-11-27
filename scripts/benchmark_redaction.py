"""Redline redaction benchmark — precision/recall of the local entity scanner.

Drives the REAL app (redline_app_preview.html) through its real UI path
(file input -> parser -> scanText) with Playwright, then scores the returned
findings (window.RL.findings) against hand-annotated ground truth embedded
below (annotated from the app's own text dumps of the repo samples).

Methodology (stated, reproducible):
  - findings are unique per (type, value), whitespace-normalized by the app
  - TRUE POSITIVE (precision): a finding exactly equals an annotated entity
    of the same type (after whitespace/case normalization)
  - RECALL: an annotated entity is recalled when a same-type finding equals
    it OR over-matches it (superset string — e.g. a cross-column layout makes
    the scanner grab trailing words; the name is still fully redacted)
  - everything else is a FALSE POSITIVE / MISSED respectively
  - the app caps findings at 24 (scan_max_findings); these samples stay below

Run:  python3 scripts/benchmark_redaction.py   (needs playwright + chromium)
"""
import json, pathlib, sys
from playwright.sync_api import sync_playwright

REPO = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent
TYPES = ['PERSON', 'ORG', 'AMOUNT', 'DATE', 'EMAIL', 'TITLE']

TRUTH = {
 'sample_brief.txt': [
   ('PERSON','Ms. Rhea Alvarez'), ('PERSON','Mr. Danilo Reyes'),
   ('ORG','Bituin Foods Corporation'), ('ORG','Sari-Saya Packaging Solutions Inc.'),
   ('AMOUNT','PHP 350,000'), ('AMOUNT','$6,000'),
   ('DATE','October 15, 2026'), ('DATE','11/05/2026'), ('DATE','12/20/2026'),
   ('EMAIL','r.alvarez@bituinfoods.com'), ('EMAIL','d.reyes@sarisaya.com'),
   ('TITLE','Treasurer'), ('TITLE','Managing Director')],
 'sample_agreement.docx': [
   ('PERSON','Ms. Katrina Ong'), ('PERSON','Atty. Paolo Mendoza'),
   ('ORG','Harborview Legal Partners LLP'), ('ORG','Tala Digital Ventures Inc.'),
   ('AMOUNT','$180,000'), ('AMOUNT','EUR 60,000'),
   ('DATE','April 15, 2026'), ('DATE','2026-12-31'),
   ('EMAIL','k.ong@taladigital.com'), ('EMAIL','accounts@harborviewlegal.com'),
   ('TITLE','Chief Financial Officer'), ('TITLE','General Counsel')],
 'sample_employment.docx': [
   ('PERSON','Ms. Andrea Bautista'), ('PERSON','Atty. Carla Domingo'),
   ('ORG','Marisol Media Productions Inc.'),
   ('AMOUNT','PHP 1,800,000'), ('AMOUNT','$8,500'),
   ('DATE','June 15, 2026'), ('DATE','2027-06-14'),
   ('EMAIL','a.bautista@marisolmedia.com'), ('EMAIL','c.domingo@marisolmedia.com'),
   ('EMAIL','hr@marisolmedia.com'),
   ('TITLE','Vice President'), ('TITLE','Chief Financial Officer'), ('TITLE','General Counsel')],
 'sample_contract.pdf': [
   ('PERSON','Atty. Liza Dela Cruz'), ('PERSON','Mr. Ramon Villanueva'),
   ('ORG','Silverline Business Solutions Inc.'), ('ORG','Cordova Trading & Logistics Corp.'),
   ('AMOUNT','PHP 2,400,000'), ('AMOUNT','$45,000'),
   ('DATE','February 28, 2026'), ('DATE','March 1, 2026'), ('DATE','05/31/2027'),
   ('EMAIL','l.dela.cruz@silverlineconsulting.com'), ('EMAIL','r.villanueva@cordovatrading.com'),
   ('EMAIL','accounts@silverlineconsulting.com'),
   ('TITLE','Chief Operating Officer'), ('TITLE','Managing Director')],
 'sample_nda.pdf': [
   ('PERSON','Dr. Mei Lin Tan'), ('PERSON','Atty. Fernando Salazar'),
   ('ORG','Quintana Robotics Ltd.'), ('ORG','Del Rosario Fabrication Works Inc.'),
   ('AMOUNT','$500,000'), ('AMOUNT','USD 250,000'),
   ('DATE','January 12, 2026'), ('DATE','December 31, 2028'),
   ('EMAIL','m.tan@quintanarobotics.com'), ('EMAIL','legal@delrosariofab.com'),
   ('TITLE','Chief Technology Officer'), ('TITLE','General Counsel')],
}

def norm(s):
    return ' '.join(str(s).split()).lower()

def score_sample(findings, truth):
    tvals = {t: {norm(v) for ty, v in truth if ty == t} for t in TYPES}
    tp = fp = recalled = 0
    fps, missed = [], []
    for f in findings:
        fv = norm(f['value'])
        if fv in tvals[f['type']]:
            tp += 1
        else:
            fp += 1
            fps.append((f['type'], f['value']))
    for ty, v in truth:
        tv = norm(v)
        hit = any(norm(f['value']) == tv or norm(f['value']) in tv or tv in norm(f['value'])
                  for f in findings if f['type'] == ty)
        if hit:
            recalled += 1
        else:
            missed.append((ty, v))
    return tp, fp, recalled, len(truth), fps, missed

rows, per_type = [], {t: {'tp': 0, 'fp': 0, 'truth': 0, 'rec': 0} for t in TYPES}
tot = {'tp': 0, 'fp': 0, 'truth': 0, 'rec': 0}
page_err_total = []

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto((REPO / 'redline_app_preview.html').as_uri(), wait_until='load')
    pg.wait_for_timeout(600)
    for name, truth in TRUTH.items():
        assert not errs, f'page errors before {name}: {errs}'
        pg.set_input_files('#fileInput', str(REPO / 'samples' / name))
        pg.wait_for_timeout(3500)
        findings = pg.evaluate('JSON.stringify(RL.findings)')
        findings = json.loads(findings)
        assert len(findings) < 24, f'{name}: findings hit the 24 cap — extend methodology'
        tp, fp, rec, n_truth, fps, missed = score_sample(findings, truth)
        rows.append({'sample': name, 'findings': len(findings), 'tp': tp, 'fp': fp,
                     'truth': n_truth, 'recalled': rec, 'false_positives': fps, 'missed': missed})
        for t in TYPES:  # per-type tally from the same data
            f2 = [f for f in findings if f['type'] == t]
            tr = [(ty, v) for ty, v in truth if ty == t]
            t2, fp2, r2, n2, _, _ = score_sample(f2, tr)
            per_type[t].update({'tp': per_type[t]['tp'] + t2, 'fp': per_type[t]['fp'] + fp2,
                                'truth': per_type[t]['truth'] + n2, 'rec': per_type[t]['rec'] + r2})
        tot.update({'tp': tot['tp'] + tp, 'fp': tot['fp'] + fp,
                    'truth': tot['truth'] + n_truth, 'rec': tot['rec'] + rec})
        pg.evaluate('window.RL = undefined')
    page_err_total = list(errs)
    b.close()

def prf(tp, fp, rec, truth):
    prec = tp / (tp + fp) if tp + fp else 0.0
    recl = rec / truth if truth else 0.0
    f1 = 2 * prec * recl / (prec + recl) if prec + recl else 0.0
    return prec, recl, f1

print(f"{'sample':28s} {'finds':>5s} {'TP':>3s} {'FP':>3s} {'truth':>5s} {'rec':>4s} {'P':>6s} {'R':>6s} {'F1':>6s}")
for r in rows:
    P, R, F = prf(r['tp'], r['fp'], r['recalled'], r['truth'])
    print(f"{r['sample']:28s} {r['findings']:5d} {r['tp']:3d} {r['fp']:3d} {r['truth']:5d} "
          f"{r['recalled']:4d} {P:6.3f} {R:6.3f} {F:6.3f}")

print(f"\n{'per type':28s} {'finds':>5s} {'TP':>3s} {'FP':>3s} {'truth':>5s} {'rec':>4s} {'P':>6s} {'R':>6s} {'F1':>6s}")
for t in TYPES:
    d = per_type[t]
    P, R, F = prf(d['tp'], d['fp'], d['rec'], d['truth'])
    print(f"{t:28s} {d['tp']+d['fp']:5d} {d['tp']:3d} {d['fp']:3d} {d['truth']:5d} "
          f"{d['rec']:4d} {P:6.3f} {R:6.3f} {F:6.3f}")

P, R, F = prf(tot['tp'], tot['fp'], tot['rec'], tot['truth'])
macro_f1 = sum(prf(per_type[t]['tp'], per_type[t]['fp'], per_type[t]['rec'], per_type[t]['truth'])[2] for t in TYPES) / len(TYPES)
print(f"\nOVERALL (micro)  P={P:.3f}  R={R:.3f}  F1={F:.3f}   |   macro-F1={macro_f1:.3f}")
print(f"entities annotated: {tot['truth']}   findings scored: {tot['tp']+tot['fp']}   TP={tot['tp']}  FP={tot['fp']}")
print('page errors:', page_err_total or 'none')

out = pathlib.Path(__file__).resolve().parent / 'benchmark_results.json'
out.write_text(json.dumps({'overall': {'precision': P, 'recall': R, 'f1': F, 'macro_f1': macro_f1,
                                       'tp': tot['tp'], 'fp': tot['fp'], 'truth': tot['truth']},
                           'per_type': per_type, 'per_sample': rows}, indent=2))
print('saved:', out)
sys.exit(0)
