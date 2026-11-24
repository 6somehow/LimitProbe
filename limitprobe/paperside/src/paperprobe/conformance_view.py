"""Separate three semantic conclusions from pending workflow state, without rejudging."""
from copy import deepcopy

CONCLUSIONS={'supports','deviates','absent'}


def three_conclusion_view(original):
    report=deepcopy(original)
    migrated=[]
    for c in report['checks']:
        for scope in ['local_entry','artifact']:
            v=c[scope]
            if 'review_state' in v:continue
            old=v['verdict']
            if old=='insufficient':
                migrated.append(dict(id=c['id'],scope=scope))
                v.update(review_state='pending',verdict=None,discrepancy='',
                    pending_reason='本轮尚未完成这项声明的核验；完成后才能形成正式结论。',
                    workflow_next_step='明确性质声明适用的算法与前提，再检查实现是否满足。' if c['claim_type']=='guarantee' else '补齐对齐入口、依赖或等价实现的查证。',
                    status_source='workflow status migration; no new model verdict',
                    legacy_assessment=dict(verdict=old,reason=v.get('barrier','')))
            elif old in CONCLUSIONS:
                v.update(review_state='completed',pending_reason='')
            else:raise ValueError('Unknown legacy conclusion')
            v.pop('barrier',None)
    report['result_schema']='three_conclusions_v1'
    report['status_migration']=dict(note='Completed verdicts are unchanged. Previously uncompleted checks are pending work, not a fourth conclusion. Raw model response remains archived.',pending=migrated,new_model_requests=0)
    return report
