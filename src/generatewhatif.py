import random

"""
How should English sentences be generated?
Four levels of complexity:

Simple: "The quick brown fox jumped over the lazy dog."
Interesting: "The quick brown fox, who was known for his habit of jumping, jumped over the lazy dog."
Detailed: "Then without warning, the quick brown fox, who was known for his habit of suddenly jumping, jumped over the lazy dog."
Complex: "Then without warning, the quick brown fox, who was known for his habit of suddenly jumping, jumped over the lazy dog, without realising that the dog had prepared itself for this attack, and stumbled."

Red big balloon vs. Big red balloon - "royal order of adjectives":
0. Opinion - "beautiful"
1. Condition - "rotten"?
2. Size - "big"
3. Age - "old"
4. Shape - "round"
5. Colour - "red"
6. Origin - "German"
7. Material - "rubber"
8. Purpose - "flying" - maybe some of these should be instead a part of the noun - "cooking pot" - maintaining order if then "explosive cooking pot"

"A beautiful, big, old, round, red German rubber balloon."

Sentence = (descriptor adverb) + (descriptor) + subject + (adverb) + action + object + (joiner + new Sentence)


Substitutions:
{1} - Any number, amount of adjectives

{O} - Object
{S} - Subject
{N} - Any noun
{T} - Time period
{A} - Action
{C} - Amount

{N!A} - Action replacing nouns with blanks
{N|A} - Noun or adjective
{OA} - Origin Adjective

"""

vowels = ["a","e","i","o","u"] # // Presumably these won't change
descriptors = [
    # // Opinion
    [
        "beautiful","pretty","nice","unpleasant","wonderful","brilliant","excellent","lovely","delightful",
        "disgusting","nasty","ugly","horrible","terrible","abysmal",

        "angry","furious","annoyed","irritated","exasperated","irked","resentful","piqued","fuming","insane",
        "calm","peaceful","tranquil","quiet","serence","undisturbed","composed","gentle","untroubled","silent",

        "objectable","disreputable","manipulative","distasteful","scheming","devious","calculating","sly","crafty",
        "caring","friendly","approachable","genial","sociable","helpful","benevolent","affectionate","cordial",

        "hopeless","desperate","despairing","disconsolate","demoralised","useless","dreadful","incompetent","pathetic",
        "hopeful","ideal","perfect","confused","perplexed","misunderstood","understanding","bewildered","disorientated",

        "mundane","uninteresting","boring","tedious","dull","repetitive","unvaried","monotonous","wearisome","dreary",
        "interesting","intriguing","compelling","absorbing","entrancing","captivating","enthralling","charming","dazzling",

        "authoritative","strong","forceful","powerful","rigid","sturdy","muscular","robust","tough","solid","influential",
        "weak","flimsy","frail","feeble","fragile","incapacitated","delicate","debilitated","sickly","immobilised","paralysed",

        "artistic","premium","hot","royal","accidental","addictive","innocent","aggressive","adorable","horny","brave","mindless",
        "stupid","rude","insensitive","desensitised"
    ],
    # // Condition
    [
        "rotten","dirty","uncooked","stale","mouldy","infected","destroyed","damaged","filthy","clean","pristine",
        "shiny","homemade","contagious","cancerous","intoxicated","drunk","inebriated","molten","burning","swollen",
        "irradiated","radioactive","rusty","wet","expired","accelerating","empty",
    ],
    # // Size
    [
        "massive","large","huge","big","average-sized","small","tiny","miniscule","microscopic","puny"
        "obese","plus-sized","overweight","healthy-weight","underweight","emaciated","chunky","fat"
    ],
    # // Age
    [
        "pre-historic","neolithic","ancient","old","aged","new","brand new","futuristic","decrepit","modern","contemporary",
        "medieval","classical","renaissance","cold war era","from the {T}s","youthful","young","recent","outdated",
    ],
    # // Shape
    [
        "round","spherical","curved","square","uneven","rectangular","triangular","polygonal","hexagonal","flat","rough","bumpy"
    ],
    # // Colour
    # // ZWSP or space indicates that this colour should not be modified (with light or dark)
    [
        "light​","dark​","white​","black​","grey","red","green","blue","orange","yellow","brown","purple","gold","pink","cyan",
        "pearl white","deep blue","navy blue","acid green","amethyst purple","apricot orange","baby blue","baby pink","olive green",
        "brick red","burgundy​","copper orange","emerald green","golden brown","granite grey","hot pink","magenta​","lemon yellow",
        "lime​","midnight blue","midnight green","royal blue","silver​","beige​","invisible​"
    ],
    # // Origin
    [
        "Canadian","American","Mexican","Colombian","Cuban","Brazilian","Argentinian",

        "British","French","Spanish","German","Polish","Italian","Latvian","Estonian",
        "Scottish","English","Welsh","Irish","Belgian","Greek","Romanian","Turkish",
        "Bulgarian","Finnish","Swedish","Danish","Belarusian","Russian","Ukrainian",
        "Albanian",

        "Mongolian","Syrian","Iranian","Iraqi","Arabian","Indian","Chinese","Vietnamese",
        "Korean","Thai","Malaysian","Indonesian","Australian","Japanese",

        "Moroccan","Tunisian","Libyan","Algerian","Egyptian","Nigerian","Sudanese","Kenyan","Tanzanian",

        "American","European","Asian","African","Antartican",
    ],
    # // Material
    [
        "rubber","leather","silk","fabric","cotton","wool","plastic","wooden","steel","metal","synthetic","fur","concrete","icy"
    ],
    # // Purpose
    [
        "explosive","distracting","confusing","dangerous","deadly","poisonous","toxic","electrifying","terrifying","genocidal","curing",
        "manipulating","fishing","intoxicating",
    ],
]

# // From the [...]
timePeriods = [
    "ancient era","medieval era","classical era","renaissance era","modern era","atomic era","year of the birth of Christ","pre-historic era","colonial era"
    "1700s","1600s","1500s","1200s","600s","1950s","1960s","1970s","1980s","1990s","2000s","2010s","2020s","2030s","2050s","3000s","2500s",
    "First World War","Second World War","Cold War","War on Terror","Boxer Insurrection","Boston Tea Party",
    "fall of the Soviet Union","fall of the USSR","fall of the Berlin Wall","Russian Revolution","Napoleonic Wars",
    "Industrial Revolution","Agricultural Revolution",
    "dawn of humanity","far future",
]

# // ZWSP indicates this amount should not be used for modificactions. Amounts ending in dash may have another non-dash number appended.
# // Amounts ending in underscore will be appended with and + number (hundred and fifty-six).
amounts = [
    "no​","infinite​",
    "two","three","four","five","six","seven","eight","nine",
    "ten-","eleven-","twelve-","thirteen-","fourteen-","fifteen-","sixteen-","seventeen-","eighteen-","nineteen-"
    "twenty-","thirty-","forty-","fifty-","sixty-","seventy-","eighty-","ninety-",
    "hundred","thousand","million","billion",
]

# // Adverbs that modify an adjective
adjAdverbs = [
    "really","quite","fairly","pretty","somewhat","barely","a little","very","extremely","immensely","needlessly","stupidly",
    "ridiculously","brutally","excessively",
]

# // {0} is substituted for any noun. If not present, a noun is appended to the end.
# // {1} is substituted for an amount.
# // {2} is substituted for a different action. {0} will be substituted with nothing in this different action.
# // {3} is substituted for a different action. {0} will be substituted as normal in this different action.
# // {4} is substituted for a noun or an adjective.
# // {5} is substituted for an adjective.
# // {6} is substituted for a noun.
actions = [
    "searched for Obama's last name with",
    "planted an explosive to eliminate",
    "set a trap, but was not to blame, for",
    "pointed and laughed at",

    "executed","shot","opened fire on","obliterated","damaged","assassinated","eliminated",
    "whacked","beat","attacked","invaded","declared war on","punched","burnt","poisoned","knocked {S} unconscious","bombed"
    "detained","apprehended","caught {S}red-handed","questioned","interrogated","arrested",
    "held a grudge against","never forgave","forgave","begged {S} for forgiveness",
    "held {S}hostage","negotiated","took {S}captive","paid the {C} dollar ransom for","refused to pay the {C} dollar ransom for",
    "threatened","berated","hurled abuse at","listed all the reasons {S}should die for {C} hours","blackmailed",
    
    "praised","cheered {S}on","had a laugh with","lived happily ever after with","defended","protected",
    "saved","rescued","resucitated","cured","revived","reincarnated","gave birth to",
    "cleared {S}of any suspicion","found {S}innocent","found {S}guilty","thanked",
    "pleaded with","requested {S}be {N!A}","asked {S}about {S}","pondered on the concept of","considered what to do with","wondered how {0}even existed","discovered {0}was actually {4}",
    "raced","chased","persued","followed","stalked","snooped on","spied on","became a spy for","weaponised",
    "returned fire against","found fault with","did not understand why {S}had {A}","blundered their next move with","terrorised",
    "painted a {1} picture of","drew a portrait of","painted the town of {S} red","painted a {1} painting of","sketched","sang a {1} song",

    "framed","harassed","razed","fled from","advertised to","proselytised","rejected","retired","accepted {S}'s offer","assembled","pirated","stole",
    "hired","fired","said their final prayers to","encouraged","egged on","exported","gave the finger to","took {S}'s finger","infected","confirmed {S}'s death",
    "found {S}'s body","hid {S}'s body away from {S}","searched for","found a body and accused","found a body with","found the corpse of","denied the death of",
    "investigated the crime scene with","altered the crime scene","found the corpse and identified it as belonging to","left {S} for dead","stuck a fork in",
],

# // Adverbs that modify an action
actAdverbs = [
    "quickly","suddenly","heroically","dangerously","nervously","happily","cheerily","ignorantly","creepily","awkwardly","mistakenly","accidentally",
    "subtly","bravely","boldly","dumbly","unconsciously","stupidly","uncomfortably","sadly","forcefully","gloomily","pointlessly","needlessly","rightfully",
]

nouns = [
    # // Subjects
    [
        "the {1} man","the {1} woman","the {2} President of the {OA} nation","the {2} King of the {OA} Empire","the {1} Queen of the {OA} Empire","the Prime Minister of the {OA} nation" # // Titles
        "the {1} British Army","the Spanish Inquisition","{1} NATO","the {1} USSR","the {OA} Empire","the {OA} nation","a {1} Jehova's Witness","a {1} British man named Barry, aged 63, single and ready to mingle", # // Things
        "nobody","everybody","a{1} ICBM",

        "{3} Boris Johnson","{3} Joe Biden","{3} Margaret Thatcher","{3} Donald Trump","{3} Barack Obama","{3} Xi Jinping","{3} Kim Jong Un","Genghis Khan","Mao Zedong", # // World leaders
        "{2} Shakespeare","{2} Pablo Picasso","{2} Bob Ross","{2} Mary Shelley","{2} Michael Jackson","{2} Vincent Van Gogh","{2} Leonardo Da Vinci","{2} Michelangelo","{2} Stephen King", # // Great Artists
        "{2} James Bond","{2} Mr. Bean","{2} Patrick Star","{2} Australia","{2} Sherlock Holmes","{2} Gandalf","{2} Harry Potter","{2} Jon Snow","{2} Darth Vader","{2} John Wick","{2} Indiana Jones", # // Fictional characters (and fictional place)
        "{2} Ronald McDonald","{2} Queen Elizabeth II","{2} Abraham Lincoln","{2} Mahatma Gandhi","{2} George Washington","{2} Agent 47",

        "a{1} fish","a{1} bird","a{1} murderer","a{1} cocaine addict","a{1} zombie","a{1} horse","a{1} cat","a{1} dog","a{1} baboon","Joe", # // Idk, other things
    ],
    # // Objects
    [
        "the {1} Sun","the {1} Moon","a fridge","a{1} microwave","a{1} umbrella","a{1} gun","a{2} bottle","drugs","a{2} phone","a{1} can of spaghetti sauce","a{1} propaganda poster for {S}",
        "a{1} bottle of vodka","a bag of groceries","a{1} advertisement for {O}","a{1} bar of chocolate","a{1} grand piano","a{1} guitar","a{1} coin","a{1} stash of weapons",
        "a{1} camera","a{1} pen","a{1} mouse","a{1} box for {O}","a window","a{1} tank","a{1} coat","a{OA} city","a{1} egg","a socket","a{1} fan","a{1} essay about {S}",
        "a{1} bomb","a{1} stick","a{1} rod","a{1} pineapple","a{1} apple","a{1} block of cheese","a{1} orange","a{1} stick of dynamite","a{1} rock","a{1} fish",
        "a bag of crisps","a{1} landfill","a{1} police department","the {O} rozzers","a{1} crab","a{1} dolphin","a{1} whale","a{1} weapon of mass destruction","a{1} pile of crap",
        "an impostor","a{1} {OA} souvenir","a{1} cardboard cutout of {S}","a{1} floorboard","a{1} finger","a{1} painting by {S}","a{1} rug","a{1} cloth","a{1} fire alarm",
    ]
]

joiners = [
    "but then","but not without",
]

"""Substitutions:
{1} - Any number, amount of adjectives

{O} - Object
{S} - Subject
{N} - Any noun
{T} - Time period
{A} - Action
{C} - Amount

{N!A} - Action replacing nouns with blanks
{N|A} - Noun or adjective
{OA} - Origin Adjective"""

def sub(s:str) -> str:
    print(s)
    newS,got,get = "","",False
    for i,v in enumerate(s):
        if v == "{":
            get = True
            newS += s[:i]
        elif v == "}":
            get = False
            print(got)
            newS += getTerm(got)
        elif get: got += v
        else: newS += v
    return newS

def getTerm(id:str) -> str:
    try:
        id = int(id)
        random.shuffle(descriptors[0])
        return " "+sub(descriptors[0][0])
    except ValueError:
        match id:
            case "O":
                random.shuffle(nouns[1])
                s:str = nouns[1][0]
                print("Subject =",s)
                return sub(s)
        

def generate():
    return "eh"
    return getTerm("O")