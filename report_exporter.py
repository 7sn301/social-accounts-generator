"""
📑 Report Exporter - تصدير تقارير احترافية بصيغ Word و PowerPoint
================================================================
يُنشئ تقارير منسقة كاملة تحتوي:
  ✅ صور المنشورات والبروفايلات
  ✅ كل البيانات المستخرجة (موقع، VPN، تحليل)
  ✅ تنسيق RTL عربي احترافي
  ✅ ألوان وأيقونات للحالات
"""
import io
import requests
from datetime import datetime

# Word
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# PowerPoint
from pptx import Presentation
from pptx.util import Inches as PptxInches, Pt as PptxPt, Emu
from pptx.dml.color import RGBColor as PptxRGB
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE


# ===========================================
# Helpers
# ===========================================

def download_image(url, timeout=10):
    """تحميل صورة من URL وإرجاع BytesIO"""
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            return io.BytesIO(r.content)
    except Exception:
        pass
    return None


def set_rtl(paragraph):
    """تطبيق RTL على paragraph"""
    pPr = paragraph._p.get_or_add_pPr()
    bidi = OxmlElement('w:bidi')
    bidi.set(qn('w:val'), '1')
    pPr.append(bidi)


def set_cell_rtl(cell):
    """تطبيق RTL على خلية"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    bidi = OxmlElement('w:bidiVisual')
    bidi.set(qn('w:val'), '1')
    tcPr.append(bidi)


def shade_cell(cell, hex_color):
    """تظليل خلية بلون"""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), hex_color)
    tc_pr.append(shd)


def get_risk_color(risk_score):
    """يعيد لون حسب درجة الخطر"""
    if risk_score >= 80:
        return 'DC2626', 'FEE2E2'  # أحمر داكن، خلفية وردية
    elif risk_score >= 50:
        return 'EA580C', 'FFEDD5'  # برتقالي
    elif risk_score >= 25:
        return 'CA8A04', 'FEF3C7'  # أصفر
    else:
        return '16A34A', 'D1FAE5'  # أخضر


# ===========================================
# Word Report
# ===========================================

def generate_word_report(results, title="تقرير تحليل المنشورات"):
    """
    ينشئ تقرير Word احترافي
    
    results: قائمة من dictionaries، كل واحد يحتوي:
      - tweet: dict (بيانات التغريدة)
      - photos: list (روابط صور)
      - image_analysis: dict (تحليل Gemini)
      - vpn_check: dict (تشخيص VPN)
      - account_country, post_country
    """
    doc = Document()
    
    # ضبط الأسلوب الافتراضي للخط العربي
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)
    rPr = style.element.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:cs'), 'Arial')
    rFonts.set(qn('w:hAnsi'), 'Arial')
    rPr.append(rFonts)
    
    # هوامش
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)
    
    # ===== الصفحة الأولى: العنوان =====
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_rtl(title_para)
    title_run = title_para.add_run(title)
    title_run.font.size = Pt(28)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(0x1E, 0x40, 0xAF)
    
    subtitle_para = doc.add_paragraph()
    subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_rtl(subtitle_para)
    subtitle_run = subtitle_para.add_run(
        f"📅 تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    subtitle_run.font.size = Pt(12)
    subtitle_run.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
    
    doc.add_paragraph()  # مسافة
    
    # ===== الملخص التنفيذي =====
    summary_heading = doc.add_paragraph()
    set_rtl(summary_heading)
    h_run = summary_heading.add_run("📊 الملخص التنفيذي")
    h_run.font.size = Pt(18)
    h_run.font.bold = True
    h_run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    
    total = len([r for r in results if r.get("success", True) is not False])
    vpn_count = sum(1 for r in results if r.get("vpn_check", {}).get("verdict") == "likely_vpn")
    matched = sum(1 for r in results if r.get("vpn_check", {}).get("verdict") == "matched")
    travel = sum(1 for r in results if r.get("vpn_check", {}).get("verdict") in ("travel", "expat_visit"))
    with_post_loc = sum(1 for r in results if r.get("post_country"))
    
    # جدول الإحصائيات
    stats_table = doc.add_table(rows=2, cols=5)
    stats_table.alignment = WD_TABLE_ALIGNMENT.RIGHT
    stats_table.style = 'Light Grid Accent 1'
    
    headers = ["الإجمالي", "تطابق ✅", "احتمال VPN 🚨", "سفر/مغترب ✈️", "موقع صورة 📸"]
    values = [str(total), str(matched), str(vpn_count), str(travel), str(with_post_loc)]
    
    for i, (h, v) in enumerate(zip(headers, values)):
        cell_h = stats_table.cell(0, i)
        cell_h.text = h
        for p in cell_h.paragraphs:
            set_rtl(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.bold = True
                run.font.size = Pt(11)
        shade_cell(cell_h, '1E3A8A')
        for p in cell_h.paragraphs:
            for run in p.runs:
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        
        cell_v = stats_table.cell(1, i)
        cell_v.text = v
        for p in cell_v.paragraphs:
            set_rtl(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.size = Pt(20)
                run.font.bold = True
    
    doc.add_paragraph()
    doc.add_page_break()
    
    # ===== التفاصيل لكل منشور =====
    for idx, r in enumerate(results, 1):
        if not r.get("success", True):
            continue
        
        tweet = r.get("tweet", {})
        vpn = r.get("vpn_check", {})
        img_an = r.get("image_analysis", {}) or {}
        agg = (img_an.get("aggregate") or {})
        
        # عنوان المنشور
        post_heading = doc.add_paragraph()
        set_rtl(post_heading)
        h_run = post_heading.add_run(f"🔍 المنشور #{idx}")
        h_run.font.size = Pt(20)
        h_run.font.bold = True
        h_run.font.color.rgb = RGBColor(0x1E, 0x40, 0xAF)
        
        # معلومات الحساب الأساسية
        info_table = doc.add_table(rows=0, cols=2)
        info_table.alignment = WD_TABLE_ALIGNMENT.RIGHT
        info_table.style = 'Light List Accent 1'
        info_table.autofit = False
        
        # صف الصورة + الاسم
        info_data = [
            ("👤 اسم المستخدم", f"@{tweet.get('user_screen_name', '-')}"),
            ("📛 الاسم", tweet.get('user_name', '-')),
            ("🆔 User ID", tweet.get('user_id', '-')),
            ("✓ موثّق", "نعم" if tweet.get('user_blue_verified') else "لا"),
            ("📅 تاريخ النشر", tweet.get('created_at', '-')),
            ("🌐 اللغة", tweet.get('lang_name_ar', tweet.get('lang', '-'))),
            ("❤️ إعجابات", str(tweet.get('favorite_count', 0))),
            ("💬 ردود", str(tweet.get('conversation_count', 0))),
            ("🔗 الرابط", r.get('url', '-')),
        ]
        
        for label, value in info_data:
            row = info_table.add_row()
            cell_l = row.cells[0]
            cell_v = row.cells[1]
            
            cell_l.text = label
            for p in cell_l.paragraphs:
                set_rtl(p)
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                for run in p.runs:
                    run.font.bold = True
                    run.font.size = Pt(10)
            shade_cell(cell_l, 'EFF6FF')
            
            cell_v.text = str(value)[:200]
            for p in cell_v.paragraphs:
                set_rtl(p)
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                for run in p.runs:
                    run.font.size = Pt(10)
        
        doc.add_paragraph()
        
        # صورة البروفايل
        if tweet.get("user_profile_image"):
            pp_para = doc.add_paragraph()
            set_rtl(pp_para)
            pp_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            label = pp_para.add_run("🖼️ صورة البروفايل: ")
            label.font.bold = True
            
            img_data = download_image(tweet["user_profile_image"])
            if img_data:
                try:
                    img_para = doc.add_paragraph()
                    img_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    img_run = img_para.add_run()
                    img_run.add_picture(img_data, width=Inches(1.2))
                except Exception:
                    pass
        
        # نص التغريدة
        if tweet.get("text"):
            text_heading = doc.add_paragraph()
            set_rtl(text_heading)
            t_run = text_heading.add_run("📝 نص التغريدة:")
            t_run.font.bold = True
            t_run.font.size = Pt(12)
            
            text_para = doc.add_paragraph()
            set_rtl(text_para)
            text_para.paragraph_format.left_indent = Cm(0.5)
            text_para.paragraph_format.right_indent = Cm(0.5)
            text_run = text_para.add_run(tweet["text"][:500])
            text_run.font.size = Pt(11)
            text_run.font.italic = True
        
        # ===== المقارنة: حساب vs منشور =====
        cmp_heading = doc.add_paragraph()
        set_rtl(cmp_heading)
        c_run = cmp_heading.add_run("🌍 مقارنة المواقع")
        c_run.font.size = Pt(14)
        c_run.font.bold = True
        c_run.font.color.rgb = RGBColor(0x7C, 0x3A, 0xED)
        
        cmp_table = doc.add_table(rows=2, cols=2)
        cmp_table.alignment = WD_TABLE_ALIGNMENT.RIGHT
        cmp_table.style = 'Light Grid Accent 4'
        
        cmp_table.cell(0, 0).text = "🏠 موقع الحساب (المعلن)"
        cmp_table.cell(0, 1).text = "📸 موقع التصوير (الفعلي)"
        for i in range(2):
            cell = cmp_table.cell(0, i)
            shade_cell(cell, '7C3AED')
            for p in cell.paragraphs:
                set_rtl(p)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        
        # موقع الحساب
        account_text = ""
        if tweet.get("user_location_field"):
            account_text += f"حقل الموقع: {tweet['user_location_field']}\n"
        if tweet.get("region_flag"):
            account_text += f"\n{tweet['region_flag']} {tweet.get('region_name_ar', '')}\n"
            account_text += f"ثقة: {tweet.get('region_confidence', 0)}%"
        if not account_text:
            account_text = "لم يحدد الحساب موقعاً"
        
        cmp_table.cell(1, 0).text = account_text
        for p in cmp_table.cell(1, 0).paragraphs:
            set_rtl(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.size = Pt(11)
        
        # موقع المنشور
        post_text = ""
        if agg.get("country_code"):
            from x_analyzer import X_REGION_MAP
            ci = X_REGION_MAP.get(agg["country_code"], {})
            post_text += f"{ci.get('flag', '🌍')} {ci.get('ar', agg.get('country_name', ''))}\n"
            if agg.get("city"):
                post_text += f"🏙️ {agg['city']}\n"
            if agg.get("neighborhood"):
                post_text += f"📍 {agg['neighborhood']}\n"
            post_text += f"\nثقة: {agg.get('confidence_score', 0)}%"
        else:
            post_text = "لم يتم استخراج موقع من الصور"
        
        cmp_table.cell(1, 1).text = post_text
        for p in cmp_table.cell(1, 1).paragraphs:
            set_rtl(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.size = Pt(11)
        
        doc.add_paragraph()
        
        # ===== تشخيص VPN =====
        risk_score = vpn.get("risk_score", 0)
        text_color, bg_color = get_risk_color(risk_score)
        
        vpn_heading = doc.add_paragraph()
        set_rtl(vpn_heading)
        v_run = vpn_heading.add_run(f"{vpn.get('icon', '🔍')} تشخيص VPN")
        v_run.font.size = Pt(14)
        v_run.font.bold = True
        v_run.font.color.rgb = RGBColor.from_string(text_color)
        
        # صندوق التشخيص
        verdict_table = doc.add_table(rows=1, cols=1)
        verdict_table.alignment = WD_TABLE_ALIGNMENT.RIGHT
        cell = verdict_table.cell(0, 0)
        shade_cell(cell, bg_color)
        cell.text = vpn.get('verdict_ar', 'بدون تشخيص')
        for p in cell.paragraphs:
            set_rtl(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.size = Pt(13)
                run.font.bold = True
                run.font.color.rgb = RGBColor.from_string(text_color)
        
        # درجة الخطر
        risk_para = doc.add_paragraph()
        set_rtl(risk_para)
        risk_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        rk_run = risk_para.add_run(f"📊 درجة الخطر: {risk_score}/100")
        rk_run.font.size = Pt(12)
        rk_run.font.bold = True
        
        # المؤشرات
        if vpn.get("indicators"):
            ind_heading = doc.add_paragraph()
            set_rtl(ind_heading)
            ih_run = ind_heading.add_run("🔍 الأدلة والمؤشرات:")
            ih_run.font.bold = True
            ih_run.font.size = Pt(11)
            
            for ind in vpn.get("indicators", []):
                ind_para = doc.add_paragraph(style='List Bullet')
                set_rtl(ind_para)
                ind_run = ind_para.add_run(ind)
                ind_run.font.size = Pt(10)
        
        # توصية
        if vpn.get("recommendation"):
            rec_para = doc.add_paragraph()
            set_rtl(rec_para)
            rec_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            rec_para.paragraph_format.left_indent = Cm(0.5)
            rec_para.paragraph_format.right_indent = Cm(0.5)
            rec_run = rec_para.add_run(f"💡 التوصية: {vpn['recommendation']}")
            rec_run.font.size = Pt(11)
            rec_run.font.bold = True
            rec_run.font.color.rgb = RGBColor(0x1E, 0x40, 0xAF)
        
        doc.add_paragraph()
        
        # ===== الأدلة من الصور =====
        if agg.get("key_evidence") or agg.get("observations"):
            ev_heading = doc.add_paragraph()
            set_rtl(ev_heading)
            e_run = ev_heading.add_run("🔬 تحليل الذكاء الاصطناعي للصور")
            e_run.font.size = Pt(14)
            e_run.font.bold = True
            e_run.font.color.rgb = RGBColor(0x05, 0x96, 0x69)
            
            if agg.get("reasoning"):
                reason_para = doc.add_paragraph()
                set_rtl(reason_para)
                reason_run = reason_para.add_run(f"🧠 الاستنتاج: {agg['reasoning']}")
                reason_run.font.size = Pt(11)
                reason_run.font.italic = True
            
            if agg.get("key_evidence"):
                ke_heading = doc.add_paragraph()
                set_rtl(ke_heading)
                keh = ke_heading.add_run("🔑 الأدلة الرئيسية:")
                keh.font.bold = True
                
                for ev in agg.get("key_evidence", []):
                    p = doc.add_paragraph(style='List Bullet')
                    set_rtl(p)
                    run = p.add_run(ev)
                    run.font.size = Pt(10)
            
            if agg.get("observations"):
                obs_heading = doc.add_paragraph()
                set_rtl(obs_heading)
                obh = obs_heading.add_run("👁️ ملاحظات:")
                obh.font.bold = True
                
                for obs in agg.get("observations", [])[:5]:
                    p = doc.add_paragraph(style='List Bullet')
                    set_rtl(p)
                    run = p.add_run(obs)
                    run.font.size = Pt(10)
        
        # ===== صور المنشور =====
        if r.get("photos"):
            ph_heading = doc.add_paragraph()
            set_rtl(ph_heading)
            ph_run = ph_heading.add_run("🖼️ صور المنشور المُحلّلة")
            ph_run.font.size = Pt(14)
            ph_run.font.bold = True
            
            for photo_url in r.get("photos", [])[:3]:
                img_data = download_image(photo_url)
                if img_data:
                    try:
                        img_para = doc.add_paragraph()
                        img_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        img_run = img_para.add_run()
                        img_run.add_picture(img_data, width=Inches(4.5))
                    except Exception:
                        pass
        
        # فاصل بين المنشورات
        if idx < len(results):
            doc.add_page_break()
    
    # حفظ في BytesIO
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


# ===========================================
# PowerPoint Report
# ===========================================

def generate_pptx_report(results, title="تقرير تحليل المنشورات"):
    """ينشئ عرض PowerPoint احترافي"""
    prs = Presentation()
    prs.slide_width = PptxInches(13.33)  # 16:9
    prs.slide_height = PptxInches(7.5)
    
    SLIDE_W = prs.slide_width
    SLIDE_H = prs.slide_height
    
    # ألوان
    PRIMARY = PptxRGB(0x1E, 0x40, 0xAF)
    ACCENT = PptxRGB(0x7C, 0x3A, 0xED)
    SUCCESS = PptxRGB(0x16, 0xA3, 0x4A)
    DANGER = PptxRGB(0xDC, 0x26, 0x26)
    WARN = PptxRGB(0xEA, 0x58, 0x0C)
    DARK = PptxRGB(0x1F, 0x29, 0x37)
    LIGHT = PptxRGB(0xF8, 0xFA, 0xFC)
    
    # ===== شريحة العنوان =====
    slide_layout = prs.slide_layouts[6]  # blank
    slide = prs.slides.add_slide(slide_layout)
    
    # خلفية متدرجة (مستطيل ملون)
    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = PRIMARY
    bg.line.fill.background()
    
    # العنوان
    title_box = slide.shapes.add_textbox(
        PptxInches(1), PptxInches(2.5),
        PptxInches(11.33), PptxInches(1.5)
    )
    tf = title_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = title
    run.font.size = PptxPt(48)
    run.font.bold = True
    run.font.color.rgb = PptxRGB(0xFF, 0xFF, 0xFF)
    run.font.name = 'Arial'
    
    # تاريخ
    date_box = slide.shapes.add_textbox(
        PptxInches(1), PptxInches(4.2),
        PptxInches(11.33), PptxInches(0.6)
    )
    df = date_box.text_frame
    pp = df.paragraphs[0]
    pp.alignment = PP_ALIGN.CENTER
    rd = pp.add_run()
    rd.text = f"📅 {datetime.now().strftime('%Y-%m-%d')}"
    rd.font.size = PptxPt(20)
    rd.font.color.rgb = PptxRGB(0xE2, 0xE8, 0xF0)
    
    # ===== شريحة الإحصائيات =====
    slide = prs.slides.add_slide(slide_layout)
    
    # عنوان
    h_box = slide.shapes.add_textbox(
        PptxInches(0.5), PptxInches(0.3),
        PptxInches(12.33), PptxInches(0.8)
    )
    h_p = h_box.text_frame.paragraphs[0]
    h_p.alignment = PP_ALIGN.CENTER
    h_r = h_p.add_run()
    h_r.text = "📊 الملخص التنفيذي"
    h_r.font.size = PptxPt(36)
    h_r.font.bold = True
    h_r.font.color.rgb = PRIMARY
    
    total = len([r for r in results if r.get("success", True) is not False])
    vpn_count = sum(1 for r in results if r.get("vpn_check", {}).get("verdict") == "likely_vpn")
    matched = sum(1 for r in results if r.get("vpn_check", {}).get("verdict") == "matched")
    travel = sum(1 for r in results if r.get("vpn_check", {}).get("verdict") in ("travel", "expat_visit"))
    with_post_loc = sum(1 for r in results if r.get("post_country"))
    
    # 5 بطاقات إحصائيات
    stats = [
        ("📋", "الإجمالي", total, PRIMARY),
        ("✅", "تطابق", matched, SUCCESS),
        ("🚨", "احتمال VPN", vpn_count, DANGER),
        ("✈️", "سفر/مغترب", travel, WARN),
        ("📸", "موقع صورة", with_post_loc, ACCENT),
    ]
    
    card_w = PptxInches(2.4)
    card_h = PptxInches(2.5)
    spacing = PptxInches(0.1)
    total_w = card_w * 5 + spacing * 4
    start_x = (SLIDE_W - total_w) / 2
    y = PptxInches(2.5)
    
    for i, (icon, label, value, color) in enumerate(stats):
        x = start_x + (card_w + spacing) * i
        
        # كرت الخلفية
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, card_w, card_h)
        card.fill.solid()
        card.fill.fore_color.rgb = color
        card.line.fill.background()
        
        # الأيقونة
        icon_box = slide.shapes.add_textbox(x, y + PptxInches(0.3), card_w, PptxInches(0.8))
        ip = icon_box.text_frame.paragraphs[0]
        ip.alignment = PP_ALIGN.CENTER
        ir = ip.add_run()
        ir.text = icon
        ir.font.size = PptxPt(40)
        
        # القيمة
        val_box = slide.shapes.add_textbox(x, y + PptxInches(1.1), card_w, PptxInches(0.7))
        vp = val_box.text_frame.paragraphs[0]
        vp.alignment = PP_ALIGN.CENTER
        vr = vp.add_run()
        vr.text = str(value)
        vr.font.size = PptxPt(40)
        vr.font.bold = True
        vr.font.color.rgb = PptxRGB(0xFF, 0xFF, 0xFF)
        
        # التسمية
        lbl_box = slide.shapes.add_textbox(x, y + PptxInches(1.85), card_w, PptxInches(0.5))
        lp = lbl_box.text_frame.paragraphs[0]
        lp.alignment = PP_ALIGN.CENTER
        lr = lp.add_run()
        lr.text = label
        lr.font.size = PptxPt(16)
        lr.font.color.rgb = PptxRGB(0xFF, 0xFF, 0xFF)
        lr.font.bold = True
    
    # ===== شريحة لكل منشور =====
    for idx, r in enumerate(results, 1):
        if not r.get("success", True):
            continue
        
        tweet = r.get("tweet", {})
        vpn = r.get("vpn_check", {})
        img_an = r.get("image_analysis", {}) or {}
        agg = (img_an.get("aggregate") or {})
        
        slide = prs.slides.add_slide(slide_layout)
        
        # شريط علوي ملون
        risk_score = vpn.get("risk_score", 0)
        if risk_score >= 80:
            top_color = DANGER
        elif risk_score >= 50:
            top_color = WARN
        elif risk_score >= 25:
            top_color = PptxRGB(0xCA, 0x8A, 0x04)
        else:
            top_color = SUCCESS
        
        top_bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, PptxInches(0.6)
        )
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = top_color
        top_bar.line.fill.background()
        
        # عنوان المنشور
        h_box = slide.shapes.add_textbox(
            PptxInches(0.3), PptxInches(0.07),
            PptxInches(12.7), PptxInches(0.5)
        )
        hp = h_box.text_frame.paragraphs[0]
        hp.alignment = PP_ALIGN.RIGHT
        hr = hp.add_run()
        hr.text = f"🔍 المنشور #{idx} - @{tweet.get('user_screen_name', '')}"
        hr.font.size = PptxPt(22)
        hr.font.bold = True
        hr.font.color.rgb = PptxRGB(0xFF, 0xFF, 0xFF)
        
        # ===== العمود الأيمن: معلومات الحساب =====
        # صورة البروفايل
        if tweet.get("user_profile_image"):
            img_data = download_image(tweet["user_profile_image"])
            if img_data:
                try:
                    slide.shapes.add_picture(
                        img_data,
                        PptxInches(11.3), PptxInches(0.9),
                        width=PptxInches(1.7), height=PptxInches(1.7)
                    )
                except Exception:
                    pass
        
        # معلومات الحساب
        info_box = slide.shapes.add_textbox(
            PptxInches(7.5), PptxInches(0.9),
            PptxInches(3.7), PptxInches(2.5)
        )
        info_tf = info_box.text_frame
        info_tf.word_wrap = True
        
        info_lines = [
            (f"📛 {tweet.get('user_name', '-')}", 16, True, DARK),
            (f"@{tweet.get('user_screen_name', '-')}", 12, False, PptxRGB(0x64, 0x74, 0x8B)),
            (f"🆔 {tweet.get('user_id', '-')}", 11, False, DARK),
            ("", 8, False, DARK),
            (f"❤️ {tweet.get('favorite_count', 0)} إعجاب", 12, False, DARK),
            (f"💬 {tweet.get('conversation_count', 0)} رد", 12, False, DARK),
            (f"🌐 {tweet.get('lang_name_ar', '-')}", 12, False, DARK),
        ]
        
        for i, (text, size, bold, color) in enumerate(info_lines):
            p = info_tf.paragraphs[0] if i == 0 else info_tf.add_paragraph()
            p.alignment = PP_ALIGN.RIGHT
            run = p.add_run()
            run.text = text
            run.font.size = PptxPt(size)
            run.font.bold = bold
            run.font.color.rgb = color
        
        # ===== العمود الأوسط: المقارنة =====
        # موقع الحساب
        acc_box = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            PptxInches(3.5), PptxInches(0.9),
            PptxInches(3.7), PptxInches(2)
        )
        acc_box.fill.solid()
        acc_box.fill.fore_color.rgb = PptxRGB(0xEF, 0xF6, 0xFF)
        acc_box.line.color.rgb = PRIMARY
        acc_box.line.width = PptxPt(1.5)
        
        acc_tf = acc_box.text_frame
        acc_tf.word_wrap = True
        acc_tf.margin_top = PptxInches(0.15)
        acc_tf.margin_left = PptxInches(0.15)
        acc_tf.margin_right = PptxInches(0.15)
        
        p = acc_tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r1 = p.add_run()
        r1.text = "🏠 موقع الحساب (المعلن)"
        r1.font.size = PptxPt(14)
        r1.font.bold = True
        r1.font.color.rgb = PRIMARY
        
        if tweet.get("user_location_field"):
            p2 = acc_tf.add_paragraph()
            p2.alignment = PP_ALIGN.CENTER
            r2 = p2.add_run()
            r2.text = f"\n📝 {tweet['user_location_field']}"
            r2.font.size = PptxPt(11)
            r2.font.color.rgb = DARK
        
        if tweet.get("region_flag"):
            p3 = acc_tf.add_paragraph()
            p3.alignment = PP_ALIGN.CENTER
            r3 = p3.add_run()
            r3.text = f"\n{tweet['region_flag']} {tweet.get('region_name_ar', '')}"
            r3.font.size = PptxPt(20)
            r3.font.bold = True
            r3.font.color.rgb = DARK
            
            p4 = acc_tf.add_paragraph()
            p4.alignment = PP_ALIGN.CENTER
            r4 = p4.add_run()
            r4.text = f"ثقة: {tweet.get('region_confidence', 0)}%"
            r4.font.size = PptxPt(11)
            r4.font.color.rgb = PptxRGB(0x64, 0x74, 0x8B)
        
        # موقع المنشور
        post_box = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            PptxInches(3.5), PptxInches(3),
            PptxInches(3.7), PptxInches(2)
        )
        post_box.fill.solid()
        post_box.fill.fore_color.rgb = PptxRGB(0xFE, 0xF3, 0xC7)
        post_box.line.color.rgb = ACCENT
        post_box.line.width = PptxPt(1.5)
        
        post_tf = post_box.text_frame
        post_tf.word_wrap = True
        post_tf.margin_top = PptxInches(0.15)
        post_tf.margin_left = PptxInches(0.15)
        post_tf.margin_right = PptxInches(0.15)
        
        pp = post_tf.paragraphs[0]
        pp.alignment = PP_ALIGN.CENTER
        pr = pp.add_run()
        pr.text = "📸 موقع التصوير (الفعلي)"
        pr.font.size = PptxPt(14)
        pr.font.bold = True
        pr.font.color.rgb = ACCENT
        
        if agg.get("country_code"):
            from x_analyzer import X_REGION_MAP
            ci = X_REGION_MAP.get(agg["country_code"], {})
            pp2 = post_tf.add_paragraph()
            pp2.alignment = PP_ALIGN.CENTER
            pr2 = pp2.add_run()
            pr2.text = f"\n{ci.get('flag', '🌍')} {ci.get('ar', agg.get('country_name', ''))}"
            pr2.font.size = PptxPt(20)
            pr2.font.bold = True
            pr2.font.color.rgb = DARK
            
            if agg.get("city"):
                pp3 = post_tf.add_paragraph()
                pp3.alignment = PP_ALIGN.CENTER
                pr3 = pp3.add_run()
                pr3.text = f"🏙️ {agg['city']}"
                pr3.font.size = PptxPt(13)
                pr3.font.color.rgb = DARK
            
            pp4 = post_tf.add_paragraph()
            pp4.alignment = PP_ALIGN.CENTER
            pr4 = pp4.add_run()
            pr4.text = f"ثقة: {agg.get('confidence_score', 0)}%"
            pr4.font.size = PptxPt(11)
            pr4.font.color.rgb = PptxRGB(0x64, 0x74, 0x8B)
        else:
            pp_empty = post_tf.add_paragraph()
            pp_empty.alignment = PP_ALIGN.CENTER
            pre = pp_empty.add_run()
            pre.text = "\nلم يتم استخراج موقع"
            pre.font.size = PptxPt(12)
            pre.font.color.rgb = PptxRGB(0x94, 0xA3, 0xB8)
        
        # ===== العمود الأيسر: تشخيص VPN =====
        vpn_box = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            PptxInches(0.3), PptxInches(0.9),
            PptxInches(3.1), PptxInches(4.1)
        )
        vpn_box.fill.solid()
        # خلفية حسب الخطر
        if risk_score >= 80:
            vpn_box.fill.fore_color.rgb = PptxRGB(0xFE, 0xE2, 0xE2)
            vpn_border = DANGER
        elif risk_score >= 50:
            vpn_box.fill.fore_color.rgb = PptxRGB(0xFF, 0xED, 0xD5)
            vpn_border = WARN
        else:
            vpn_box.fill.fore_color.rgb = PptxRGB(0xD1, 0xFA, 0xE5)
            vpn_border = SUCCESS
        vpn_box.line.color.rgb = vpn_border
        vpn_box.line.width = PptxPt(2)
        
        vpn_tf = vpn_box.text_frame
        vpn_tf.word_wrap = True
        vpn_tf.margin_top = PptxInches(0.2)
        vpn_tf.margin_left = PptxInches(0.2)
        vpn_tf.margin_right = PptxInches(0.2)
        
        vpn_p = vpn_tf.paragraphs[0]
        vpn_p.alignment = PP_ALIGN.CENTER
        vpn_r = vpn_p.add_run()
        vpn_r.text = f"{vpn.get('icon', '🔍')} تشخيص VPN"
        vpn_r.font.size = PptxPt(16)
        vpn_r.font.bold = True
        vpn_r.font.color.rgb = vpn_border
        
        vpn_p2 = vpn_tf.add_paragraph()
        vpn_p2.alignment = PP_ALIGN.CENTER
        vpn_r2 = vpn_p2.add_run()
        vpn_r2.text = f"\n{vpn.get('verdict_ar', '')}"
        vpn_r2.font.size = PptxPt(13)
        vpn_r2.font.bold = True
        vpn_r2.font.color.rgb = DARK
        
        # درجة الخطر
        vpn_p3 = vpn_tf.add_paragraph()
        vpn_p3.alignment = PP_ALIGN.CENTER
        vpn_r3 = vpn_p3.add_run()
        vpn_r3.text = f"\n📊 درجة الخطر: {risk_score}/100"
        vpn_r3.font.size = PptxPt(13)
        vpn_r3.font.bold = True
        vpn_r3.font.color.rgb = vpn_border
        
        # المؤشرات
        if vpn.get("indicators"):
            vpn_p4 = vpn_tf.add_paragraph()
            vpn_p4.alignment = PP_ALIGN.RIGHT
            vpn_r4 = vpn_p4.add_run()
            vpn_r4.text = "\n🔍 المؤشرات:"
            vpn_r4.font.size = PptxPt(11)
            vpn_r4.font.bold = True
            vpn_r4.font.color.rgb = DARK
            
            for ind in vpn.get("indicators", [])[:4]:
                p_ind = vpn_tf.add_paragraph()
                p_ind.alignment = PP_ALIGN.RIGHT
                r_ind = p_ind.add_run()
                r_ind.text = f"• {ind[:60]}"
                r_ind.font.size = PptxPt(9)
                r_ind.font.color.rgb = DARK
        
        # ===== الصف السفلي: صور المنشور =====
        if r.get("photos"):
            ph_y = PptxInches(5.3)
            ph_h = PptxInches(2)
            
            ph_label = slide.shapes.add_textbox(
                PptxInches(0.3), PptxInches(5),
                PptxInches(12.7), PptxInches(0.3)
            )
            phl = ph_label.text_frame.paragraphs[0]
            phl.alignment = PP_ALIGN.RIGHT
            phlr = phl.add_run()
            phlr.text = "🖼️ صور المنشور المحلّلة"
            phlr.font.size = PptxPt(13)
            phlr.font.bold = True
            phlr.font.color.rgb = PRIMARY
            
            photos = r.get("photos", [])[:4]
            ph_count = len(photos)
            if ph_count > 0:
                ph_w = (PptxInches(12.7) - PptxInches(0.2) * (ph_count - 1)) / ph_count
                for i, photo_url in enumerate(photos):
                    ph_x = PptxInches(0.3) + (ph_w + PptxInches(0.2)) * i
                    img_data = download_image(photo_url)
                    if img_data:
                        try:
                            slide.shapes.add_picture(
                                img_data, ph_x, ph_y, width=ph_w, height=ph_h
                            )
                        except Exception:
                            pass
    
    # ===== شريحة الخاتمة =====
    slide = prs.slides.add_slide(slide_layout)
    end_bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H
    )
    end_bg.fill.solid()
    end_bg.fill.fore_color.rgb = PRIMARY
    end_bg.line.fill.background()
    
    end_box = slide.shapes.add_textbox(
        PptxInches(1), PptxInches(3),
        PptxInches(11.33), PptxInches(1.5)
    )
    ep = end_box.text_frame.paragraphs[0]
    ep.alignment = PP_ALIGN.CENTER
    er = ep.add_run()
    er.text = "✨ شكراً لاستخدامكم"
    er.font.size = PptxPt(48)
    er.font.bold = True
    er.font.color.rgb = PptxRGB(0xFF, 0xFF, 0xFF)
    
    sub_box = slide.shapes.add_textbox(
        PptxInches(1), PptxInches(4.5),
        PptxInches(11.33), PptxInches(0.6)
    )
    sp = sub_box.text_frame.paragraphs[0]
    sp.alignment = PP_ALIGN.CENTER
    sr = sp.add_run()
    sr.text = f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    sr.font.size = PptxPt(18)
    sr.font.color.rgb = PptxRGB(0xE2, 0xE8, 0xF0)
    
    # حفظ
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


# ===========================================
# Test
# ===========================================

if __name__ == "__main__":
    # بيانات اختبار
    test_results = [
        {
            "success": True,
            "url": "https://x.com/hureyaksa/status/123",
            "tweet": {
                "user_screen_name": "hureyaksa",
                "user_name": "أحمد الحريري",
                "user_id": "1234567890",
                "user_blue_verified": True,
                "user_location_field": "المملكة العربية السعودية",
                "region_flag": "🇸🇦",
                "region_name_ar": "السعودية",
                "region_confidence": 90,
                "text": "مرحبا من الرياض!",
                "lang_name_ar": "العربية",
                "lang": "ar",
                "favorite_count": 250,
                "conversation_count": 50,
                "user_profile_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Saudi_Arabia_flag.png/120px-Saudi_Arabia_flag.png",
                "created_at": "2025-05-20",
            },
            "photos": [],
            "image_analysis": {
                "aggregate": {
                    "country_code": "SA",
                    "country_name": "السعودية",
                    "city": "الرياض",
                    "confidence_score": 88,
                    "key_evidence": ["برج المملكة في الخلفية", "لوحة سيارة سعودية"],
                    "observations": ["معمار خليجي مميز", "لافتة بالعربية", "صحراء"],
                    "reasoning": "الصورة تظهر برج المملكة الشهير في الرياض",
                }
            },
            "vpn_check": {
                "verdict": "matched",
                "verdict_ar": "تطابق: الحساب والصورة من السعودية",
                "icon": "✅",
                "risk_score": 0,
                "indicators": ["موقع الحساب = موقع الصورة = السعودية"],
                "recommendation": "✅ موقع الحساب مؤكد ومتطابق",
            },
            "account_country": "SA",
            "post_country": "SA",
        },
        {
            "success": True,
            "url": "https://x.com/example/status/456",
            "tweet": {
                "user_screen_name": "example_user",
                "user_name": "مستخدم مغترب",
                "user_id": "9876543210",
                "user_blue_verified": False,
                "user_location_field": "England, United Kingdom",
                "region_flag": "🇬🇧",
                "region_name_ar": "المملكة المتحدة",
                "region_confidence": 90,
                "text": "صورة من بغداد",
                "lang_name_ar": "العربية",
                "lang": "ar",
                "favorite_count": 100,
                "conversation_count": 20,
                "created_at": "2025-05-21",
            },
            "photos": [],
            "image_analysis": {
                "aggregate": {
                    "country_code": "IQ",
                    "country_name": "العراق",
                    "city": "بغداد",
                    "confidence_score": 85,
                    "key_evidence": ["لافتة بالعربية", "نمط معمار عراقي"],
                    "observations": ["مكان شائع في بغداد"],
                    "reasoning": "صور من العراق",
                }
            },
            "vpn_check": {
                "verdict": "likely_vpn",
                "verdict_ar": "🚨 VPN محتمل جداً — الشخص على الأرجح في العراق",
                "icon": "🚨",
                "risk_score": 90,
                "indicators": [
                    "⚠️ موقع الحساب: GB",
                    "📸 موقع الصورة: IQ",
                    "🔍 اللغة عربية",
                    "🔍 الصورة من بلد عربي",
                ],
                "recommendation": "❗ احتمال VPN عالي جداً",
            },
            "account_country": "GB",
            "post_country": "IQ",
        },
    ]
    
    # توليد Word
    print("📝 توليد Word...")
    docx_bytes = generate_word_report(test_results, title="تقرير اختبار - تحليل المنشورات")
    with open("/tmp/test_report.docx", "wb") as f:
        f.write(docx_bytes)
    print(f"✓ {len(docx_bytes)} bytes saved to /tmp/test_report.docx")
    
    # توليد PowerPoint
    print("\n📊 توليد PowerPoint...")
    pptx_bytes = generate_pptx_report(test_results, title="تقرير اختبار - تحليل المنشورات")
    with open("/tmp/test_report.pptx", "wb") as f:
        f.write(pptx_bytes)
    print(f"✓ {len(pptx_bytes)} bytes saved to /tmp/test_report.pptx")
    
    print("\n✅ تم بنجاح!")
