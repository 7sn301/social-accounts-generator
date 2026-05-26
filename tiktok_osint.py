st.markdown("### 🕵️ محقق OSINT تيك توك")
st.markdown(
    """
    <div class="info-box">
    أدوات OSINT متخصصة لتيك توك: استنتاج الموقع من الفيديوهات، بناء روابط بحث جغرافي،
    تحليل نمط النشر الزمني، خريطة للدول المكتشفة، وروابط تحقق سريعة.
    </div>
    """,
    unsafe_allow_html=True,
)

if not TIKTOK_OSINT_AVAILABLE:
    st.error(f"tiktok_osint.py غير متوفر: {TIKTOK_OSINT_ERROR}")
    st.stop()

for _k in (
    "tt_osint_location_report",
    "tt_osint_timezone_report",
    "tt_osint_geo_search",
    "tt_osint_user_geo_links",
    "tt_osint_verification_links",
):
    st.session_state.setdefault(_k, None)

(sub1, sub2, sub3, sub4, sub5) = st.tabs([
    "🔍 تحديد الموقع عبر الفيديوهات",
    "🌐 بحث TikTok الجغرافي",
    "⏰ تحليل نمط النشر",
    "🗺️ خريطة المواقع",
    "🔗 روابط التحقق",
])

with sub1:
    st.markdown("💡 ملاحظة: يمكنك تحليل فيديوهاتك من تبويب تحليل الفيديو أولاً ثم العودة هنا")
    st.markdown(
        """
        <div class="info-box">
        هذا التبويب يحلل <code>locationCreated</code> من فيديوهاتك المحللة مسبقاً
        ويقارنها مع <code>author.region</code> للحصول على أفضل استنتاج ممكن.
        </div>
        """,
        unsafe_allow_html=True,
    )

    current_video_results = st.session_state.get("video_results") or []

    if current_video_results:
        st.success(f"تم العثور على {len(current_video_results)} نتيجة فيديو محفوظة في الجلسة")
        if st.button("🔍 تحليل مواقع الفيديوهات الموجودة", use_container_width=True, key="tt_osint_existing_videos"):
            st.session_state["tt_osint_location_report"] = infer_user_location_from_videos(current_video_results)

        location_report = st.session_state.get("tt_osint_location_report")
        if location_report:
            probable_code = location_report.get("probable_country_code", "")
            probable_flag = location_report.get("probable_flag", "🌍")
            probable_name = location_report.get("probable_country_name_ar", "غير محدد")
            confidence = int(location_report.get("confidence", 0) or 0)

            if probable_code and confidence >= 40:
                st.success(f"الموقع المحتمل: {probable_flag} {probable_name} — نسبة الثقة {confidence}%")
            elif probable_code:
                st.warning(f"النتيجة ما زالت مبدئية: {probable_flag} {probable_name} — نسبة الثقة {confidence}%")
            else:
                st.warning("لم يتم العثور على موقع مرجّح واضح من الفيديوهات الحالية")

            m1, m2, m3 = st.columns(3)
            m1.metric("عدد الفيديوهات", location_report.get("total_videos", 0))
            m2.metric("له موقع", location_report.get("videos_with_location", 0))
            m3.metric("نسبة الثقة", f"{confidence}%")

            loc_rows = location_report.get("location_counts", [])
            if loc_rows:
                df_loc = pd.DataFrame(loc_rows)
                df_loc = df_loc.rename(columns={
                    "country_name_ar": "الدولة",
                    "count": "العدد",
                    "flag": "العلم",
                    "country_code": "الرمز",
                })
                df_loc = df_loc[["الدولة", "العدد", "العلم", "الرمز"]]
                st.markdown("#### 🌍 locationCreated حسب الدولة")
                st.dataframe(df_loc, use_container_width=True, hide_index=True)
            else:
                st.info("لا توجد قيم locationCreated صريحة داخل النتائج الحالية")

            if location_report.get("evidence"):
                st.markdown("#### 🧾 الأدلة")
                for item in location_report.get("evidence", []):
                    st.markdown(f"- {item}")

            st.markdown("#### 🧠 author.region counts")
            st.json(location_report.get("author_region_counts", {}))

            export_json = json.dumps(location_report, ensure_ascii=False, indent=2)
            st.download_button(
                "📥 تصدير JSON للتقرير الكامل",
                data=export_json.encode("utf-8"),
                file_name="tiktok_osint_location_report.json",
                mime="application/json",
                use_container_width=True,
                key="tt_osint_export_location_json",
            )
    else:
        st.markdown(
            """
            <div class="warn-box">
            لم يتم تحليل فيديوهات بعد. اذهب لتبويب 🎬 تحليل فيديو TikTok
            </div>
            """,
            unsafe_allow_html=True,
        )
        direct_video_urls = st.text_area(
            "أو أدخل روابط فيديوهات هنا مباشرة:",
            height=180,
            key="tt_osint_direct_video_urls",
            placeholder="https://www.tiktok.com/@username/video/1234567890123456789",
        )
        if st.button("🚀 تحليل مباشر", type="primary", use_container_width=True, key="tt_osint_direct_analyze"):
            direct_urls = []
            for line in direct_video_urls.splitlines():
                line = line.strip()
                if line and "tiktok.com" in line.lower() and "/video/" in line:
                    direct_urls.append(line)
            if not direct_urls:
                st.error("❌ أدخل روابط فيديو TikTok صحيحة")
            else:
                with st.spinner(f"جارٍ تحليل {len(direct_urls)} فيديو..."):
                    direct_results = []
                    with ThreadPoolExecutor(max_workers=max_workers) as ex:
                        futures = {ex.submit(analyze_tiktok_video, url): url for url in direct_urls}
                        for future in as_completed(futures):
                            try:
                                direct_results.append(future.result())
                            except Exception as exc:
                                direct_results.append({
                                    "video_url": futures[future],
                                    "status": "❌ فشل",
                                    "error": str(exc),
                                })
                st.session_state["video_results"] = direct_results
                st.session_state["tt_osint_location_report"] = infer_user_location_from_videos(direct_results)
                st.success("✅ تم التحليل المباشر ويمكنك الآن مراجعة النتائج أو الانتقال لباقي التبويبات")
                st.rerun()

with sub2:
    st.markdown("#### 🌐 بحث TikTok الجغرافي")
    c_geo1, c_geo2 = st.columns(2)
    with c_geo1:
        manual_place = st.text_input("اسم المدينة أو المكان", key="tt_osint_manual_place")
    with c_geo2:
        extra_keywords = st.text_input("كلمات مفتاحية إضافية (اختياري)", key="tt_osint_extra_keywords")

    selected_place = st.selectbox(
        "اختر من FAMOUS_LOCATIONS_TT أو أدخل يدوياً",
        options=["— اختر مكاناً مشهوراً —"] + FAMOUS_LOCATIONS_TT,
        key="tt_osint_famous_place",
    )

    if st.button("🔍 ابحث + أنشئ روابط", use_container_width=True, key="tt_osint_generate_geo_links"):
        target_place = manual_place.strip() or ("" if selected_place == "— اختر مكاناً مشهوراً —" else selected_place)
        if not target_place:
            st.error("❌ أدخل مكاناً أو اختر مكاناً جاهزاً")
        else:
            geo_result = geocode_tiktok_place(target_place, lang="ar")
            if not geo_result:
                st.error("❌ تعذر تحديد إحداثيات هذا المكان")
            else:
                st.session_state["tt_osint_geo_search"] = {
                    "place": target_place,
                    "keywords": extra_keywords.strip(),
                    "geo": geo_result,
                    "links": build_tiktok_search_links(target_place, extra_keywords.strip(), geo_result),
                }

    geo_payload = st.session_state.get("tt_osint_geo_search")
    if geo_payload:
        geo_result = geo_payload["geo"]
        links = geo_payload["links"]
        st.info(
            f"إحداثيات: {geo_result['lat']:.6f}, {geo_result['lon']:.6f} — {geo_result.get('country') or 'غير معروف'}"
        )
        col_l1, col_l2, col_l3 = st.columns(3)
        with col_l1:
            st.link_button("🔍 بحث TikTok عام", links["general_search"], use_container_width=True)
        with col_l2:
            st.link_button("🏷️ هاشتاق المكان", links["hashtag_search"], use_container_width=True)
        with col_l3:
            st.link_button("🌍 بحث TikTok الإقليمي", links["regional_search"], use_container_width=True)

        with st.expander("روابط خرائط للموقع"):
            map_links = links.get("maps", {})
            if map_links:
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.link_button("Google Maps", map_links["google_maps"], use_container_width=True)
                with m2:
                    st.link_button("Yandex", map_links["yandex_maps"], use_container_width=True)
                with m3:
                    st.link_button("OSM", map_links["openstreetmap"], use_container_width=True)
                with m4:
                    st.link_button("Apple Maps", map_links["apple_maps"], use_container_width=True)

    st.markdown("---")
    st.markdown("#### 👤 بحث حساب محدد في موقع")
    user_geo_username = st.text_input("اسم مستخدم TikTok", key="tt_osint_user_geo_username")
    if st.button("🔗 بناء روابط الحساب داخل الموقع", use_container_width=True, key="tt_osint_build_user_geo"):
        place_for_user = manual_place.strip()
        if not place_for_user and geo_payload:
            place_for_user = geo_payload.get("place", "")
        if not user_geo_username.strip():
            st.error("❌ أدخل اسم المستخدم أولاً")
        elif not place_for_user.strip():
            st.error("❌ أدخل موقعاً أولاً أو أنشئ بحثاً جغرافياً من الأعلى")
        else:
            st.session_state["tt_osint_user_geo_links"] = build_tiktok_user_search(
                user_geo_username.strip(),
                place_for_user.strip(),
                extra_keywords.strip(),
            )

    user_geo_links = st.session_state.get("tt_osint_user_geo_links")
    if user_geo_links:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.link_button("🎵 الملف المباشر", user_geo_links["profile_url"], use_container_width=True)
        with c2:
            st.link_button("🔍 بحث TikTok للحساب", user_geo_links["tiktok_search"], use_container_width=True)
        with c3:
            st.link_button("🌐 بحث Google للحساب + الموقع", user_geo_links["google_search"], use_container_width=True)

with sub3:
    st.markdown(
        """
        <div class="info-box">
        يحلل أوقات نشر الفيديوهات لاستنتاج المنطقة الزمنية الفعلية للمستخدم
        بالاعتماد على تواريخ النشر المستخرجة من فيديوهات TikTok.
        </div>
        """,
        unsafe_allow_html=True,
    )

    video_results_for_tz = st.session_state.get("video_results") or []
    if video_results_for_tz:
        if st.button("⏰ تحليل نمط النشر", use_container_width=True, key="tt_osint_tz_analyze"):
            st.session_state["tt_osint_timezone_report"] = analyze_timezone_from_videos(video_results_for_tz)

        tz_report = st.session_state.get("tt_osint_timezone_report")
        if tz_report:
            if tz_report.get("error"):
                st.warning("لا توجد تواريخ فيديو كافية لتحليل المنطقة الزمنية")
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric("أفضل توقيت", tz_report.get("best_offset_str", "—"))
                c2.metric("الثقة", f"{tz_report.get('confidence', 0)}%")
                c3.metric("عينة الفيديوهات", tz_report.get("sample_size", 0))

                candidate_countries = tz_report.get("candidate_countries", [])
                if candidate_countries:
                    labels = []
                    for code in candidate_countries:
                        flag, name = TIKTOK_REGION_MAP.get(code, ("🌍", code))
                        labels.append(f"{flag} {code}")
                    st.markdown(f"**🌍 الدول المحتملة:** {'، '.join(labels)}")

                hist = tz_report.get("histogram_local_hours", {})
                if hist:
                    hist_series = pd.Series(hist).sort_index()
                    st.bar_chart(hist_series)

                top_offsets = tz_report.get("top_offsets", [])
                if top_offsets:
                    df_offsets = pd.DataFrame(top_offsets)
                    df_offsets["candidate_countries"] = df_offsets["candidate_countries"].apply(
                        lambda xs: ", ".join(xs) if isinstance(xs, list) else xs
                    )
                    df_offsets = df_offsets.rename(columns={
                        "offset_str": "التوقيت",
                        "confidence": "الثقة",
                        "score": "النتيجة",
                        "candidate_countries": "الدول المحتملة",
                    })
                    st.markdown("#### أفضل 5 فروقات زمنية")
                    st.dataframe(
                        df_offsets[["التوقيت", "الثقة", "النتيجة", "الدول المحتملة"]],
                        use_container_width=True,
                        hide_index=True,
                    )
    else:
        st.markdown(
            """
            <div class="warn-box">
            لا توجد بيانات فيديو لتحليل التوقيت. حلّل بعض الفيديوهات أولاً من تبويب 🎬 تحليل فيديو TikTok.
            </div>
            """,
            unsafe_allow_html=True,
        )

with sub4:
    st.markdown("#### 🗺️ خريطة المواقع")
    map_video_results = st.session_state.get("video_results") or []
    map_rows = []
    for row in map_video_results:
        code = (row.get("location_created") or "").upper().strip()
        center = get_tiktok_region_center(code) if code else None
        if center:
            flag, country_name = TIKTOK_REGION_MAP.get(code, ("🌍", code))
            map_rows.append({
                "username": row.get("username", ""),
                "country_code": code,
                "country_name_ar": country_name,
                "flag": flag,
                "lat": center[0],
                "lon": center[1],
                "title": row.get("video_desc") or row.get("video_url") or "فيديو TikTok",
            })

    if FOLIUM_AVAILABLE and map_rows:
        region_counter = Counter([r["country_code"] for r in map_rows])
        top_code = region_counter.most_common(1)[0][0]
        top_center = get_tiktok_region_center(top_code) or [24.7136, 46.6753]
        m = folium.Map(location=top_center, zoom_start=3, control_scale=True)
        palette = ["red", "blue", "green", "purple", "orange", "darkred", "cadetblue"]

        for idx, row in enumerate(map_rows):
            color = palette[idx % len(palette)]
            popup_html = (
                f"<div dir='rtl'><b>@{row['username']}</b><br>"
                f"{row['flag']} {row['country_name_ar']}<br>{row['title'][:140]}</div>"
            )
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=7,
                color=color,
                fill=True,
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=320),
            ).add_to(m)

        if top_center:
            top_flag, top_name = TIKTOK_REGION_MAP.get(top_code, ("🌍", top_code))
            folium.Circle(
                location=top_center,
                radius=300000,
                color="#ff0050",
                fill=True,
                fill_opacity=0.15,
                popup=folium.Popup(f"<div dir='rtl'>الأكثر تكراراً: {top_flag} {top_name}</div>"),
            ).add_to(m)

        st_folium(m, width=800, height=500)
    else:
        if not map_rows:
            st.warning("لا توجد مواقع فيديو قابلة للرسم حالياً")
        rows_for_table = []
        for row in map_rows:
            map_link = f"https://www.google.com/maps?q={row['lat']},{row['lon']}"
            rows_for_table.append({
                "المستخدم": row["username"],
                "الدولة": row["country_name_ar"],
                "العلم": row["flag"],
                "الإحداثيات": f"{row['lat']:.4f}, {row['lon']:.4f}",
                "Google Maps": map_link,
            })
        if rows_for_table:
            st.dataframe(pd.DataFrame(rows_for_table), use_container_width=True, hide_index=True)
            for row in rows_for_table:
                st.markdown(f"- **@{row['المستخدم']}** — [{row['الدولة']}]({row['Google Maps']})")

with sub5:
    verification_username = st.text_input("أدخل اسم مستخدم TikTok", key="tt_osint_verify_username")
    if st.button("🔗 أنشئ روابط التحقق", use_container_width=True, key="tt_osint_build_verification"):
        if not verification_username.strip():
            st.error("❌ أدخل اسم مستخدم TikTok")
        else:
            st.session_state["tt_osint_verification_links"] = build_tiktok_verification_links(verification_username.strip())

    verification_links = st.session_state.get("tt_osint_verification_links")
    if verification_links:
        v1, v2, v3, v4, v5 = st.columns(5)
        with v1:
            st.link_button("🎵 ملف TikTok المباشر", verification_links["tiktok_profile"], use_container_width=True)
        with v2:
            st.link_button("🕰️ Wayback Machine", verification_links["wayback"], use_container_width=True)
        with v3:
            st.link_button("🔍 بحث Google", verification_links["google"], use_container_width=True)
        with v4:
            st.link_button("🦅 Yandex", verification_links["yandex"], use_container_width=True)
        with v5:
            st.link_button("🐦 Urlebird", verification_links["urlebird"], use_container_width=True)

    with st.expander("روابط إضافية للمواقع المكتشفة"):
        location_report = st.session_state.get("tt_osint_location_report") or {}
        probable_code = location_report.get("probable_country_code", "")
        center = get_tiktok_region_center(probable_code) if probable_code else None
        if center:
            map_links = build_tt_map_links(center[0], center[1])
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.link_button("Google Maps", map_links["google_maps"], use_container_width=True)
            with c2:
                st.link_button("Yandex", map_links["yandex_maps"], use_container_width=True)
            with c3:
                st.link_button("OSM", map_links["openstreetmap"], use_container_width=True)
            with c4:
                st.link_button("Apple Maps", map_links["apple_maps"], use_container_width=True)
        else:
            st.caption("ستظهر هنا روابط الخرائط عند اكتشاف موقع محتمل من الفيديوهات")
