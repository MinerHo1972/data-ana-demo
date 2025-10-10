import os
import subprocess

# 尝试使用pandoc将markdown转换为PDF
def convert_markdown_to_pdf(md_file, pdf_file):
    try:
        # 检查pandoc是否可用
        result = subprocess.run(['pandoc', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("使用pandoc转换PDF...")
            cmd = f'pandoc "{md_file}" -o "{pdf_file}" --pdf-engine=xelatex -V CJKmainfont="SimHei" --standalone'
            subprocess.run(cmd, shell=True, check=True)
            print(f"PDF已生成: {pdf_file}")
            return True
        else:
            print("pandoc不可用，尝试其他方法...")
            return False
    except FileNotFoundError:
        print("pandoc未安装，尝试其他方法...")
        return False
    except Exception as e:
        print(f"pandoc转换失败: {e}")
        return False

# 尝试使用WeasyPrint
def convert_with_weasyprint(md_file, pdf_file):
    try:
        import markdown
        from weasyprint import HTML, CSS

        print("使用WeasyPrint转换PDF...")

        # 读取markdown文件
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # 转换为HTML
        html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

        # 添加CSS样式和HTML结构
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>数据分析报告</title>
            <style>
                body {{
                    font-family: "Microsoft YaHei", "SimHei", sans-serif;
                    line-height: 1.6;
                    margin: 40px;
                    font-size: 12pt;
                }}
                h1 {{ font-size: 24pt; page-break-before: always; }}
                h1:first-of-type {{ page-break-before: auto; }}
                h2 {{ font-size: 18pt; }}
                h3 {{ font-size: 14pt; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .page-break {{ page-break-before: always; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        # 生成PDF
        HTML(string=full_html).write_pdf(pdf_file)
        print(f"PDF已生成: {pdf_file}")
        return True

    except ImportError:
        print("WeasyPrint未安装，尝试其他方法...")
        return False
    except Exception as e:
        print(f"WeasyPrint转换失败: {e}")
        return False

# 如果以上方法都失败，创建一个简单的文本报告
def create_simple_report():
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        print("使用ReportLab创建简单的PDF报告...")

        # 尝试注册中文字体
        try:
            # Windows系统常见中文字体路径
            font_paths = [
                "C:/Windows/Fonts/simhei.ttf",
                "C:/Windows/Fonts/simsun.ttc",
                "C:/Windows/Fonts/msyh.ttc"
            ]

            font_registered = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('SimHei', font_path))
                        font_registered = True
                        print(f"成功注册字体: {font_path}")
                        break
                    except:
                        continue

            if not font_registered:
                print("未能注册中文字体，使用默认字体")

        except Exception as e:
            print(f"字体注册失败: {e}")

        # 创建PDF
        c = canvas.Canvas("数据分析报告.pdf", pagesize=A4)
        width, height = A4

        # 标题
        c.setFont("SimHei" if font_registered else "Helvetica-Bold", 20)
        c.drawString(100, height - 100, "好翔来仓库订货数据分析报告")

        # 报告内容（简化版）
        c.setFont("SimHei" if font_registered else "Helvetica", 12)
        y_position = height - 150

        report_lines = [
            "报告概要",
            "=" * 40,
            "分析日期: 2025年10月5日",
            "数据来源: haoxianglai.xlsx",
            "分析期间: 2025年7月9日 - 2025年10月5日（88天）",
            "预测期间: 2025年11月5日 - 2025年12月4日（未来30天）",
            "",
            "数据概况",
            "=" * 40,
            f"数据记录总数: 252条",
            f"经营组织数量: 7个",
            f"省份数量: 23个",
            f"仓库数量: 47个",
            f"平均订货量: 118.84件",
            f"订货量中位数: 62.50件",
            f"最大单次订货量: 730件",
            f"最小单次订货量: 20件",
            "",
            "主要发现",
            "=" * 40,
            "1. 订货分布不均：少数省份贡献主要订货量",
            "2. 订货量波动性较大：需要加强库存管理",
            "3. 无明显季节性：在当前时间范围内",
            "4. 组织集中度高：华中华南和华南占主要份额",
            "",
            "预测结果",
            "=" * 40,
            "预测仓库总数: 47个",
            "详细预测结果请参考: 订货预测结果.xlsx",
            "",
            "业务建议",
            "=" * 40,
            "1. 重点区域管理：加强江苏、山东、安徽等重点省份供应链",
            "2. 库存优化：建立安全库存机制应对波动",
            "3. 数据完善：收集更长时间历史数据",
            "4. 网络优化：考虑低频仓库运营效率提升",
            "",
            "风险提示",
            "=" * 40,
            "- 预测基于历史数据，实际情况可能存在变化",
            "- 外部因素影响未充分考虑",
            "- 建议结合具体业务情况综合考虑",
            "",
            "输出文件",
            "=" * 40,
            "1. 数据初步探察.xlsx",
            "2. 订货预测结果.xlsx",
            "3. 关键统计指标.xlsx",
            "4. 数据分析报告图表.png"
        ]

        for line in report_lines:
            if y_position < 50:  # 换页
                c.showPage()
                y_position = height - 50

            if font_registered:
                c.drawString(50, y_position, line)
            else:
                c.drawString(50, y_position, line.encode('ascii', 'ignore').decode('ascii'))

            y_position -= 20

        c.save()
        print("简版PDF报告已生成: 数据分析报告.pdf")
        return True

    except ImportError:
        print("ReportLab未安装")
        return False
    except Exception as e:
        print(f"ReportLab创建失败: {e}")
        return False

# 主转换流程
if __name__ == "__main__":
    md_file = "数据分析报告.md"
    pdf_file = "数据分析报告.pdf"

    if not os.path.exists(md_file):
        print(f"找不到文件: {md_file}")
        exit(1)

    # 尝试各种转换方法
    success = False

    # 方法1: pandoc
    success = convert_markdown_to_pdf(md_file, pdf_file)

    # 方法2: WeasyPrint
    if not success:
        success = convert_with_weasyprint(md_file, pdf_file)

    # 方法3: ReportLab
    if not success:
        success = create_simple_report()

    if not success:
        print("PDF转换失败，请安装以下工具之一:")
        print("1. Pandoc (推荐): https://pandoc.org/installing.html")
        print("2. WeasyPrint: pip install weasyprint markdown")
        print("3. ReportLab: pip install reportlab")
        print("或者手动将markdown文件转换为PDF")
    else:
        print("PDF转换完成!")