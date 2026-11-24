"""Clickable SVG of the realized paper-to-code workflow and its expansion boundary."""
from html import escape


def workflow_svg():
    boxes=[]
    def box(x,y,w,h,title,lines,href,fill='#ffffff',stroke='#9cabb8',dashed=False):
        content=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="1.5"'+(' stroke-dasharray="7 5"' if dashed else '')+'/>'
        content+=f'<text x="{x+w/2}" y="{y+28}" text-anchor="middle" class="title">{escape(title)}</text>'
        for i,line in enumerate(lines):content+=f'<text x="{x+w/2}" y="{y+52+i*21}" text-anchor="middle" class="body">{escape(line)}</text>'
        boxes.append(f'<a href="{href}">{content}</a>' if href else content)
    box(390,52,320,66,'① 论文原文：文字＋原始页面',['论文侧独立分析，不输入仓库代码'],'#discoveries','#fff3d7','#c9a664')
    box(100,156,350,70,'② A：独立发现机制',['按章节阅读 · 14 个候选'],'#discoveries','#fff3d7','#c9a664')
    box(650,156,350,70,'② B：独立发现机制',['按系统流程阅读 · 19 个候选'],'#discoveries','#fff3d7','#c9a664')
    box(370,264,360,74,'③ 合并并冻结机制清单',['20 项，保留父子／阶段边界'],'#merged','#fff3d7','#c9a664')
    box(100,374,350,78,'④ 按冻结机制拆行为',['首次合计 103 条 · 保留原文／前提'],'#call-split-M01','#fff3d7','#c9a664')
    box(650,374,350,78,'④ 独立读机制相关原页',['列初始化／条件／更新等步骤','此请求不看初次行为清单'],'#call-M02-obligations','#fff3d7','#c9a664')
    box(370,490,360,78,'⑤ 机制内对账与原子性复核',['检查复合动作、遗漏步骤与适用条件','模型提出拆分／补充，保留修改来源'],'#call-M02-reconcile','#fff3d7','#c9a664')
    box(370,604,360,66,'⑥ 冻结待审行为草稿',['共 206 条；M02 为其中 14 条'],'#continuation-all','#e4eee3','#88a58b')
    box(30,774,270,130,'代码证据准备',['固定仓库与 commit','检查 README／构建依赖','可复用逐行核实的源码包'],'#conformance-table','#e7eef4','#91a7ba')
    box(370,774,360,108,'⑦ 每个机制一个 Pi 调查会话',['输入：机制＋相关原页＋行为清单','整机制探索，再对每条声明对账'],'#conformance-trace','#dfeaf7','#7899bb')
    box(800,774,270,130,'Pi 自主调用只读工具',['目录／搜索／读 Git blob','Python 静态符号上下文','原始论文页；不运行目标'],'#conformance-trace','#e7eef4','#91a7ba')
    box(370,936,360,78,'⑧ 解释声明，再比较代码',['机制步骤／语义效果／保证','写出原文要求、代码事实及具体差异'],'#conformance-table','#dfeaf7','#7899bb')
    box(370,1052,360,78,'⑨ 模型语义一致性复核',['检查前提、合取条件、等价实现','复核本轮初判，允许改判'],'#conformance-overview','#e8e0f1','#a08ab9')
    box(370,1168,360,78,'⑩ 程序校验来源与结果结构',['ID／原页／已读代码范围／字段一致','结构通过不代表语义正确'],'#conformance-trace','#e7eef4','#91a7ba')
    box(30,1168,270,78,'校验失败：保留原始记录',['当前阶段拒收，修正另存新阶段','不把失败输出当质疑候选'],'#conformance-trace','#f7e7e3','#c39a90')
    box(800,1168,270,78,'核验任务未完成',['补齐路径或性质核验后再给结论','这是工作状态，不是第四种结论'],'#conformance-pending','#e8ebee','#a0a9b1')
    outputs=[(70,'支持论文声明','代码兑现了该项要求','#e0eddf','#82a17e'),(415,'实现与论文不符','有相关实现，但偏离明确要求','#f4dfdf','#bd8585'),(760,'论文声明未实现','对齐路径缺少该核心行为','#f6e7ce','#be9c66')]
    for x,t,line,fill,stroke in outputs:box(x,1310,270,78,t,[line],'#conformance-overview',fill,stroke)
    box(370,1456,360,88,'⑪ 合并质疑候选',['只纳入“不符／未实现”，按共享原因归组','原文→代码→差异→适用范围→效果未决'],'#conformance-findings','#f4dfdf','#bd8585')
    box(30,1462,270,70,'支持证据保留',['作为方法评估的正向对照'],'#conformance-table','#e0eddf','#82a17e')
    box(370,1590,360,88,'后续交给小组测试／运行阶段',['当前模块只交付静态质疑与证据','效果确认与运行验证尚未完成'],'#project-position','#faf7f0','#a8a391',True)
    edges=[
      'M550 118V136H275V156','M550 118V136H825V156',
      'M275 226V244H550V264','M825 226V244H550V264',
      'M550 338V354H275V374','M550 338V354H825V374',
      'M275 452V472H550V490','M825 452V472H550V490',
      'M550 568V604','M550 670V774','M300 827H370',
      'M730 807H800','M800 858H730','M550 882V936',
      'M550 1014V1052','M550 1130V1168','M370 1207H300',
      'M730 1207H800',
      'M550 1246V1280H205V1310','M550 1246V1310',
      'M550 1246V1280H895V1310',
      'M550 1388V1456','M895 1388V1425H550V1456',
      'M205 1388V1425H165V1462']
    arrows=''.join(f'<path d="{d}"/>' for d in edges)+'<path d="M550 1544V1590" stroke-dasharray="6 5"/>'
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 1710" role="img" aria-labelledby="workflow-title workflow-desc" style="width:100%;height:auto;display:block;background:#fbf8f1;border-radius:16px">
    <title id="workflow-title">论文机制拆解到 Pi 声明一致性判定：当前完整流程</title>
    <desc id="workflow-desc">论文独立发现两次后合并冻结；拆行为并独立读机制原页，对账后冻结草稿。每机制一个 Pi 会话自主读固定版本代码，先解释声明再判定，并由模型复核、程序校验；已完成核验输出三类结论；未完成项保留工作状态，合并不符与未实现候选。运行验证属于后续团队阶段。</desc>
    <defs><marker id="current-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="#6d8294"/></marker></defs>
    <style>.title{font:600 17px sans-serif;fill:#19334d}.body{font:13px sans-serif;fill:#3c5366}.lane{font:600 16px sans-serif;fill:#526778}a:hover rect{stroke-width:3}</style>
    <rect x="12" y="16" width="1076" height="685" rx="18" fill="#fcf6e9" stroke="#e4d5b7"/>
    <text x="34" y="44" class="lane">A · 论文侧独立拆解（20 项机制已跑过）</text>
    <rect x="12" y="720" width="1076" height="845" rx="18" fill="#eff4f7" stroke="#c7d5e0"/>
    <text x="34" y="750" class="lane">B · 机制级 Pi 代码核验（当前跑通 M02；其余待扩展）</text>
    <g fill="none" stroke="#6d8294" stroke-width="2" marker-end="url(#current-arrow)">'''+arrows+'</g>'+''.join(boxes)+'''<text x="752" y="821" class="body">请求</text><text x="748" y="881" class="body">证据</text></svg>'''


def render_current_flow(root,batch_summary=None):
    svg=workflow_svg()
    if batch_summary:
        svg=svg.replace('当前跑通 M02；其余待扩展',f"M02 沿用；新增 {batch_summary['reviewed_mechanisms']}/19 项已调查")
        svg=svg.replace('href="#conformance-overview"','href="#sparta-batch"').replace('href="#conformance-pending"','href="#batch-M18"').replace('href="#conformance-findings"','href="#batch-M08"')
        svg=svg.replace('href="#conformance-trace"','href="#batch-trace-M08"').replace('href="#conformance-table"','href="#batch-M08"')
    (root/'current-paper-to-code-flow.svg').write_text(svg.replace('href="#','href="sparta-independent-k2.html#'))
    html='''<section id="current-workflow"><h2>当前完整流程：论文机制 → Pi 声明一致性判定</h2>
    <p><b>探索单位是机制，核验单位是论文声明，交付单位是归组后的质疑候选。</b> 点击图中节点可跳到实际 prompt、模型返回或源码证据。
    黄色区域先独立读论文；代码直到机制与行为冻结后才进入核验。</p>
    <p class="notice">进度：论文侧 20 项机制已形成 206 条待审行为；新版 Pi 一致性流程目前只跑通传播机制 M02 的 14 条。
    其余 19 项共 192 条尚未完成新版代码核验。20 项含组合父子机制，并非互不重叠的 20 个算法。</p>
    <div style="overflow:auto">'''+svg+'''</div>
    <p>当前 M02 判定：已完成 13/14 项；正式结论为支持 8／实现不符 4／声明未实现 1。B08 是待完成的核验任务，不是第四类结论。两阶段共 5 次模型请求、6 次新增工具调用；复用了此前核实的源码。</p>
    <p><b>扩到其他机制的边界：</b>复用图中的判定合同和两阶段流程；每项需独立准备相关论文页、对齐入口、仓库版本与必要依赖。
    当前准备脚本仍固定 M02，下一步须参数化机制 ID 和证据准备，不能直接宣称剩余机制已经具备正确调用路径。
    不重新发现机制，不从源码反向改写论文声明，不运行目标系统。</p>
    <p><a href="#conformance-overview">查看 M02 本轮结果</a> · <a href="#conformance-trace">查看实际 prompts 与完整代码</a> · <a href="#continuation-all">查看其他机制与行为草稿</a></p></section>'''

    if batch_summary:
        html=html.replace('其余 19 项共 192 条尚未完成新版代码核验。',f"新增机制 {batch_summary['reviewed_mechanisms']}/19 项已运行调查与复核；{batch_summary['completed_behaviors']}/192 条形成三类判定，{batch_summary['pending_behaviors']} 条核验待办。")
        html=html.replace('新版 Pi 一致性流程目前只跑通传播机制 M02 的 14 条。','传播机制 M02 沿用此前 14 条核验记录。')
        html=html.replace('当前准备脚本仍固定 M02，下一步须参数化机制 ID 和证据准备，不能直接宣称剩余机制已经具备正确调用路径。','准备脚本已参数化机制 ID；新增机制自主选择调用入口，并可只读检索 primary、NNI、NNFusion 和 TVM 的固定版本。各项入口以实际工具记录为准。')
        html=html.replace('查看其他机制与行为草稿','查看冻结的行为草稿')
        html=html.replace('<p><b>扩到其他机制的边界：</b>','<p><b>本轮批量核验：</b>')
    return html
