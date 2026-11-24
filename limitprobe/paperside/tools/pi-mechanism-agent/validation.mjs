/** Structural and read-range checks only; not a semantic correctness oracle. */
export function validateReport(report, behaviors, reads) {
  const ids=report.checks.map(c=>c.id), expected=new Set(behaviors.map(b=>b.id));
  if(ids.length!==expected.size||new Set(ids).size!==ids.length||ids.some(id=>!expected.has(id)))
    throw new Error('Final report missing/duplicate/invented behavior IDs');
  const allowed=new Set(['supported','partial','local_mismatch','unlocated','static_undecidable']);
  for(const c of report.checks)if(!allowed.has(c.result))throw new Error('Invalid result label');
  for(const c of [...report.checks,...report.paths,...report.finding_clusters])for(const e of c.evidence){
    if(!Number.isInteger(e.start_line)||!Number.isInteger(e.end_line)||e.start_line<1||e.end_line<e.start_line||
       !reads.some(r=>r.path===e.path&&r.start_line<=e.start_line&&r.end_line>=e.end_line))
      throw new Error(`Unread citation ${e.path}:${e.start_line}-${e.end_line}`);
  }
  return report;
}
