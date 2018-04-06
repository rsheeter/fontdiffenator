"""
Flatten a font's GPOS kerning.
"""


def _kerning_lookup_indexes(ttfont):
    """Return the lookup ids for the kern feature"""
    for feat in ttfont['GPOS'].table.FeatureList.FeatureRecord:
        if feat.FeatureTag == 'kern':
            return feat.Feature.LookupListIndex
    return None


def _flatten_format1_subtable(table, results):
    """Flatten pair on pair kerning"""
    seen = set(results)
    first_glyphs = {idx: g for idx, g in enumerate(table.Coverage.glyphs)}

    for idx, pairset in enumerate(table.PairSet):
        first_glyph = first_glyphs[idx]

        for record in pairset.PairValueRecord:

            kern = (first_glyph, record.SecondGlyph, record.Value1.XAdvance)

            if kern not in seen:
                results.append(kern)
                seen.add(kern)


def _flatten_format2_subtable(table, results):
    """Flatten class on class kerning"""
    seen = set(results)
    classes1 = _kern_class(table.ClassDef1.classDefs)
    classes2 = _kern_class(table.ClassDef2.classDefs)

    for idx1, class1 in enumerate(table.Class1Record):
        for idx2, class2 in enumerate(class1.Class2Record):

            if idx1 not in classes1:
                continue
            if idx2 not in classes2:
                continue

            if class2.Value1.XAdvance != 0:
                for glyph1 in classes1[idx1]:
                    for glyph2 in classes2[idx2]:

                        kern = (glyph1, glyph2, class2.Value1.XAdvance)
                        if kern not in seen:
                            results.append(kern)
                            seen.add(kern)


def _kern_class(class_definition):
    """Transpose a ttx classDef

    {glyph_name: idx, glyph_name: idx} --> {idx: [glyph_name, glyph_name]}"""
    classes = {}
    for glyph, idx in class_definition.items():
        if idx not in classes:
            classes[idx] = []
        classes[idx].append(glyph)
    return classes


def flatten_kerning(ttfont, glyph_map=None):

    if 'GPOS' not in ttfont:
        raise Exception("Font doesn's have GPOS table")

    kerning_lookup_indexes = _kerning_lookup_indexes(ttfont)
    if not kerning_lookup_indexes:
        raise Exception("Font doesn't have a GPOS kern feature")

    kern_table = []
    for lookup_idx in kerning_lookup_indexes:
        lookup = ttfont['GPOS'].table.LookupList.Lookup[lookup_idx]

        for sub_table in lookup.SubTable:
            if sub_table.Format == 1:
                _flatten_format1_subtable(sub_table, kern_table)
            if sub_table.Format == 2:
                _flatten_format2_subtable(sub_table, kern_table)

    kern_table = [{'left': k[0], 'right': k[1], 'value': k[2]} for k in kern_table]

    if glyph_map:
        kern_table_decomped = []
        for idx, kern in enumerate(kern_table):
            try:
                kern_table[idx]['left'] = glyph_map[kern['left']]
                kern_table[idx]['right'] = glyph_map[kern['right']]
                kern_table_decomped.append(kern_table[idx])
            except KeyError:
                pass
        return kern_table_decomped
    return kern_table


if __name__ == '__main__':
    from fontTools.ttLib import TTFont
    from glyphs import glyph_map
    f = TTFont('/Users/marc/Downloads/roboto-unhinted/Roboto-Regular.ttf')
    # f = TTFont('/Users/marc/Documents/googlefonts/manual_font_cleaning/_privates/Roboto/master_ttf/Roboto-Regular.ttf')
    g_map = glyph_map(f)
    kern_tbl = flatten_kerning(f, g_map)
    print kern_tbl[:20]

    # for item in kern_tbl:
    #     print item['left'].characters, item['right'].characters