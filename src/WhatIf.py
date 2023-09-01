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
    # // Opinion - 0
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
    # // Condition - 1
    [
        "rotten","dirty","uncooked","stale","mouldy","infected","destroyed","damaged","filthy","clean","pristine",
        "shiny","homemade","contagious","cancerous","intoxicated","drunk","inebriated","molten","burning","swollen",
        "irradiated","radioactive","rusty","wet","expired","accelerating","empty",
    ],
    # // Size - 2
    [
        "massive","large","huge","big","average-sized","small","tiny","miniscule","microscopic","puny",
        "obese","plus-sized","overweight","healthy-weight","underweight","emaciated","chunky","fat"
    ],
    # // Age - 3
    [
        "pre-historic","neolithic","ancient","old","aged","new","brand new","futuristic","decrepit","modern","contemporary",
        "medieval","classical","renaissance","cold war era","from the {T}s","youthful","young","recent","outdated",
    ],
    # // Shape - 4
    [
        "round","spherical","curved","square","uneven","rectangular","triangular","polygonal","hexagonal","flat","rough","bumpy"
    ],
    # // Colour - 5
    # // ZWSP or space indicates that this colour should not be modified (with light or dark)
    [
        "light​","dark​","white​","black​","grey","red","green","blue","orange","yellow","brown","purple","gold","pink","cyan",
        "pearl white","deep blue","navy blue","acid green","amethyst purple","apricot orange","baby blue","baby pink","olive green",
        "brick red","burgundy​","copper orange","emerald green","golden brown","granite grey","hot pink","magenta​","lemon yellow",
        "lime​","midnight blue","midnight green","royal blue","silver​","beige​","invisible​"
    ],
    # // Origin - 6
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
    # // Material - 7
    [
        "rubber","leather","silk","fabric","cotton","wool","plastic","wooden","steel","metal","synthetic","fur","concrete","icy"
    ],
    # // Purpose - 8
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

# // ZWSP indicates this amount should not be used for modifications. Amounts ending in dash may have another non-dash number appended.
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
    
    "praised","cheered{S} on","had a laugh with","lived happily ever after with","defended","protected",
    "saved","rescued","resucitated","cured","revived","reincarnated","gave birth to",
    "cleared{S} of any suspicion after hearing about","found{S} innocent thanks to","found{S} guilty mostly because of","thanked",
    "pleaded with","requested {S}be {N!A}","asked {S} about{S} and their affairs with","pondered on the concept of","considered what to do with","wondered how {0}even existed","discovered {0}was actually {4}",
    "raced","chased","persued","followed","stalked","snooped on","spied on","became a spy for","weaponised",
    "returned fire against","found fault with","did not understand why{S}had {A}","blundered their next move with","terrorised",
    "painted a {1} picture of","drew a portrait of","painted the town of{S} red for","painted a {1} painting of","sketched","sang a {1} song",

    "framed","harassed","razed","fled from","advertised to","proselytised","rejected","retired","accepted {S}'s offer for","assembled","pirated","stole",
    "hired","fired","said their final prayers to","encouraged","egged on","exported","gave the finger to","took {S}'s finger in exchange for","infected","confirmed {S}'s death with",
    "found {S}'s body with","hid {S}'s body away from {S} with","searched for","found a body and accused","found a body with","found the corpse of","denied the death of",
    "investigated the crime scene with","altered the crime scene","found the corpse and identified it as belonging to","left {S} for dead with","stuck a fork in",
]

# // Adverbs that modify an action
actAdverbs = [
    "quickly","suddenly","heroically","dangerously","nervously","happily","cheerily","ignorantly","creepily","awkwardly","mistakenly","accidentally",
    "subtly","bravely","boldly","dumbly","unconsciously","stupidly","uncomfortably","sadly","forcefully","gloomily","pointlessly","needlessly","rightfully",
]

nouns = [
    # // Subjects
    [
        "the{1} man","the{1} woman","the{2} President of the {OA} nation","the{2} King of the{OA} Empire","the{1} Queen of the {OA} Empire","the Prime Minister of the{OA} nation" # // Titles
        "the{1} British Army","the Spanish Inquisition","{1} NATO","the{1} USSR","the{OA} Empire","the{OA} nation","a{1} Jehova's Witness","a{1} British man named Barry, aged 63, single and ready to mingle", # // Things
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

def sub(s:str,block=False) -> str:
    "Returns the string with all substitutions made."
    new = ""
    while True:
        new = s.replace("{O}","" if block else getTerm("O",block=True),1)
        new.replace("{S}","" if block else getTerm("S",block=True),1)
        new.replace("{N}","" if block else getTerm("N",block=True),1)
        new.replace("{T}","" if block else getTerm("T",block=True),1)
        new.replace("{A}","" if block else getTerm("A",block=True),1)
        new.replace("{C}","" if block else getTerm("C",block=True),1)
        new.replace("{N!A}","" if block else getTerm("N!A",block=True),1)
        new.replace("{N|A}","" if block else getTerm("N|A",block=True),1)
        new.replace("{OA}","" if block else getTerm("OA",block=True),1)
        if s == new: break # // i.e, the string did not change after all the replacements in this loop
        s = new

    # // Now we need to sub adjectives, which can have any integer as an ID. Because I'm fancy.
    det,st = "",False
    ls = s
    for i in ls:
        # // We need to only collect the number
        if i == "{": st = True
        elif st and i != "}": det += i
        if i == "}":
            s = s.replace("{"+det+"}","" if block else getTerm(det,block=True),1)
            det,st = "",False

    return s
        

def getTerm(id:str,block=False) -> str:
    try:
        id = int(id)

        adjs = [[] for _ in range(9)] # // Create a list with 8 elements for the royal order of adjs. Annoyingly range is exclusive.
        for _ in range(id):
            chosen = random.randint(0,8)
            random.shuffle(descriptors[chosen])
            adjs[chosen].append(descriptors[chosen][0])

        lng = 0
        for i in adjs:
            for _ in i: lng += 1

        s = ""
        index = 0
        
        for i in adjs:
            for v in i:
                index += 1
                if v:
                    start = ""
                    if index == 1 and v[0].lower() in vowels: start = "n "
                    elif index == lng and index != 1: start = " and "
                    else: start = " "

                    end = ""
                    if index < (lng - 1): end = ","

                    s += start + v + end

        return sub(s,block)
        
    except ValueError:
        match id:
            case "O":
                random.shuffle(nouns[1])
                s = nouns[1][0]
                return sub(s,block)
            case "S":
                random.shuffle(nouns[0])
                s = nouns[0][0]
                return sub(s,block)
            case "N":
                chosen = random.randint(0,1)
                random.shuffle(nouns[chosen])
                s = nouns[chosen][0]
                return sub(s,block)
            case "T":
                random.shuffle(timePeriods)
                s = timePeriods[0]
                return sub(s,block)
            case "A":
                random.shuffle(actions)
                s = actions[0]
                return sub(s,block)
            case "C":
                random.shuffle(amounts)
                s = amounts[0]
                return sub(s,block)

            case "N!A":
                random.shuffle(actions)
                s = actions[0]
                return sub(s,block)
            case "N|A":
                chosen = nouns[random.randint(0,1)] if random.randint(0,1) == 1 else descriptors[random.randint(0,8)]
                random.shuffle(chosen)
                s = chosen[0]
                return sub(s,block)
            case "OA":
                random.shuffle(descriptors[6])
                s = descriptors[6][0]
                return sub(s,block)
        

def generate():
    s = getTerm("S")+" "+getTerm("A")+" "+getTerm("O")+"."
    s = s[0].upper()+s[1:]
    return s

print(generate())