"""Render the experiment matrix from local run records without estimating missing results."""
import argparse
import hashlib
import json
from pathlib import Path

CORE = (('01','nnsmith'),('02','minference'),('03','infinigen'),('04','sparta'))
PUBLIC_SOURCE = (('05','prompt-cache'),('07','spinquant'),('09','kvquant'),('14','dx100'))
PAPER_ONLY = (('11','onesidedmw'),('13','cxlfork'),('16','juneberry'),('17','twilight-tlite'))
PORTS = ('swarm_goal','joint_swarm_goal','direct_deepseek')
PILOT_DATE = '20261122'


def load(p):
    return json.loads(p.read_text())


def paths(runs, paper, stratum):
    if paper == 'nnsmith':
        swarm = runs/'method-boundary-synthesis-max-20261120'
        direct = runs/f'method-boundary-direct-max-r2-{PILOT_DATE}'
    elif stratum == 'development':
        swarm = runs/f'method-boundary-core-synthesis-max-{PILOT_DATE}'
        direct = runs/f'method-boundary-direct-max-r2-{paper}-{PILOT_DATE}'
    elif stratum == 'expanded_source':
        swarm = runs/f'method-boundary-expanded-synthesis-max-{PILOT_DATE}'
        direct = runs/f'method-boundary-direct-max-{paper}-{PILOT_DATE}'
    else:
        swarm = runs/f'method-boundary-paper-only-synthesis-max-{PILOT_DATE}'
        direct = runs/f'method-boundary-direct-paper-only-{paper}-{PILOT_DATE}'
    for attempt in ('recovered','closed'):
        recovery = runs/f'method-boundary-direct-max-{attempt}-{paper}-{PILOT_DATE}'
        if (recovery/'recovery.json').is_file():
            direct = recovery
    fresh = runs/f'method-boundary-direct-max-fresh-{paper}-{PILOT_DATE}'
    if (fresh/'input-index.json').is_file():
        direct = fresh
    streamed = runs/f'method-boundary-direct-max-stream-{paper}-{PILOT_DATE}'
    if (streamed/'input-index.json').is_file():
        direct = streamed
    stream_close = runs/f'method-boundary-direct-max-stream-close-{paper}-{PILOT_DATE}'
    if (stream_close/'recovery.json').is_file():
        direct = stream_close
    framework = []
    framework_conditions = ('paper_only_swarm',) if stratum == 'expanded_paper_only' else PORTS[:2]
    for condition in framework_conditions:
        retry = runs/f'method-boundary-framework-retry-{paper}-{condition}-{PILOT_DATE}'
        chosen = retry if (retry/'technical-retry.json').is_file() else swarm
        framework.append(chosen/paper/condition)
    if stratum == 'expanded_paper_only':
        framework.append(None)
    return *framework, direct/paper/PORTS[2]


def cell_state(folder):
    if folder is None:
        return {'state':'not_applicable'}
    path = folder/'summary.json'
    protocol = folder.parent.parent/'protocol.json'
    transport = load(protocol).get('transport') if protocol.is_file() else None
    if not path.is_file():
        prepared = (folder.parent.parent/'input-index.json').is_file()
        request_count = sum(1 for _ in folder.glob('request-[0-9][0-9].json'))
        state = ('requests_archived' if request_count else 'prepared' if prepared else 'unprepared')
        return dict(state=state, folder=str(folder), archived_requests=request_count, transport=transport)
    stats = load(path)
    final = folder/'final.txt'
    artifact = hashlib.sha256(final.read_bytes()).hexdigest() if final.is_file() and final.stat().st_size else None
    completed = bool(artifact) and stats.get('finish_reason') != 'length'
    return dict(state='final_received' if completed else 'terminal_without_final', folder=str(folder),
                calls=stats['requests'], responses=len(list(folder.glob('response-[0-9][0-9].json'))),
                tokens=stats['actual_returned_total_tokens'], agents=stats.get('agents'), recovery=stats.get('recovery'),
                errors=stats['errors'], validation=stats['validation'], sha256=artifact, transport=transport,
                truncated=stats.get('finish_reason') == 'length')


def build(runs):
    output = []
    for stratum,papers in (('development',CORE),('expanded_source',PUBLIC_SOURCE),('expanded_paper_only',PAPER_ONLY)):
        for ident,paper in papers:
            output.append(dict(case=ident,paper=paper,stratum=stratum,
                cells={port:cell_state(folder) for port,folder in zip(PORTS,paths(runs,paper,stratum))}))
    return output


def describe(cell):
    flags = {
        'prepared':'已准备', 'unprepared':'尚未生成单独运行目录', 'not_applicable':'—',
        'requests_archived':f"已发 {cell.get('archived_requests',0)} 次，尚无终态",
        'terminal_without_final':'终态无报告', 'final_received':'已返回',
    }
    state = cell['state']
    description=flags[state]
    if cell.get('transport') == 'sse':
        description += ' · 流式传输'
    if state in ('final_received','terminal_without_final'):
        description += f" · {cell['responses']}/{cell['calls']} 回复 · {cell['tokens']:,} token"
        if cell.get('truncated'):
            description += ' · 输出截断'
        if cell.get('recovery'):
            recovery = cell['recovery']
            if recovery.get('after_length'):
                description += ' · 输出触顶后收尾'
            elif recovery.get('force_close'):
                description += ' · 传输失败后收尾'
            else:
                description += ' · 超时后续跑'
        if cell['errors']:
            description += ' · 运行错误'
        if state=='final_received' and not cell['validation']['json_parsed']:
            description += ' · 外层格式需核对'
    if 'judgment' in cell:
        score=cell['judgment']
        label={'core':'命中核心','partial':'部分命中','miss':'未命中'}[score['match']]
        record=score.get('model_record')
        description += f' · {label}' + (f' ({record})' if record else '')
    return description


def attach_judgments(rows, judgments):
    indexed={}
    for score in judgments:
        key=(score['paper'],score['condition'])
        if key in indexed:
            raise ValueError(f'Duplicate score for {key}')
        indexed[key]=score
    for row in rows:
        for condition,cell in row['cells'].items():
            key=(row['paper'],condition)
            if key not in indexed:
                continue
            score=indexed.pop(key)
            if cell.get('sha256') != score['final_sha256']:
                raise ValueError(f'Judgment does not match the original final for {key}')
            cell['judgment']=score
    if indexed:
        raise ValueError(f'Scores outside the matrix: {list(indexed)}')


def markdown(rows):
    result=['# 运行账本','',
            '数值为 API 已返回的 total_tokens。运行状态来自存档。已附人工评分的格子显示命中程度，未审阅格子只显示状态。','',
            '| 案例 | 证据分层 | 框架：先读或仅论文 | 框架：同时开放 | 直接基线 |',
            '|---|---|---|---|---|']
    strata={'development':'开发 · 论文与源码','expanded_source':'新增 · 论文与源码','expanded_paper_only':'新增 · 仅论文'}
    for row in rows:
        result.append('| '+' | '.join([row['case']+' '+row['paper'],strata[row['stratum']],
                                          *(describe(cell) for cell in row['cells'].values())])+' |')
    return '\n'.join(result)+'\n'


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs',type=Path)
    parser.add_argument('--format',choices=['markdown','json'], default='markdown')
    parser.add_argument('--judgments',type=Path)
    args=parser.parse_args()
    rows=build(args.runs.resolve())
    if args.judgments:
        attach_judgments(rows,load(args.judgments))
    print(markdown(rows) if args.format=='markdown' else json.dumps(rows,ensure_ascii=False,indent=2),end='\n')
