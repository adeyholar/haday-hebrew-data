"""Tanakh book order, Hebrew canon, matching OSHB OSIS ids."""

BOOKS = [
    ("Gen", "Genesis", "בְּרֵאשִׁית", "Torah", "Genesis.xml", "prose"),
    ("Exod", "Exodus", "שְׁמוֹת", "Torah", "Exodus.xml", "prose"),
    ("Lev", "Leviticus", "וַיִּקְרָא", "Torah", "Leviticus.xml", "prose"),
    ("Num", "Numbers", "בְּמִדְבַּר", "Torah", "Numbers.xml", "prose"),
    ("Deut", "Deuteronomy", "דְּבָרִים", "Torah", "Deuteronomy.xml", "prose"),
    ("Josh", "Joshua", "יְהוֹשֻׁעַ", "Neviim", "Joshua.xml", "prose"),
    ("Judg", "Judges", "שׁוֹפְטִים", "Neviim", "Judges.xml", "prose"),
    ("1Sam", "1 Samuel", "שְׁמוּאֵל א", "Neviim", "Samuel_1.xml", "prose"),
    ("2Sam", "2 Samuel", "שְׁמוּאֵל ב", "Neviim", "Samuel_2.xml", "prose"),
    ("1Kgs", "1 Kings", "מְלָכִים א", "Neviim", "Kings_1.xml", "prose"),
    ("2Kgs", "2 Kings", "מְלָכִים ב", "Neviim", "Kings_2.xml", "prose"),
    ("Isa", "Isaiah", "יְשַׁעְיָהוּ", "Neviim", "Isaiah.xml", "prose"),
    ("Jer", "Jeremiah", "יִרְמְיָהוּ", "Neviim", "Jeremiah.xml", "prose"),
    ("Ezek", "Ezekiel", "יְחֶזְקֵאל", "Neviim", "Ezekiel.xml", "prose"),
    ("Hos", "Hosea", "הוֹשֵׁעַ", "Neviim", "Hosea.xml", "prose"),
    ("Joel", "Joel", "יוֹאֵל", "Neviim", "Joel.xml", "prose"),
    ("Amos", "Amos", "עָמוֹס", "Neviim", "Amos.xml", "prose"),
    ("Obad", "Obadiah", "עֹבַדְיָה", "Neviim", "Obadiah.xml", "prose"),
    ("Jonah", "Jonah", "יוֹנָה", "Neviim", "Jonah.xml", "prose"),
    ("Mic", "Micah", "מִיכָה", "Neviim", "Micah.xml", "prose"),
    ("Nah", "Nahum", "נַחוּם", "Neviim", "Nahum.xml", "prose"),
    ("Hab", "Habakkuk", "חֲבַקּוּק", "Neviim", "Habakkuk.xml", "prose"),
    ("Zeph", "Zephaniah", "צְפַנְיָה", "Neviim", "Zephaniah.xml", "prose"),
    ("Hag", "Haggai", "חַגַּי", "Neviim", "Haggai.xml", "prose"),
    ("Zech", "Zechariah", "זְכַרְיָה", "Neviim", "Zechariah.xml", "prose"),
    ("Mal", "Malachi", "מַלְאָכִי", "Neviim", "Malachi.xml", "prose"),
    ("Ps", "Psalms", "תְּהִלִּים", "Ketuvim", "Psalms.xml", "poetic"),
    ("Prov", "Proverbs", "מִשְׁלֵי", "Ketuvim", "Proverbs.xml", "poetic"),
    ("Job", "Job", "אִיּוֹב", "Ketuvim", "Job.xml", "poetic"),
    ("Song", "Song of Songs", "שִׁיר הַשִּׁירִים", "Ketuvim", "Song_of_Songs.xml", "prose"),
    ("Ruth", "Ruth", "רוּת", "Ketuvim", "Ruth.xml", "prose"),
    ("Lam", "Lamentations", "אֵיכָה", "Ketuvim", "Lamentations.xml", "prose"),
    ("Eccl", "Ecclesiastes", "קֹהֶלֶת", "Ketuvim", "Ecclesiastes.xml", "prose"),
    ("Esth", "Esther", "אֶסְתֵּר", "Ketuvim", "Esther.xml", "prose"),
    ("Dan", "Daniel", "דָּנִיֵּאל", "Ketuvim", "Daniel.xml", "prose"),
    ("Ezra", "Ezra", "עֶזְרָא", "Ketuvim", "Ezra.xml", "prose"),
    ("Neh", "Nehemiah", "נְחֶמְיָה", "Ketuvim", "Nehemiah.xml", "prose"),
    ("1Chr", "1 Chronicles", "דִּבְרֵי הַיָּמִים א", "Ketuvim", "Chronicles_1.xml", "prose"),
    ("2Chr", "2 Chronicles", "דִּבְרֵי הַיָּמִים ב", "Ketuvim", "Chronicles_2.xml", "prose"),
]

BY_OSIS = {row[0]: row for row in BOOKS}


def verse_system(osis: str, chapter: int, verse: int) -> str:
    if osis in ("Ps", "Prov"):
        return "poetic"
    if osis == "Job":
        if chapter < 3 or (chapter == 3 and verse == 1) or (chapter == 42 and verse >= 7):
            return "prose"
        return "poetic"
    return "prose"
