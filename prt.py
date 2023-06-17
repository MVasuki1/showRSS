def gen_xml_from_list(l: list, title: str):
    xml=f"<rss>\n<channel>\n<title>{title}</title>"
    for r in l:
        e = "\n".join([f'<{key}>{value}</{key}>' for key, value in r.items()])
        row_xml = f"<item>\n{e}\n</item>"
        xml = xml + "\n" + row_xml
    xml = xml + "\n</channel>\n</rss>" 
    return xml       


