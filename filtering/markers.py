import re

TOKEN_RE = re.compile(r"[a-z]+(?:[-'][a-z]+)*")

# These forms are not allowed to decide between Cebuano and Tagalog.
# "gamit" and "tas" were supporting markers in the old script, but are placed
# here because they can be used or interpreted outside a clearly Cebuano frame.
AMBIGUOUS_OR_SHARED = {
    "ako", "ang", "ba", "daw", "di", "diko", "gamit", "gusto",
    "ikaw", "ka", "kami", "kamo", "kay", "ko", "kulang", "lang", "lasa",
    "lagi", "man", "may", "mga", "mo", "na", "nag", "naka", "ni", "nila",
    "niya", "pag", "para", "pero", "po", "sa", "sila", "siya", "sulit",
    "tas", "wala", "way",
}

# One decisive Cebuano word is sufficient Cebuano evidence. This set collapses
# the old weights 2 and 3 because both already satisfied the old minimum score.
CEBUANO_DECISIVE_WORDS = {
    "abi", "akoa", "amoa", "amoang", "among", "ana", "ani", "ari", "aron",
    "asa", "asay", "atoa", "atoang", "ayha", "barato", "bisag", "bisan",
    "bitaw", "buotan", "daghan", "dako", "dghan", "diay", "didto", "dili",
    "diri", "dli", "dris", "dugay", "dugang", "dungag", "gagmay", "gamay",
    "gamaya", "gamayg", "gamayng", "gani", "gibutang",
    "gihatag", "gihatud", "gihapon", "gipadala", "giputos", "gud", "gyud",
    "ingani", "inani", "inyoha", "jud", "jod", "jd", "juy", "kabuok",
    "kagabii", "kagbie", "kalami", "kanang", "kani", "kanus-a", "kanusa",
    "kaau", "kaayo", "kaayog", "kaayow", "kaayu", "kapila", "karon",
    "karun", "kayng", "kinsa",
    "kinahanglan", "kog", "kos", "lahi", "lain", "lamia", "lamian", "lami",
    "lisod", "maayo", "maau", "mao", "maong", "mausab", "morag", "muabot",
    "mubasa", "mubasag", "murag", "naa", "naabot", "naay", "nako", "namo",
    "namong", "nato", "natong", "ngano", "nganong", "ngari", "ngbyad",
    "niabot", "nigamay", "nindot", "nimo", "ninyo", "pag-abot", "pagkaon",
    "padong", "pajud", "palihug", "paspas", "permi", "pirmi", "pod", "pud",
    "puhon", "raman", "rapod", "sayop", "sulod", "tanan", "tarong",
    "tarunga", "tawo", "tgaan", "tua", "uban", "ug", "og", "unsa", "unsay",
    "unsaon", "unya", "unta", "way", "walay", "wlay",
} - AMBIGUOUS_OR_SHARED

# Supporting markers cannot establish Cebuano evidence alone. Two different
# supporting markers are required when no decisive Cebuano marker is present.
CEBUANO_SUPPORTING_WORDS = {
    "akong", "amo", "ato", "ga", "ge", "gi", "ila", "ilaha", "ilahang",
    "ilang", "inyo", "inyong", "inyung", "mi", "nko", "nla", "nmo", "nnu",
    "nnyo", "nya", "ra", "rag", "sakto", "sya", "ta", "wa", "wla", "nga",
} - AMBIGUOUS_OR_SHARED

# A phrase is treated as one decisive piece of evidence. Component words may
# still be recorded for traceability, but they do not add numerical points.
CEBUANO_DECISIVE_PHRASES = {
    "akong order",
    "among order",
    "dili kaayo",
    "dili kaayu",
    "dili lami",
    "dili jud",
    "dli maau",
    "dli lami",
    "gamay ra",
    "ilang food",
    "inyong food",
    "kapila na",
    "lami kaayo",
    "lami kaayu",
    "mao ra",
    "naa sa",
    "naay buhok",
    "ok ra",
    "okay ra",
    "pag abot",
    "ra kaayo",
    "sakto ra",
    "unsa man",
    "wa juy",
    "walay lami",
    "wala jud",
    "wala lami",
    "wala pajud",
    "pan os",
    "way ayo",
}

# These flag likely Tagalog overlap. They do not remove a review from the
# annotation queue when Cebuano and English evidence are also present.
TAGALOG_DECISIVE_WORDS = {
    "akin", "ayos", "ayoko", "bahay", "bakit", "balik-balikan", "beses",
    "binigay", "binili", "dahil", "dapat", "din", "dito", "dumating", "ganito",
    "ganto", "hindi", "isa", "kahit", "kainin", "kanina", "kasi", "kaso",
    "konti", "lahat", "lapit", "malaki", "malinis", "maliit", "masarap",
    "masyado", "matabang", "matigas", "mukhang", "muna", "nadeliver",
    "nakalagay", "nakakamay", "naman", "namin", "napaka", "nasa", "natin",
    "nareceive", "nung", "nyo", "niyo", "pakonti", "palagi", "panis",
    "parang", "pinadala", "rin", "sabi", "sakin", "samin", "sana", "sarap",
    "siguro", "sobrang", "talaga", "tapos", "tignan", "tinipid", "ulit",
    "umoorder", "umorder", "ulitin", "walang", "yung", "yun",
} - AMBIGUOUS_OR_SHARED

TAGALOG_DECISIVE_PHRASES = {
    "ang bilis",
    "ang daming",
    "ang liit",
    "ang pangit",
    "ang sarap",
    "at saka",
    "di na ako",
    "hindi na",
    "lagi na lang",
    "nag order ako",
    "nag try",
    "sa amin",
    "sa inyo",
    "sa susunod",
    "sana next time",
    "pa rin",
    "pa din",
    "yung order",
}

ENGLISH_MARKERS = {
    "a", "add", "again", "all", "always", "am", "and", "are", "around",
    "arrived", "as", "at", "bad", "bag", "balance", "because", "before",
    "beef", "best", "bit", "bland", "box", "burger", "but", "can", "cannot",
    "chicken", "cold", "combo", "container", "cream", "crunchy", "customer",
    "delayed", "delicious", "delivery", "did", "disappointed", "disappointing",
    "do", "does", "don't", "dry", "egg", "expensive", "fast", "first",
    "flavor", "food", "for", "forgot", "fresh", "fries", "from", "good",
    "gravy", "great", "had", "has", "have", "here", "hot", "hour", "how", "i",
    "if", "in", "instructions", "into", "item", "items", "it", "just", "large",
    "late", "lemon", "like", "liked", "love", "mcflurry", "meat", "missing",
    "more", "much", "my", "never", "next", "nice", "no", "not", "note", "of",
    "old", "on", "only", "or", "order", "ordered", "original", "our", "out",
    "packaging", "paid", "paperbag", "perfect", "plain", "plastic", "pork",
    "portion", "prepare", "price", "quality", "really", "receipt", "recommend",
    "rice", "rider", "rolls", "salty", "sauce", "service", "serving", "shake",
    "should", "small", "so", "soggy", "some", "sorry", "sour", "spicy",
    "spilled", "spoon", "store", "sweet", "taste", "tea", "than", "that",
    "the", "their", "they", "this", "time", "to", "too", "try", "up", "us",
    "very", "was", "we", "were", "what", "when", "where", "which", "whip",
    "who", "why", "will", "with", "would", "worst", "worth", "wrong", "you",
    "your", "also", "affordable", "almost", "available", "be", "better",
    "bread", "breading", "buy", "cake", "check", "cheese", "coffee", "cooked",
    "crispy", "cravings", "definitely", "deliver", "drinks", "even", "expect",
    "extra", "far", "favorite", "fave", "free", "garlic", "generous", "happy",
    "half", "highly", "hope", "ice", "is", "it's", "its", "job", "meal",
    "med", "milk", "mins", "maybe", "need", "noodles", "nothing", "now",
    "okay", "ok", "one", "ordering", "orders", "other", "others", "overall",
    "pay", "pcs", "picture", "pizza", "please", "plus", "properly", "request",
    "requested", "recommended", "same", "sandwich", "satisfied", "satisfy",
    "secure", "serve", "servings", "size", "something", "straw", "sugar",
    "super", "sure", "tasty", "thank", "thanks", "then", "tuna", "unlike",
    "use", "usual", "warm", "well", "wings", "work", "yummy",
}

# A single occurrence of one of these is too weak for the highest-priority
# queue, although it remains useful in the broader review queue.
WEAK_ENGLISH_MARKERS = {"a", "i", "ok", "okay"}

# The second pass uses a stricter subset for the publishable Tier A batch.
COLLISION_MARKERS = {
    "kani",    # Japanese crab stick; appears constantly in sushi reviews
    "og",      # English "OG" slang, and a common typo
    "gud",     # English texting spelling of "good"
    "ninyo",   # used identically in Tagalog
    "ana",     # the name Ana, and Sta. Ana branch names
    "ari",     # collides inside sari-sari, safari, Mari
    "asa",     # Tagalog "to hope"
    "lahi",    # Tagalog "race / lineage"
    "lain",
    "dako",
    "barato",  # shared Spanish loan
    "tawo",
    "isa",     # Tagalog "one"
}

# --- Tagalog-exclusive tokens ---------------------------------------------
# Deliberately narrow. Forms that Cebuano speakers also use (po, kayo, nila,
# niya, sila, kaya, pwede, siguro, parang) are NOT listed here, because
# including them removes genuine Cebuano-English reviews.
TAGALOG_EXCLUSIVE = {
    "ng", "yung", "yun", "naman", "talaga", "kasi", "hindi", "masarap",
    "bakit", "paano", "sino", "magkano", "pala", "konti", "meron",
    "mabilis", "dito", "doon", "ganito", "ganon", "ngayon", "iyon",
    "akin", "natin", "namin", "bumili", "ito", "marami", "dahil",
    "kahit", "ulit", "beses", "dumating", "sobrang", "nung", "sakin",
    "samin", "binili", "binigay", "nakalagay", "umorder", "masyado",
    "mukhang", "muna", "palagi", "walang", "tignan",
}

