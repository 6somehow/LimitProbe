"""Render README workflow PNGs: python3 scripts/render_workflow.py (Pillow)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "docs" / "workflow"
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
INK = "#172c43"


def render(name, title, subtitle, steps, footer, fill):
    scale = 2
    width, height = 1080, 190 + len(steps) * 132 + 80
    im = Image.new("RGB", (width * scale, height * scale), "#faf9f5")
    d = ImageDraw.Draw(im)

    def text(x, y, s, size=24, color=INK):
        d.text((x * scale, y * scale), s,
               font=ImageFont.truetype(FONT, size * scale), fill=color)

    def rect(box, color, radius=14):
        d.rounded_rectangle(tuple(v * scale for v in box), radius=radius * scale, fill=color)

    rect((0, 0, width, 116), INK, 0)
    text(42, 20, title, 32, "white")
    text(42, 70, subtitle, 20, "#d6e0ec")
    for i, (heading, detail) in enumerate(steps):
        y = 152 + i * 132
        rect((42, y, 1038, y + 98), fill)
        text(64, y + 12, f"{i + 1:02d}  {heading}", 26)
        text(64, y + 55, detail, 21)
        if i < len(steps) - 1 and not (name == "03-code.png" and i == 3):
            x, top = 540 * scale, (y + 103) * scale
            d.line((x, top, x, top + 20 * scale), fill=INK, width=3 * scale)
            d.polygon([(x, top + 25 * scale), (x - 7 * scale, top + 17 * scale),
                       (x + 7 * scale, top + 17 * scale)], fill=INK)
    text(42, height - 66, footer, 20)
    OUT.mkdir(parents=True, exist_ok=True)
    im.save(OUT / name, optimize=True)


if __name__ == "__main__":
    render("01-mechanisms.png", "阶段 1 / 4：独立发现机制", "输入：论文逐页文字 + 原始页面图像；这一阶段不输入源码", [
        ("同一篇论文，独立读取两次（k = 2）", "A 按章节阅读；B 按系统输入输出流程阅读；彼此不看结果。"),
        ("合并两个候选集合", "合并别名，保留不同职责、父子关系、原文出处和适用前提。"),
        ("确定机制清单", "输出：后续拆行为使用的统一机制；保留两次原始返回。"),
    ], "衔接 → 将统一机制及相关论文页交给阶段 2。", "#fff0c9")
    render("02-behaviors.png", "阶段 2 / 4：拆行为并在机制内复核", "输入：统一机制 + 对应论文原页；继续不输入源码", [
        ("初次拆行为", "每条描述一个可核验动作，记录原文、页码、条件和推断标记。"),
        ("独立列出机制应有步骤", "另一请求阅读相关原页，不看初次行为清单，避免被清单锚定。"),
        ("两份清单对账并做原子性复核", "补初始化、条件、更新、分支或返回步骤；拆开复合行为。"),
        ("冻结行为清单", "输出：行为 ID、论文证据及适用前提；源码调查不反向改写要求。"),
    ], "衔接 → 按机制把冻结行为与论文证据交给 Pi。", "#fff0c9")
    render("03-code.png", "阶段 3 / 4：Pi 调查源码并逐条核验", "输入：机制 + 相关原文 + 冻结行为 + 固定 commit 的仓库", [
        ("每个机制一个 Pi 会话，自主使用工具", "搜索符号、读取源码、追查静态调用关系和必要依赖。"),
        ("对齐实际入口、配置和实现路径", "逐条比较论文要求与代码事实，检查条件及可能的等价实现。"),
        ("模型语义复核 + 程序来源检查", "模型检查判断依据；程序检查行为 ID、字段及实际已读行范围。"),
        ("完成核验 → 三类结论", "supports 支持  /  deviates 不符  /  absent 该路径未实现。"),
        ("另一分支：未完成核验 → 待办", "pending + null verdict；不是第四类结论，也不计入差异候选。"),
    ], "边界：静态核验，不运行目标系统；单一路径缺失不等于整个仓库缺失。", "#e3eef9")
    render("04-delivery.png", "阶段 4 / 4：组织证据并交接", "输入：冻结声明 + 逐条源码判断；并行支线：论文范围与实验配置", [
        ("只从论文提取范围和实验配置，并复核", "与源码调查并行开展；源码用于核对术语映射，不改写论文声明。"),
        ("组织完整证据，归组差异候选", "仅对不符、未实现归组；保留支持证据、适用条件和核验待办。"),
        ("适配共享接口", "paper_side.json：claims / scope / eval_points / bindings。"),
        ("交给 Wanting 读取和整合", "另附逐条判断、源码证据、候选及未激活映射；不硬塞进共享枚举。"),
    ], "全程留档：实际 prompt、返回、工具读取、失败与修正记录。", "#ece5f3")
