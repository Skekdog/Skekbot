import random

subject = [
    (0,"a {0} fish"),
    (1,"an {0} ICBM"),
    (-1,"traitor"),
    (4,"{0} Skekdog"),
    (0,"a {0} cat"),
    (-1,"you"),
    (4,"{0} Margaret Thatcher"),
    (4,"{0} Boris Johnson"),
    (4,"{0} Elon Musk"),
    (4,"{0} Donald Trump"),
    (4,"{0} Barack Obama"),
    (4,"{0} Joe Biden"),
    (4,"{0} Vladimir Putin"),
    (4,"{0} Volodymyr Zelensky"),
    (4,"the {0} British Army"),
    (4,"{0} NATO"),
    (4,"{0} Syria"),
    (4,"{0} Canada"),
    (4,"{0} Liechtenstien"),
    (4,"{0} Scotland"),
    (4,"{0} Germany"),
    (4,"{0} France"),
    (4,"the {0} USSR"),
    (4,"{0} Mexico"),
    (4,"{0} Joseph Stalin"),
    (0,"a {0} dog"),
    (4,"{0} Ireland"),
    (0,"a {0} baboon"),
    (4,"{0} Gandhi"),
    (4,"{0} George Washington"),
    (4,"{0} Mr. Bean"),
    (4,"{0} Agent 47"),
    (4,"{0} Diana Burnwood"),
    (4,"{0} Shrek"),
    (4,"{0} Ronald McDonald"),
    (4,"{0} Abraham Lincoln"),
    (0,"a {0} British man named Barry, aged 63, single and ready to mingle"),
    (4,"{0} Queen Elizabeth II"),
]

dirObject = [
    (0,"the {0} sun"),
    (0,"a {0} bottle of water"),
    (0,"a {0} cannon"),
    (0,"a {0} light bulb"),
    (4,"{0} Skekbot"),
    ([3,0],"{0} {1} potatoes"),
    ([3,0],"{0} {1} men"),
    (-1,"Shakespeare's poems"),
    (1,"an {0} umbrella"),
    (4,"the {0} road"),
    (2,"{0} town"),
    (0,"a {0} grand piano"),
    (1,"an {0} phone"),
    (1,"an {0} can of spaghetti sauce"),
    (0,"a {0} black hole"),
]

actions = [
    "invaded",
    "whacked",
    "pointed and laughed at",
    "stoned",
    "killed",
    "raced",
    "chased",
    "fled",
    "harassed",
    "doxxed",
    "berated",
    "betrayed",
    "KO'd",
    "burnt down",
    "razed",
    "funded",
    "aided",
    "cured",
    "cooked",
    "shook",
    "tried to find Obama's last name with",
    "murdered",
]

adverbs = [
    "swiftly",
    "quickly",
    "slowly",
    "dumbly",
    "sadly",
    "cheerily",
    "angrily",
    "furiously",
    "drunkenly",
    "carelessly",
    "brutally",
]

anAdjectives = [
    "old",
    "explosive",
    "icy",
    "ugly",
    "idiotic",
    "adorable",
    "innocent",
    "interesting",
    "intelligent",
    "ultimate",
    "excellent",
    "accelerating",
    "aggressive",
    "artistic",
    "expired",
    "addictive",
    "accidental",
    "intoxicated",
]

aAdjectives = [
    "youthful",
    "silly",
    "rotten",
    "deceased",
    "horny",
    "brave",
    "raging",
    "molten",
    "rigid",
    "cold",
    "hot",
    "plastic",
    "premium",
    "precise",
    "wet",
    "rusty",
]

amounts = [
    "two",
    "three",
    "many",
    "a few",
    "one hundred",
    "a couple",
    "nine",
    "over nine thousand",
    "seven",
    "thirteen",
    "two and a half",
]

adjectives = aAdjectives+anAdjectives

def getWord(num:int) -> str:
    """
    0: Consonant adjective (aAdjective)
    1: Vowel adjective (anAdjective)
    2: Noun (subject)
    3: Amount (amounts)
    4: Any adjective (adjectives)
    5: Adverbs (adverbs)
    -1: None
    """
    match num:
        case 0:
            random.shuffle(aAdjectives)
            return aAdjectives[0]
        case 1:
            random.shuffle(anAdjectives)
            return anAdjectives[0]
        case 2:
            random.shuffle(subject)
            return subject[0][1].format(getWord(subject[0][0]))
        case 3:
            random.shuffle(amounts)
            return amounts[0]
        case 4:
            random.shuffle(adjectives)
            return adjectives[0]
        case 5:
            random.shuffle(adverbs)
            return adverbs[0]
        case -1:
            return ""
        case _:
            if type(num) == list:
                t = ()
                for i in num:
                    t += (getWord(i),)
                return t


def generate():
    random.shuffle(actions)
    random.shuffle(subject)
    string = ""

    sub = subject[0]
    string += sub[1].format(getWord(sub[0]))+" "+getWord(5)+" "+actions[0]+" "
    string = string[0].upper()+string[1:]

    if random.randint(0,1) == 0:
        random.shuffle(dirObject)
        sub = dirObject[0]
    else:
        sub = subject[1]

    w = getWord(sub[0])
    if type(w) == tuple:
        string += sub[1].format(*w)+" "
    else:
        string += sub[1].format(w)+" "

    return (string[:-1] if string[-1] == " " else string)+"."