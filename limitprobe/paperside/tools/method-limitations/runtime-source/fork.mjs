/** Fork semantic context without inventing results for the parent's pending calls.
 * Pi's structured provider transcripts cannot inherit an unfinished assistant tool
 * batch as if it had completed. Preserve that last decision as explicitly pending
 * text; earlier completed history remains structured and unchanged.
 */
export function validateCompletedTranscript(messages) {
  const pending = new Set();
  for (const message of messages) {
    if (message.role === 'toolResult') {
      if (!pending.delete(message.toolCallId)) throw Error('Unmatched tool result');
      continue;
    }
    if (pending.size) throw Error('Unresolved parent tool batch');
    if (message.role === 'assistant') {
      for (const c of message.content ?? []) if (c.type === 'toolCall') {
        if (pending.has(c.id)) throw Error('Duplicate tool call');
        pending.add(c.id);
      }
    }
  }
  if (pending.size) throw Error('Unresolved parent tool batch');
}
export function forkForWorker(messages) {
  const copy = structuredClone(messages), last = copy.at(-1);
  if (last?.role === 'assistant' && last.content.some(c => c.type === 'toolCall')) {
    copy.pop();
    validateCompletedTranscript(copy);
    copy.push({role:'user',timestamp:last.timestamp,
      content:[{type:'text',text:'Parent decision at the fork. These are pending requests, not tool results or completed child work:\n'+JSON.stringify(last.content)}]});
  }
  validateCompletedTranscript(copy);
  return copy;
}
