/** A bounded, two-worker protocol for resolving evidence gaps in paper diagnoses. */
const links = new Set(['rule', 'trigger', 'mitigation', 'consequence']);

function parse(text) {
  const clean = text.trim().replace(/^```(?:json)?\s*([\s\S]+?)\s*```$/, '$1');
  try { return JSON.parse(clean); } catch { return null; }
}

export function gapWorkflow(config, emit) {
  const slots = config.routes.map((route, index) => {
    let report, assign;
    const reported = new Promise(resolve => { report = resolve; });
    const assignment = new Promise(resolve => { assign = resolve; });
    return {route, id: 'root.'+(index+1), report, assign, reported, assignment};
  });
  return async function coordinate({id, task, complete, resumePhase, startWorker}) {
    if (id !== 'root') {
      const slot = slots.find(worker => worker.id === id);
      let candidates = [];
      try {
        const answer = await complete(task + '\n\nPHASE: independent discovery\n'
          + slot.route + '\n' + config.discovery);
        const decoded = parse(answer);
        const records = Array.isArray(decoded) ? decoded : decoded?.candidates;
        const procedures = Array.isArray(decoded?.procedures)
          ? decoded.procedures.slice(0,5).flatMap((item,index) =>
              item && typeof item==='object' && !Array.isArray(item)
                ? [{...item,id:id+'#P'+(index+1)}] : []) : [];
        if (Array.isArray(records)) {
          candidates = records.slice(0, config.candidateLimit ?? 3).flatMap((item, index) =>
            item && ['rule','trigger','mitigation','consequence'].every(key => typeof item[key] === 'string')
              ? [{id:id+'#'+(index+1),
                  ...Object.fromEntries([
                    'title', 'rule', 'trigger', 'mitigation', 'consequence', 'evidence',
                    'paper_evidence', 'code_evidence', 'counterevidence', 'minimal_comparison',
                    'case_a', 'case_b', 'fixed', 'study_metric',
                  ].filter(key => item[key] != null).map(key => [key,item[key]])),
                }] : []);
        }
        slot.procedures = procedures;
        await emit('gap_discovery_frozen', {agent:id, answer, candidates, procedures, parsed:Array.isArray(records)});
      } finally {
        slot.report(candidates);
      }
      const assignment = await slot.assignment;
      if (!assignment) return 'No reassignment.';
      const answer = await resumePhase('PHASE: cross-worker verification\n' + config.verification
        + '\n\n' + JSON.stringify(assignment), config.verificationTurns);
      await emit('gap_verification_received', {agent:id, assignment, answer});
      return answer;
    }

    task = config.coordinatorTask ?? task;
    const workers = slots.map(slot => startWorker(slot.id).catch(async error => {
      slot.report([]);
      await emit('gap_worker_unavailable', {agent:slot.id, error:String(error)});
      return null;
    }));
    let verification = null;
    try {
      const candidates = (await Promise.all(slots.map(slot => slot.reported))).flat();
      const procedures = slots.flatMap(slot => slot.procedures ?? []);
      if (candidates.length || procedures.length) {
        let selection;
        try {
          selection = await resumePhase(task + '\n\nPHASE: route an evidence gap\n'
            + config.routing + '\n\n' + JSON.stringify({candidates, procedures}), 1);
        } catch (error) {
          await emit('gap_routing_unavailable', {agent:id,error:String(error)});
        }
        const choice = typeof selection === 'string' ? parse(selection) : null;
        const candidate = [...candidates,...procedures].find(item => item.id === choice?.candidate_id);
        const question = choice?.question;
        const valid = candidate && links.has(choice?.link) && typeof question === 'string'
          && question.trim().length >= 8 && question.length <= 550;
        const recipient = valid ? slots.find(slot => !candidate.id.startsWith(slot.id+'#')) : null;
        await emit('gap_route_selected', {agent:id, selection:selection ?? '', recipient:recipient?.id ?? null});
        for (const slot of slots) slot.assign(slot === recipient ? {candidate, link:choice.link, question} : null);
        if (recipient) verification = await workers[slots.indexOf(recipient)];
      }
      for (const slot of slots) slot.assign(null);
      return await resumePhase((candidates.length || procedures.length ? '' : task+'\n\n') + 'PHASE: final synthesis\n' + config.final
        + '\n\n' + JSON.stringify({candidates, procedures, verification}), 1);
    } finally {
      for (const slot of slots) slot.assign(null);
      await Promise.allSettled(workers);
    }
  };
}
